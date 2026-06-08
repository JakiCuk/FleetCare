"""Shared serialization helpers for routers."""

from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.car import Car, UserCarGroup
from app.models.user import User
from app.schemas.car import CarOut
from app.schemas.user import CarRef, UserOut


async def serialize_user(session: AsyncSession, user: User) -> UserOut:
    """Build a ``UserOut`` including the user's assigned cars (id + name)."""
    rows = (
        await session.execute(
            select(Car.id, Car.name)
            .join(UserCarGroup, UserCarGroup.car_id == Car.id)
            .where(UserCarGroup.user_id == user.id)
            .order_by(Car.name)
        )
    ).all()
    cars = [CarRef(id=r[0], name=r[1]) for r in rows]
    return UserOut(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        is_admin=user.is_admin,
        is_active=user.is_active,
        locale=user.locale,
        cars=cars,
    )


def car_full_name(car: Car) -> str:
    """Compose a friendly full name: 'Make Model' or fall back to ``name``."""
    parts = [p for p in (car.make, car.model) if p]
    if parts:
        return " ".join(parts)
    return car.name


def serialize_car(car: Car) -> CarOut:
    """Build a ``CarOut`` with a computed ``full_name``."""
    return CarOut(
        id=car.id,
        name=car.name,
        full_name=car_full_name(car),
        make=car.make,
        model=car.model,
        year=car.year,
        license_plate=car.license_plate,
        vin=car.vin,
        current_odometer_km=car.current_odometer_km,
    )


def days_left(valid_until: date | None, today: date) -> int | None:
    if valid_until is None:
        return None
    return (valid_until - today).days
