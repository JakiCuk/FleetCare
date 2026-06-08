"""Odometer reading endpoints (nested under a car)."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, status
from sqlalchemy import select

from app.dependencies import CurrentUser, SessionDep, get_owned_car
from app.models.odometer import OdometerReading
from app.schemas.odometer import OdometerCreate, OdometerOut

router = APIRouter(prefix="/cars/{car_id}/odometer", tags=["odometer"])


@router.get("", response_model=list[OdometerOut])
async def list_readings(
    car_id: int, current_user: CurrentUser, session: SessionDep
) -> list[OdometerOut]:
    await get_owned_car(session, current_user, car_id)
    rows = (
        await session.execute(
            select(OdometerReading)
            .where(OdometerReading.car_id == car_id)
            .order_by(OdometerReading.recorded_at.desc())
        )
    ).scalars().all()
    return [OdometerOut.model_validate(r) for r in rows]


@router.post("", response_model=OdometerOut, status_code=status.HTTP_201_CREATED)
async def create_reading(
    car_id: int,
    payload: OdometerCreate,
    current_user: CurrentUser,
    session: SessionDep,
) -> OdometerOut:
    car = await get_owned_car(session, current_user, car_id)
    reading = OdometerReading(
        car_id=car_id,
        reading_km=payload.reading_km,
        recorded_at=payload.recorded_at or datetime.now(timezone.utc),
        note=payload.note,
    )
    session.add(reading)
    # Keep the denormalized current odometer at the max observed reading.
    if payload.reading_km > car.current_odometer_km:
        car.current_odometer_km = payload.reading_km
    await session.commit()
    await session.refresh(reading)
    return OdometerOut.model_validate(reading)
