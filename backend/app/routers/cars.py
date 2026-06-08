"""Car CRUD + aggregated CarDetail."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, status
from sqlalchemy import select

from app.dependencies import CurrentUser, SessionDep, get_owned_car
from app.models.car import Car, UserCarGroup
from app.models.notification import NotificationRule
from app.routers._serializers import car_full_name, serialize_car
from app.schemas.car import (
    CarCreate,
    CarDetail,
    CarOut,
    CarUpdate,
    NextServiceSummary,
    TireSummary,
)
from app.services import dashboard_service

router = APIRouter(prefix="/cars", tags=["cars"])

# Default notification rules created on car creation (lead days 30/14/7).
_DEFAULT_RULE_ITEM_TYPES = ["stk"]


async def _accessible_car_ids(session: SessionDep, user: CurrentUser) -> list[int] | None:
    """Car ids a user may see (``None`` = all, for admins)."""
    if user.is_admin:
        return None
    rows = (
        await session.execute(
            select(UserCarGroup.car_id).where(UserCarGroup.user_id == user.id)
        )
    ).scalars().all()
    return list(rows)


@router.get("", response_model=list[CarOut])
async def list_cars(current_user: CurrentUser, session: SessionDep) -> list[CarOut]:
    ids = await _accessible_car_ids(session, current_user)
    stmt = select(Car).order_by(Car.name)
    if ids is not None:
        if not ids:
            return []
        stmt = stmt.where(Car.id.in_(ids))
    cars = (await session.execute(stmt)).scalars().all()
    return [serialize_car(c) for c in cars]


@router.post("", response_model=CarOut, status_code=status.HTTP_201_CREATED)
async def create_car(
    payload: CarCreate, current_user: CurrentUser, session: SessionDep
) -> CarOut:
    car = Car(**payload.model_dump())
    session.add(car)
    await session.flush()

    # Non-admin creators are auto-assigned the new car.
    if not current_user.is_admin:
        session.add(UserCarGroup(user_id=current_user.id, car_id=car.id))

    # Auto-create default notification rules (lead days 30/14/7, email).
    for item_type in _DEFAULT_RULE_ITEM_TYPES:
        session.add(
            NotificationRule(
                car_id=car.id,
                item_type=item_type,
                lead_days_1=30,
                lead_days_2=14,
                lead_days_3=7,
                is_active=True,
                channel_email=True,
            )
        )

    await session.commit()
    await session.refresh(car)
    return serialize_car(car)


@router.get("/{car_id}", response_model=CarDetail)
async def get_car(
    car_id: int, current_user: CurrentUser, session: SessionDep
) -> CarDetail:
    car = await get_owned_car(session, current_user, car_id)
    today = date.today()
    agg = await dashboard_service.aggregate_car(session, car, today=today)

    # Document lists with days_left (reuse the documents-router serializers).
    from app.models.document import InsurancePolicy, TechnicalInspection, Vignette
    from app.routers.documents import _out_insurance, _out_stk, _out_vignette

    stk_rows = (
        await session.execute(
            select(TechnicalInspection)
            .where(TechnicalInspection.car_id == car_id)
            .order_by(TechnicalInspection.valid_until.desc())
        )
    ).scalars().all()
    ins_rows = (
        await session.execute(
            select(InsurancePolicy)
            .where(InsurancePolicy.car_id == car_id)
            .order_by(InsurancePolicy.valid_until.desc())
        )
    ).scalars().all()
    vig_rows = (
        await session.execute(
            select(Vignette)
            .where(Vignette.car_id == car_id)
            .order_by(Vignette.valid_until.desc())
        )
    ).scalars().all()

    # Single current (latest valid_until) record per document type for the
    # Overview widget; rows are ordered valid_until DESC above.
    pzp_rows = [i for i in ins_rows if i.type == "PZP"]
    kasko_rows = [i for i in ins_rows if i.type == "KASKO"]
    stk = _out_stk(stk_rows[0], today) if stk_rows else None
    pzp = _out_insurance(pzp_rows[0], today) if pzp_rows else None
    kasko = _out_insurance(kasko_rows[0], today) if kasko_rows else None
    vignettes = [_out_vignette(v, today) for v in vig_rows]

    active_tire = None
    if agg.active_tire_set_id is not None:
        active_tire = TireSummary(
            id=agg.active_tire_set_id,
            name=agg.active_tire_set_name or "",
            season=agg.active_tire_set_season or "",
            avg_tread_mm=agg.active_tire_set_avg_tread_mm,
            projection_date=agg.active_tire_set_projection_date,
        )

    next_service = None
    if agg.next_service_name is not None:
        next_service = NextServiceSummary(
            name=agg.next_service_name,
            km_left=agg.next_service_km_left,
            days_left=agg.next_service_days_left,
            label=agg.next_service_label or agg.next_service_name,
        )

    return CarDetail(
        id=car.id,
        name=car.name,
        full_name=car_full_name(car),
        make=car.make,
        model=car.model,
        year=car.year,
        license_plate=car.license_plate,
        vin=car.vin,
        current_odometer_km=car.current_odometer_km,
        stk=stk,
        pzp=pzp,
        kasko=kasko,
        vignettes=vignettes,
        active_tire_set=active_tire,
        next_service=next_service,
        overdue=agg.overdue.any,
        monthly_cost=agg.monthly_cost,
    )


@router.patch("/{car_id}", response_model=CarOut)
async def update_car(
    car_id: int, payload: CarUpdate, current_user: CurrentUser, session: SessionDep
) -> CarOut:
    car = await get_owned_car(session, current_user, car_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(car, field, value)
    await session.commit()
    await session.refresh(car)
    return serialize_car(car)


@router.delete("/{car_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_car(
    car_id: int, current_user: CurrentUser, session: SessionDep
) -> None:
    car = await get_owned_car(session, current_user, car_id)
    await session.delete(car)
    await session.commit()
