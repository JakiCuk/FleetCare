"""Tire set, measurement, and trend/projection endpoints."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.dependencies import CurrentUser, SessionDep, get_owned_car, user_owns_car
from app.models.odometer import OdometerReading
from app.models.tire import TireMeasurement, TireSet
from app.schemas.tire import (
    MeasurementCreate,
    MeasurementOut,
    ProjectionPoint,
    TireSetCreate,
    TireSetOut,
    TireSetUpdate,
    TrendPoint,
    TrendResponse,
)
from app.services import projection_service

router = APIRouter(tags=["tires"])


def _measurement_out(m: TireMeasurement) -> MeasurementOut:
    avg = projection_service._avg_tread(m)
    return MeasurementOut(
        id=m.id,
        measured_at=m.measured_at,
        odometer_km=m.odometer_km,
        tread_fl_mm=m.tread_fl_mm,
        tread_fr_mm=m.tread_fr_mm,
        tread_rl_mm=m.tread_rl_mm,
        tread_rr_mm=m.tread_rr_mm,
        pressure_fl_before_bar=m.pressure_fl_before_bar,
        pressure_fr_before_bar=m.pressure_fr_before_bar,
        pressure_rl_before_bar=m.pressure_rl_before_bar,
        pressure_rr_before_bar=m.pressure_rr_before_bar,
        pressure_fl_after_bar=m.pressure_fl_after_bar,
        pressure_fr_after_bar=m.pressure_fr_after_bar,
        pressure_rl_after_bar=m.pressure_rl_after_bar,
        pressure_rr_after_bar=m.pressure_rr_after_bar,
        avg_tread_mm=avg,
    )


async def _tire_set_out(
    session: SessionDep, tire_set: TireSet, *, today: date | None = None
) -> TireSetOut:
    today = today or date.today()
    measurements = (
        await session.execute(
            select(TireMeasurement)
            .where(TireMeasurement.tire_set_id == tire_set.id)
            .order_by(TireMeasurement.measured_at)
        )
    ).scalars().all()
    readings = (
        await session.execute(
            select(OdometerReading).where(OdometerReading.car_id == tire_set.car_id)
        )
    ).scalars().all()
    proj = projection_service.compute_projection(
        list(measurements), list(readings), today=today
    )
    return TireSetOut(
        id=tire_set.id,
        name=tire_set.name,
        season=tire_set.season,
        is_active=tire_set.is_active,
        mounted_at=tire_set.mounted_at,
        mounted_odometer_km=tire_set.mounted_odometer_km,
        expected_change_date=tire_set.expected_change_date,
        avg_tread_mm=proj.latest_avg_tread_mm,
        mileage_km=proj.mileage_km,
        avg_pressure_bar=proj.avg_pressure_bar,
        projection_date=proj.projection_date,
        measurements=[_measurement_out(m) for m in measurements],
    )


async def _load_owned_set(session, current_user, set_id: int) -> TireSet:
    obj = await session.get(TireSet, set_id)
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tire set not found")
    if not await user_owns_car(session, current_user, obj.car_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access to this car is forbidden",
        )
    return obj


@router.get("/cars/{car_id}/tires", response_model=list[TireSetOut])
async def list_tire_sets(car_id: int, current_user: CurrentUser, session: SessionDep):
    await get_owned_car(session, current_user, car_id)
    sets = (
        await session.execute(
            select(TireSet)
            .where(TireSet.car_id == car_id)
            .order_by(TireSet.is_active.desc(), TireSet.created_at.desc())
        )
    ).scalars().all()
    return [await _tire_set_out(session, s) for s in sets]


@router.post(
    "/cars/{car_id}/tires", response_model=TireSetOut, status_code=status.HTTP_201_CREATED
)
async def create_tire_set(
    car_id: int, payload: TireSetCreate, current_user: CurrentUser, session: SessionDep
):
    await get_owned_car(session, current_user, car_id)
    # New set becomes active; deactivate all existing sets for this car.
    existing = (
        await session.execute(
            select(TireSet).where(TireSet.car_id == car_id, TireSet.is_active.is_(True))
        )
    ).scalars().all()
    for s in existing:
        s.is_active = False

    tire_set = TireSet(
        car_id=car_id,
        name=payload.name,
        season=payload.season,
        is_active=True,
        mounted_at=payload.mounted_at,
        mounted_odometer_km=payload.mounted_odometer_km,
        expected_change_date=payload.expected_change_date,
    )
    session.add(tire_set)
    await session.flush()

    if payload.initial_measurement is not None:
        session.add(
            TireMeasurement(
                tire_set_id=tire_set.id,
                **payload.initial_measurement.model_dump(),
            )
        )
    await session.commit()
    await session.refresh(tire_set)
    return await _tire_set_out(session, tire_set)


@router.patch("/tires/{set_id}", response_model=TireSetOut)
async def update_tire_set(
    set_id: int, payload: TireSetUpdate, current_user: CurrentUser, session: SessionDep
):
    tire_set = await _load_owned_set(session, current_user, set_id)
    data = payload.model_dump(exclude_unset=True)
    activating = data.get("is_active") is True and not tire_set.is_active
    for field, value in data.items():
        setattr(tire_set, field, value)
    if activating:
        others = (
            await session.execute(
                select(TireSet).where(
                    TireSet.car_id == tire_set.car_id,
                    TireSet.id != tire_set.id,
                    TireSet.is_active.is_(True),
                )
            )
        ).scalars().all()
        for s in others:
            s.is_active = False
    await session.commit()
    await session.refresh(tire_set)
    return await _tire_set_out(session, tire_set)


@router.delete("/tires/{set_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
async def delete_tire_set(set_id: int, current_user: CurrentUser, session: SessionDep):
    tire_set = await _load_owned_set(session, current_user, set_id)
    await session.delete(tire_set)
    await session.commit()


@router.post(
    "/tires/{set_id}/measurements",
    response_model=MeasurementOut,
    status_code=status.HTTP_201_CREATED,
)
async def add_measurement(
    set_id: int,
    payload: MeasurementCreate,
    current_user: CurrentUser,
    session: SessionDep,
):
    tire_set = await _load_owned_set(session, current_user, set_id)
    measurement = TireMeasurement(tire_set_id=tire_set.id, **payload.model_dump())
    session.add(measurement)
    await session.commit()
    await session.refresh(measurement)
    return _measurement_out(measurement)


@router.get("/tires/{set_id}/trend", response_model=TrendResponse)
async def tire_trend(set_id: int, current_user: CurrentUser, session: SessionDep):
    tire_set = await _load_owned_set(session, current_user, set_id)
    today = date.today()
    measurements = (
        await session.execute(
            select(TireMeasurement).where(TireMeasurement.tire_set_id == set_id)
        )
    ).scalars().all()
    readings = (
        await session.execute(
            select(OdometerReading).where(OdometerReading.car_id == tire_set.car_id)
        )
    ).scalars().all()
    proj = projection_service.compute_projection(
        list(measurements), list(readings), today=today
    )
    return TrendResponse(
        points=[TrendPoint(km=p.km, actual=p.actual) for p in proj.points],
        projection=[
            ProjectionPoint(km=p.km, projected=p.projected) for p in proj.projection
        ],
        reference_mm=proj.reference_mm,
        projection_date=proj.projection_date,
    )
