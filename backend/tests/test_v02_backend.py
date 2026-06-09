"""Integration + unit tests for the FleetCare v0.2 backend changes.

Covers:
    * admin-only deletion of cars and tire sets (403 for a regular user, 204 admin);
    * tire tread/pressure serialised as JSON numbers (not Decimal-as-string);
    * measurement PATCH / DELETE with ownership via measurement→set→car;
    * notification-log scoped to a non-admin's assigned cars;
    * costs breakdown summing manual expenses + fuel + service;
    * projection fallback exposing ``km_at_reference`` even when no date is computable;
    * ``create_reminder`` upserting a single idempotent ``ServiceInterval``;
    * enriched cars list (STK/PZP/KASKO + overdue) and optional car ``name``.
"""

from __future__ import annotations

import uuid
from datetime import date, timedelta

import pytest

from app.models.car import UserCarGroup
from app.models.notification import NotificationLog
from app.models.tire import TireMeasurement
from app.models.user import User
from app.security import create_access_token, hash_password
from app.services.projection_service import compute_projection


# ── helpers ──────────────────────────────────────────────────────────────
async def _make_regular_user(session, *, car_ids: list[int] | None = None) -> User:
    """Create a non-admin user, optionally assigned to the given cars."""
    suffix = uuid.uuid4().hex[:8]
    user = User(
        username=f"user_{suffix}",
        email=f"user_{suffix}@fleetcare.test",
        hashed_password=hash_password("user-password-123"),
        is_admin=False,
        is_active=True,
        locale="sk",
    )
    session.add(user)
    await session.flush()
    for cid in car_ids or []:
        session.add(UserCarGroup(user_id=user.id, car_id=cid))
    await session.commit()
    await session.refresh(user)
    return user


def _auth(user: User) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(user.id)}"}


