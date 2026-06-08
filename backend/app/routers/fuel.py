"""Fuel record endpoints + consumption statistics."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.dependencies import CurrentUser, SessionDep, get_owned_car, user_owns_car
from app.models.fuel import FuelRecord
from app.schemas.fuel import (
    FuelMonthlyPoint,
    FuelRecordCreate,
    FuelRecordOut,
    FuelRecordUpdate,
    FuelStats,
)
from app.services import fuel_service

router = APIRouter(tags=["fuel"])


def _out(r: FuelRecord, consumption: float | None) -> FuelRecordOut:
    return FuelRecordOut(
        id=r.id,
        refueled_at=r.refueled_at,
        odometer_km=r.odometer_km,
        liters=r.liters,
        price_per_liter=r.price_per_liter,
        total_cost=r.total_cost,
        full_tank=r.full_tank,
        consumption_l_100km=consumption,
    )


async def _load_owned(session, current_user, record_id: int) -> FuelRecord:
    obj = await session.get(FuelRecord, record_id)
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fuel record not found")
    if not await user_owns_car(session, current_user, obj.car_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access to this car is forbidden",
        )
    return obj


@router.get("/cars/{car_id}/fuel", response_model=list[FuelRecordOut])
async def list_fuel(car_id: int, current_user: CurrentUser, session: SessionDep):
    await get_owned_car(session, current_user, car_id)
    rows = (
        await session.execute(
            select(FuelRecord)
            .where(FuelRecord.car_id == car_id)
            .order_by(FuelRecord.refueled_at.desc(), FuelRecord.odometer_km.desc())
        )
    ).scalars().all()
    cmap = fuel_service.consumption_map(list(rows))
    return [_out(r, cmap.get(r.id)) for r in rows]


@router.post(
    "/cars/{car_id}/fuel", response_model=FuelRecordOut, status_code=status.HTTP_201_CREATED
)
async def create_fuel(
    car_id: int, payload: FuelRecordCreate, current_user: CurrentUser, session: SessionDep
):
    await get_owned_car(session, current_user, car_id)
    data = payload.model_dump()
    # Derive total_cost from liters * price when omitted.
    if data.get("total_cost") is None and data.get("price_per_liter") is not None:
        data["total_cost"] = data["liters"] * data["price_per_liter"]
    row = FuelRecord(car_id=car_id, **data)
    session.add(row)
    await session.commit()
    await session.refresh(row)
    # Recompute consumption with full history for an accurate value.
    rows = (
        await session.execute(select(FuelRecord).where(FuelRecord.car_id == car_id))
    ).scalars().all()
    cmap = fuel_service.consumption_map(list(rows))
    return _out(row, cmap.get(row.id))


@router.patch("/fuel/{record_id}", response_model=FuelRecordOut)
async def update_fuel(
    record_id: int,
    payload: FuelRecordUpdate,
    current_user: CurrentUser,
    session: SessionDep,
):
    row = await _load_owned(session, current_user, record_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(row, field, value)
    await session.commit()
    await session.refresh(row)
    rows = (
        await session.execute(select(FuelRecord).where(FuelRecord.car_id == row.car_id))
    ).scalars().all()
    cmap = fuel_service.consumption_map(list(rows))
    return _out(row, cmap.get(row.id))


@router.delete("/fuel/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_fuel(record_id: int, current_user: CurrentUser, session: SessionDep):
    row = await _load_owned(session, current_user, record_id)
    await session.delete(row)
    await session.commit()


@router.get("/cars/{car_id}/fuel/stats", response_model=FuelStats)
async def fuel_stats(car_id: int, current_user: CurrentUser, session: SessionDep):
    await get_owned_car(session, current_user, car_id)
    rows = (
        await session.execute(select(FuelRecord).where(FuelRecord.car_id == car_id))
    ).scalars().all()
    stats = fuel_service.compute_stats(list(rows))
    return FuelStats(
        avg_consumption=stats["avg_consumption"],
        total_spent=stats["total_spent"],
        count=stats["count"],
        monthly=[FuelMonthlyPoint(**m) for m in stats["monthly"]],
    )
