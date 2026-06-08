"""Integration tests for car CRUD + CarDetail + ownership enforcement."""

from __future__ import annotations

import uuid

import pytest

from app.models.car import Car
from app.models.user import User
from app.security import create_access_token, hash_password


@pytest.mark.asyncio
async def test_admin_creates_car_and_it_lists(admin_client) -> None:
    payload = {
        "name": "Škoda Octavia",
        "make": "Škoda",
        "model": "Octavia",
        "year": 2019,
        "license_plate": "BA123AB",
        "vin": "TMBJB41Z5K0000001",
        "current_odometer_km": 127540,
    }
    create = await admin_client.post("/api/cars", json=payload)
    assert create.status_code == 201
    created = create.json()
    assert created["name"] == "Škoda Octavia"
    assert created["license_plate"] == "BA123AB"
    # full_name is derived from make + model.
    assert created["full_name"] == "Škoda Octavia"
    car_id = created["id"]

    listing = await admin_client.get("/api/cars")
    assert listing.status_code == 200
    ids = [c["id"] for c in listing.json()]
    assert car_id in ids


@pytest.mark.asyncio
async def test_car_detail_shape(admin_client) -> None:
    create = await admin_client.post(
        "/api/cars",
        json={"name": "Detail Car", "license_plate": "BA999ZZ", "current_odometer_km": 1000},
    )
    car_id = create.json()["id"]

    resp = await admin_client.get(f"/api/cars/{car_id}")
    assert resp.status_code == 200
    detail = resp.json()

    # Aggregated CarDetail fields (single current docs, overdue flag, cost).
    assert detail["id"] == car_id
    assert detail["stk"] is None
    assert detail["pzp"] is None
    assert detail["kasko"] is None
    assert detail["vignettes"] == []
    assert detail["active_tire_set"] is None
    assert detail["next_service"] is None
    assert isinstance(detail["overdue"], bool)
    assert detail["overdue"] is False
    assert detail["monthly_cost"] == 0.0


@pytest.mark.asyncio
async def test_non_admin_cannot_access_foreign_car(client, session, admin_user) -> None:
    # A car the non-admin user is NOT assigned to.
    car = Car(name="Owner Car", license_plate="BA000OW", current_odometer_km=5000)
    session.add(car)

    suffix = uuid.uuid4().hex[:8]
    regular = User(
        username=f"user_{suffix}",
        email=f"user_{suffix}@fleetcare.test",
        hashed_password=hash_password("user-password-123"),
        is_admin=False,
        is_active=True,
        locale="sk",
    )
    session.add(regular)
    await session.commit()
    await session.refresh(car)
    await session.refresh(regular)

    token = create_access_token(regular.id)
    resp = await client.get(
        f"/api/cars/{car.id}", headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 403

    # The same user sees an empty fleet list (no assignments).
    listing = await client.get(
        "/api/cars", headers={"Authorization": f"Bearer {token}"}
    )
    assert listing.status_code == 200
    assert listing.json() == []
