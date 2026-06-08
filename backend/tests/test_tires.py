"""Integration test for tire set creation, measurements, and the trend endpoint."""

from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_tire_trend_returns_points_and_projection(admin_client) -> None:
    # 1) Create a car.
    car = await admin_client.post(
        "/api/cars",
        json={"name": "Tire Car", "license_plate": "BA-TIRE", "current_odometer_km": 130000},
    )
    car_id = car.json()["id"]

    # 2) Odometer readings 30 days apart (positive span -> a projection date).
    await admin_client.post(
        f"/api/cars/{car_id}/odometer",
        json={"reading_km": 100000, "recorded_at": "2024-01-01T00:00:00Z"},
    )
    await admin_client.post(
        f"/api/cars/{car_id}/odometer",
        json={"reading_km": 130000, "recorded_at": "2024-06-29T00:00:00Z"},
    )

    # 3) Create a tire set with a first measurement, then add two more (decreasing).
    create_set = await admin_client.post(
        f"/api/cars/{car_id}/tires",
        json={
            "name": "Winter set",
            "season": "winter",
            "mounted_at": "2024-01-01",
            "mounted_odometer_km": 100000,
            "expected_change_date": "2025-01-01",
            "initial_measurement": {
                "measured_at": "2024-01-01",
                "odometer_km": 100000,
                "tread_fl_mm": 8.0,
                "tread_fr_mm": 8.0,
                "tread_rl_mm": 8.0,
                "tread_rr_mm": 8.0,
            },
        },
    )
    assert create_set.status_code == 201
    set_id = create_set.json()["id"]
    assert create_set.json()["is_active"] is True

    for odo, tread, when in (
        (115000, 6.5, "2024-03-15"),
        (130000, 5.0, "2024-06-29"),
    ):
        m = await admin_client.post(
            f"/api/tires/{set_id}/measurements",
            json={
                "measured_at": when,
                "odometer_km": odo,
                "tread_fl_mm": tread,
                "tread_fr_mm": tread,
                "tread_rl_mm": tread,
                "tread_rr_mm": tread,
            },
        )
        assert m.status_code == 201

    # 4) Trend endpoint: actual points + dashed projection to the 1.6 mm reference.
    trend = await admin_client.get(f"/api/tires/{set_id}/trend")
    assert trend.status_code == 200
    body = trend.json()

    assert body["reference_mm"] == 1.6
    assert len(body["points"]) == 3
    assert [round(p["km"]) for p in body["points"]] == [100000, 115000, 130000]

    # Decreasing trend -> a non-empty projection ending exactly on 1.6 mm.
    assert len(body["projection"]) == 2
    assert body["projection"][-1]["projected"] == 1.6
    assert body["projection_date"] is not None
