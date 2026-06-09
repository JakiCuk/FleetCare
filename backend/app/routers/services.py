"""Service record and service interval endpoints."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.dependencies import CurrentUser, SessionDep, get_owned_car, user_owns_car
from app.models.car import Car
from app.models.service import ServiceInterval, ServiceRecord
from app.schemas.service import (
    ServiceIntervalCreate,
    ServiceIntervalOut,
    ServiceIntervalUpdate,
    ServiceRecordCreate,
    ServiceRecordOut,
    ServiceRecordUpdate,
)
from app.services.dashboard_service import _add_months

router = APIRouter(tags=["services"])


def _record_out(r: ServiceRecord) -> ServiceRecordOut:
    return ServiceRecordOut.model_validate(r)


def _interval_out(iv: ServiceInterval, current_km: int, today: date) -> ServiceIntervalOut:
    next_due_km = None
    km_left = None
    if iv.interval_km is not None and iv.last_performed_km is not None:
        next_due_km = iv.last_performed_km + iv.interval_km
        km_left = next_due_km - current_km
    next_due_date = None
    days_left = None
    if iv.interval_months is not None and iv.last_performed_at is not None:
        next_due_date = _add_months(iv.last_performed_at, iv.interval_months)
        days_left = (next_due_date - today).days
    return ServiceIntervalOut(
        id=iv.id,
        name=iv.name,
        interval_km=iv.interval_km,
        interval_months=iv.interval_months,
        last_performed_km=iv.last_performed_km,
        last_performed_at=iv.last_performed_at,
        next_due_km=next_due_km,
        next_due_date=next_due_date,
        km_left=km_left,
        days_left=days_left,
        is_active=iv.is_active,
    )


async def _load_owned(session, current_user, model, item_id: int, label: str):
    obj = await session.get(model, item_id)
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{label} not found")
    if not await user_owns_car(session, current_user, obj.car_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access to this car is forbidden",
        )
    return obj


def _interval_name(row: ServiceRecord) -> str:
    """Stable interval name derived from a service record (≤128 chars).

    Keyed by category/description so repeated reminders for the same kind of
    work upsert the same ``ServiceInterval`` rather than creating duplicates.
    """
    base = (row.description or "").strip()
    if not base:
        base = {
            "service": "Servisná prehliadka",
            "repair": "Oprava",
            "tires": "Pneumatiky",
            "other": "Servis",
        }.get(row.category, "Servis")
    return base[:128]


async def _upsert_reminder_interval(session, row: ServiceRecord) -> None:
    """Idempotently create/update a ServiceInterval for a record's next term.

    Runs when ``create_reminder`` is set and at least one next term (date or km)
    is present. The interval (km/months) is derived from the gap between the
    record's odometer/date and the requested next term, and ``last_performed_*``
    anchors are set so the intervals panel + smart notifications fire correctly.
    A stable name (``_interval_name``) keeps the upsert idempotent.
    """
    if not row.create_reminder:
        return
    if row.next_service_date is None and row.next_service_km is None:
        return

    interval_km: int | None = None
    if row.next_service_km is not None and row.odometer_km is not None:
        gap = row.next_service_km - row.odometer_km
        interval_km = gap if gap > 0 else None
    interval_months: int | None = None
    if row.next_service_date is not None and row.performed_at is not None:
        months = (
            (row.next_service_date.year - row.performed_at.year) * 12
            + (row.next_service_date.month - row.performed_at.month)
        )
        interval_months = months if months > 0 else None

    name = _interval_name(row)
    existing = (
        await session.execute(
            select(ServiceInterval).where(
                ServiceInterval.car_id == row.car_id,
                ServiceInterval.name == name,
            )
        )
    ).scalars().first()
    if existing is None:
        session.add(
            ServiceInterval(
                car_id=row.car_id,
                name=name,
                interval_km=interval_km,
                interval_months=interval_months,
                last_performed_km=row.odometer_km,
                last_performed_at=row.performed_at,
                is_active=True,
            )
        )
    else:
        existing.interval_km = interval_km
        existing.interval_months = interval_months
        existing.last_performed_km = row.odometer_km
        existing.last_performed_at = row.performed_at
        existing.is_active = True


# ── Service records ──────────────────────────────────────────────────────
@router.get("/cars/{car_id}/services", response_model=list[ServiceRecordOut])
async def list_services(car_id: int, current_user: CurrentUser, session: SessionDep):
    await get_owned_car(session, current_user, car_id)
    rows = (
        await session.execute(
            select(ServiceRecord)
            .where(ServiceRecord.car_id == car_id)
            .order_by(ServiceRecord.performed_at.desc())
        )
    ).scalars().all()
    return [_record_out(r) for r in rows]


@router.post(
    "/cars/{car_id}/services",
    response_model=ServiceRecordOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_service(
    car_id: int,
    payload: ServiceRecordCreate,
    current_user: CurrentUser,
    session: SessionDep,
):
    await get_owned_car(session, current_user, car_id)
    row = ServiceRecord(car_id=car_id, **payload.model_dump(exclude_unset=True))
    session.add(row)
    await session.flush()
    await _upsert_reminder_interval(session, row)
    await session.commit()
    await session.refresh(row)
    return _record_out(row)


@router.patch("/services/{service_id}", response_model=ServiceRecordOut)
async def update_service(
    service_id: int,
    payload: ServiceRecordUpdate,
    current_user: CurrentUser,
    session: SessionDep,
):
    row = await _load_owned(session, current_user, ServiceRecord, service_id, "Service record")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(row, field, value)
    await session.flush()
    await _upsert_reminder_interval(session, row)
    await session.commit()
    await session.refresh(row)
    return _record_out(row)


@router.delete("/services/{service_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
async def delete_service(
    service_id: int, current_user: CurrentUser, session: SessionDep
):
    row = await _load_owned(session, current_user, ServiceRecord, service_id, "Service record")
    await session.delete(row)
    await session.commit()


# ── Service intervals ────────────────────────────────────────────────────
@router.get("/cars/{car_id}/service-intervals", response_model=list[ServiceIntervalOut])
async def list_intervals(car_id: int, current_user: CurrentUser, session: SessionDep):
    car = await get_owned_car(session, current_user, car_id)
    today = date.today()
    rows = (
        await session.execute(
            select(ServiceInterval)
            .where(ServiceInterval.car_id == car_id)
            .order_by(ServiceInterval.name)
        )
    ).scalars().all()
    return [_interval_out(iv, car.current_odometer_km, today) for iv in rows]


@router.post(
    "/cars/{car_id}/service-intervals",
    response_model=ServiceIntervalOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_interval(
    car_id: int,
    payload: ServiceIntervalCreate,
    current_user: CurrentUser,
    session: SessionDep,
):
    car = await get_owned_car(session, current_user, car_id)
    row = ServiceInterval(car_id=car_id, **payload.model_dump())
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return _interval_out(row, car.current_odometer_km, date.today())


@router.patch("/service-intervals/{interval_id}", response_model=ServiceIntervalOut)
async def update_interval(
    interval_id: int,
    payload: ServiceIntervalUpdate,
    current_user: CurrentUser,
    session: SessionDep,
):
    row = await _load_owned(session, current_user, ServiceInterval, interval_id, "Service interval")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(row, field, value)
    await session.commit()
    await session.refresh(row)
    car = await session.get(Car, row.car_id)
    current_km = car.current_odometer_km if car else 0
    return _interval_out(row, current_km, date.today())


@router.delete("/service-intervals/{interval_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
async def delete_interval(
    interval_id: int, current_user: CurrentUser, session: SessionDep
):
    row = await _load_owned(session, current_user, ServiceInterval, interval_id, "Service interval")
    await session.delete(row)
    await session.commit()