async def _create_car(admin_client, **overrides) -> int:
    payload = {"license_plate": f"BA{uuid.uuid4().hex[:5].upper()}", "current_odometer_km": 1000}
    payload.update(overrides)
    resp = await admin_client.post("/api/cars", json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


# ── authz: admin-only deletes ─────────────────────────────────────────────
@pytest.mark.asyncio
async def test_delete_car_requires_admin(admin_client, client, session) -> None:
    car_id = await _create_car(admin_client, name="Del Car")
    user = await _make_regular_user(session, car_ids=[car_id])

    forbidden = await client.delete(f"/api/cars/{car_id}", headers=_auth(user))
    assert forbidden.status_code == 403

    ok = await admin_client.delete(f"/api/cars/{car_id}")
    assert ok.status_code == 204


@pytest.mark.asyncio
async def test_delete_tire_set_requires_admin(admin_client, client, session) -> None:
    car_id = await _create_car(admin_client, name="Tire Del Car")
    user = await _make_regular_user(session, car_ids=[car_id])
    set_resp = await admin_client.post(
        f"/api/cars/{car_id}/tires", json={"name": "Set", "season": "summer"}
    )
    set_id = set_resp.json()["id"]

    forbidden = await client.delete(f"/api/tires/{set_id}", headers=_auth(user))
    assert forbidden.status_code == 403

    ok = await admin_client.delete(f"/api/tires/{set_id}")
    assert ok.status_code == 204


# ── tires: numeric serialisation + measurement CRUD ───────────────────────
@pytest.mark.asyncio
async def test_tires_return_tread_pressure_as_numbers(admin_client) -> None:
    car_id = await _create_car(admin_client, name="Num Car", current_odometer_km=100000)
    create = await admin_client.post(
        f"/api/cars/{car_id}/tires",
        json={
            "name": "Set",
            "season": "summer",
            "initial_measurement": {
                "measured_at": "2024-01-01",
                "odometer_km": 100000,
                "tread_fl_mm": 7.5,
                "tread_fr_mm": 7.5,
                "tread_rl_mm": 7.0,
                "tread_rr_mm": 7.0,
                "pressure_fl_after_bar": 2.3,
                "pressure_fr_after_bar": 2.3,
                "pressure_rl_after_bar": 2.2,
                "pressure_rr_after_bar": 2.2,
            },
        },
    )
    assert create.status_code == 201
    listing = await admin_client.get(f"/api/cars/{car_id}/tires")
    m = listing.json()[0]["measurements"][0]
    # JSON numbers, not Decimal-as-string -> no NaN on the client.
    assert isinstance(m["tread_fl_mm"], (int, float))
    assert isinstance(m["pressure_fl_after_bar"], (int, float))
    assert m["tread_fl_mm"] == 7.5
    assert isinstance(listing.json()[0]["avg_pressure_bar"], (int, float))


@pytest.mark.asyncio
async def test_measurement_patch_and_delete(admin_client, client, session) -> None:
    car_id = await _create_car(admin_client, name="Meas Car", current_odometer_km=100000)
    create = await admin_client.post(
        f"/api/cars/{car_id}/tires",
        json={
            "name": "Set",
            "season": "summer",
            "initial_measurement": {
                "measured_at": "2024-01-01",
                "odometer_km": 100000,
                "tread_fl_mm": 7.0,
                "tread_fr_mm": 7.0,
                "tread_rl_mm": 7.0,
                "tread_rr_mm": 7.0,
            },
        },
    )
    set_id = create.json()["id"]
    measurement_id = create.json()["measurements"][0]["id"]

    # PATCH a single field.
    patched = await admin_client.patch(
        f"/api/tires/measurements/{measurement_id}", json={"tread_fl_mm": 6.0}
    )
    assert patched.status_code == 200
    assert patched.json()["tread_fl_mm"] == 6.0
    assert patched.json()["tread_fr_mm"] == 7.0  # untouched

    # A non-owner cannot touch it.
    other = await _make_regular_user(session, car_ids=[])
    forbidden = await client.patch(
        f"/api/tires/measurements/{measurement_id}",
        json={"tread_fl_mm": 1.0},
        headers=_auth(other),
    )
    assert forbidden.status_code == 403

    # DELETE returns 204 and removes the row.
    deleted = await admin_client.delete(f"/api/tires/measurements/{measurement_id}")
    assert deleted.status_code == 204
    gone = await admin_client.delete(f"/api/tires/measurements/{measurement_id}")
    assert gone.status_code == 404
    _ = set_id


# ── notifications: scoped log ─────────────────────────────────────────────
@pytest.mark.asyncio
async def test_notification_log_scoped_to_user_cars(admin_client, client, session) -> None:
    mine = await _create_car(admin_client, name="My Car")
    other = await _create_car(admin_client, name="Other Car")
    session.add(
        NotificationLog(
            car_id=mine, channel="email", recipient="a@b.c", status="sent",
            item_type="stk", subject="mine",
        )
    )
    session.add(
        NotificationLog(
            car_id=other, channel="email", recipient="a@b.c", status="sent",
            item_type="stk", subject="theirs",
        )
    )
    await session.commit()
    user = await _make_regular_user(session, car_ids=[mine])

    resp = await client.get("/api/notification-log", headers=_auth(user))
    assert resp.status_code == 200
    subjects = {r["subject"] for r in resp.json()}
    assert subjects == {"mine"}

    # Admin sees both.
    admin_resp = await admin_client.get("/api/notification-log")
    admin_subjects = {r["subject"] for r in admin_resp.json()}
    assert {"mine", "theirs"} <= admin_subjects


# ── costs: breakdown includes fuel + service ──────────────────────────────
@pytest.mark.asyncio
async def test_breakdown_includes_fuel_and_service(admin_client) -> None:
    car_id = await _create_car(admin_client, name="Cost Car", current_odometer_km=10000)
    # A manual "other" expense.
    await admin_client.post(
        f"/api/cars/{car_id}/expenses",
        json={"occurred_at": "2024-05-01", "amount": 50, "category": "other"},
    )
    # A fuel record (total_cost) -> bucket "fuel".
    await admin_client.post(
        f"/api/cars/{car_id}/fuel",
        json={"refueled_at": "2024-05-02", "odometer_km": 10100, "liters": 40,
              "total_cost": 60, "full_tank": True},
    )
    # A service record (cost) -> bucket "service".
    await admin_client.post(
        f"/api/cars/{car_id}/services",
        json={"performed_at": "2024-05-03", "category": "service", "cost": 120},
    )

    resp = await admin_client.get(f"/api/cars/{car_id}/expenses/breakdown")
    assert resp.status_code == 200
    body = resp.json()
    buckets = {b["category"]: b["amount"] for b in body["breakdown"]}
    assert buckets.get("fuel") == 60.0
    assert buckets.get("service") == 120.0
    assert buckets.get("other") == 50.0
    assert body["total"] == 230.0

    # Date range excludes the fuel record (only the manual expense on 05-01).
    ranged = await admin_client.get(
        f"/api/cars/{car_id}/expenses/breakdown",
        params={"from_date": "2024-05-01", "to_date": "2024-05-01"},
    )
    ranged_buckets = {b["category"]: b["amount"] for b in ranged.json()["breakdown"]}
    assert ranged_buckets == {"other": 50.0}


# ── projection fallback: km_at_reference without a date ───────────────────
def test_projection_fallback_km_at_reference_without_date() -> None:
    """A clear decreasing slope but no time signal -> km projection, no date."""
    same_day = date(2024, 1, 1)
    measurements = [
        TireMeasurement(
            tire_set_id=1, measured_at=same_day, odometer_km=100_000,
            tread_fl_mm=8.0, tread_fr_mm=8.0, tread_rl_mm=8.0, tread_rr_mm=8.0,
        ),
        TireMeasurement(
            tire_set_id=1, measured_at=same_day, odometer_km=120_000,
            tread_fl_mm=4.0, tread_fr_mm=4.0, tread_rl_mm=4.0, tread_rr_mm=4.0,
        ),
    ]
    # No odometer readings, no mounted_at -> daily km is unknowable.
    result = compute_projection(measurements, [])
    assert result.projection_date is None
    assert result.km_at_reference is not None
    assert result.km_at_reference > 120_000
    # A dashed projection line is still produced for the chart.
    assert len(result.projection) == 2
    assert result.projection[-1].projected == result.reference_mm


def test_projection_fallback_uses_measurement_span_for_date() -> None:
    """Without odometer readings, the set's own measurement span yields a date."""
    base = date(2024, 1, 1)
    measurements = [
        TireMeasurement(
            tire_set_id=1, measured_at=base, odometer_km=100_000,
            tread_fl_mm=8.0, tread_fr_mm=8.0, tread_rl_mm=8.0, tread_rr_mm=8.0,
        ),
        TireMeasurement(
            tire_set_id=1, measured_at=base + timedelta(days=100), odometer_km=110_000,
            tread_fl_mm=6.0, tread_fr_mm=6.0, tread_rl_mm=6.0, tread_rr_mm=6.0,
        ),
    ]
    result = compute_projection(measurements, [], today=base + timedelta(days=100))
    assert result.km_at_reference is not None
    assert result.projection_date is not None


# ── service reminder -> idempotent interval upsert ────────────────────────
@pytest.mark.asyncio
async def test_create_reminder_upserts_service_interval(admin_client) -> None:
    car_id = await _create_car(admin_client, name="Svc Car", current_odometer_km=50000)
    payload = {
        "performed_at": "2024-01-01",
        "odometer_km": 50000,
        "category": "service",
        "description": "Olejový servis",
        "create_reminder": True,
        "next_service_km": 65000,
        "next_service_date": "2025-01-01",
    }
    first = await admin_client.post(f"/api/cars/{car_id}/services", json=payload)
    assert first.status_code == 201

    intervals = await admin_client.get(f"/api/cars/{car_id}/service-intervals")
    assert intervals.status_code == 200
    rows = intervals.json()
    assert len(rows) == 1
    iv = rows[0]
    assert iv["name"] == "Olejový servis"
    assert iv["interval_km"] == 15000  # 65000 - 50000
    assert iv["interval_months"] == 12

    # A second record with the same name upserts (no duplicate interval).
    second = await admin_client.post(f"/api/cars/{car_id}/services", json=payload)
    assert second.status_code == 201
    again = await admin_client.get(f"/api/cars/{car_id}/service-intervals")
    assert len(again.json()) == 1

    # Without create_reminder, no interval is created.
    no_reminder = await admin_client.post(
        f"/api/cars/{car_id}/services",
        json={"performed_at": "2024-02-01", "category": "repair",
              "description": "Brzdy", "next_service_km": 70000},
    )
    assert no_reminder.status_code == 201
    final = await admin_client.get(f"/api/cars/{car_id}/service-intervals")
    assert {r["name"] for r in final.json()} == {"Olejový servis"}


# ── cars list enrich + optional name ──────────────────────────────────────
@pytest.mark.asyncio
async def test_cars_list_is_enriched_with_doc_status(admin_client) -> None:
    car_id = await _create_car(admin_client, name="Enrich Car", current_odometer_km=1000)
    today = date.today()
    # An overdue STK + a valid PZP.
    await admin_client.post(
        f"/api/cars/{car_id}/stk",
        json={"valid_until": (today - timedelta(days=5)).isoformat()},
    )
    await admin_client.post(
        f"/api/cars/{car_id}/insurance",
        json={"type": "PZP", "valid_until": (today + timedelta(days=40)).isoformat()},
    )

    listing = await admin_client.get("/api/cars")
    assert listing.status_code == 200
    item = next(c for c in listing.json() if c["id"] == car_id)
    assert item["stk"]["days_left"] == -5
    assert item["pzp"]["days_left"] == 40
    assert item["kasko"] is None
    assert item["overdue"] is True


@pytest.mark.asyncio
async def test_create_car_without_name_derives_from_make_model(admin_client) -> None:
    resp = await admin_client.post(
        "/api/cars",
        json={"make": "Škoda", "model": "Octavia", "license_plate": "BA-NONAME"},
    )
    assert resp.status_code == 201
    assert resp.json()["name"] == "Škoda Octavia"
