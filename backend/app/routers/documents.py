"""Document endpoints: STK, insurance, vignettes (+ combined view)."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.dependencies import CurrentUser, SessionDep, get_owned_car, user_owns_car
from app.models.document import InsurancePolicy, TechnicalInspection, Vignette
from app.routers._serializers import days_left
from app.schemas.document import (
    DocumentsBundle,
    InsuranceCreate,
    InsuranceOut,
    InsuranceUpdate,
    STKCreate,
    STKOut,
    STKUpdate,
    VignetteCreate,
    VignetteOut,
    VignetteUpdate,
)

router = APIRouter(tags=["documents"])


def _out_stk(row: TechnicalInspection, today: date) -> STKOut:
    return STKOut(
        id=row.id,
        inspected_at=row.inspected_at,
        valid_until=row.valid_until,
        cost=row.cost,
        provider=row.provider,
        note=row.note,
        days_left=days_left(row.valid_until, today),
    )


def _out_insurance(row: InsurancePolicy, today: date) -> InsuranceOut:
    return InsuranceOut(
        id=row.id,
        type=row.type,
        provider=row.provider,
        policy_number=row.policy_number,
        valid_from=row.valid_from,
        valid_until=row.valid_until,
        cost=row.cost,
        days_left=days_left(row.valid_until, today),
    )


def _out_vignette(row: Vignette, today: date) -> VignetteOut:
    return VignetteOut(
        id=row.id,
        country=row.country,
        valid_from=row.valid_from,
        valid_until=row.valid_until,
        cost=row.cost,
        provider=row.provider,
        days_left=days_left(row.valid_until, today),
    )


async def _load_owned(session, current_user, model, item_id: int, label: str):
    """Load an item by id and assert the user may access its car."""
    obj = await session.get(model, item_id)
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{label} not found")
    if not await user_owns_car(session, current_user, obj.car_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access to this car is forbidden",
        )
    return obj


# ── STK ──────────────────────────────────────────────────────────────────
@router.get("/cars/{car_id}/stk", response_model=list[STKOut])
async def list_stk(car_id: int, current_user: CurrentUser, session: SessionDep):
    await get_owned_car(session, current_user, car_id)
    today = date.today()
    rows = (
        await session.execute(
            select(TechnicalInspection)
            .where(TechnicalInspection.car_id == car_id)
            .order_by(TechnicalInspection.valid_until.desc())
        )
    ).scalars().all()
    return [_out_stk(r, today) for r in rows]


@router.post("/cars/{car_id}/stk", response_model=STKOut, status_code=status.HTTP_201_CREATED)
async def create_stk(
    car_id: int, payload: STKCreate, current_user: CurrentUser, session: SessionDep
):
    await get_owned_car(session, current_user, car_id)
    row = TechnicalInspection(car_id=car_id, **payload.model_dump())
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return _out_stk(row, date.today())


@router.patch("/stk/{stk_id}", response_model=STKOut)
async def update_stk(
    stk_id: int, payload: STKUpdate, current_user: CurrentUser, session: SessionDep
):
    row = await _load_owned(session, current_user, TechnicalInspection, stk_id, "STK")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(row, field, value)
    await session.commit()
    await session.refresh(row)
    return _out_stk(row, date.today())


@router.delete("/stk/{stk_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_stk(stk_id: int, current_user: CurrentUser, session: SessionDep):
    row = await _load_owned(session, current_user, TechnicalInspection, stk_id, "STK")
    await session.delete(row)
    await session.commit()


# ── Insurance ──────────────────────────────────────────────────────────────
@router.get("/cars/{car_id}/insurance", response_model=list[InsuranceOut])
async def list_insurance(car_id: int, current_user: CurrentUser, session: SessionDep):
    await get_owned_car(session, current_user, car_id)
    today = date.today()
    rows = (
        await session.execute(
            select(InsurancePolicy)
            .where(InsurancePolicy.car_id == car_id)
            .order_by(InsurancePolicy.valid_until.desc())
        )
    ).scalars().all()
    return [_out_insurance(r, today) for r in rows]


@router.post(
    "/cars/{car_id}/insurance",
    response_model=InsuranceOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_insurance(
    car_id: int, payload: InsuranceCreate, current_user: CurrentUser, session: SessionDep
):
    await get_owned_car(session, current_user, car_id)
    row = InsurancePolicy(car_id=car_id, **payload.model_dump())
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return _out_insurance(row, date.today())


@router.patch("/insurance/{insurance_id}", response_model=InsuranceOut)
async def update_insurance(
    insurance_id: int,
    payload: InsuranceUpdate,
    current_user: CurrentUser,
    session: SessionDep,
):
    row = await _load_owned(session, current_user, InsurancePolicy, insurance_id, "Insurance")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(row, field, value)
    await session.commit()
    await session.refresh(row)
    return _out_insurance(row, date.today())


@router.delete("/insurance/{insurance_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_insurance(
    insurance_id: int, current_user: CurrentUser, session: SessionDep
):
    row = await _load_owned(session, current_user, InsurancePolicy, insurance_id, "Insurance")
    await session.delete(row)
    await session.commit()


# ── Vignettes ──────────────────────────────────────────────────────────────
@router.get("/cars/{car_id}/vignettes", response_model=list[VignetteOut])
async def list_vignettes(car_id: int, current_user: CurrentUser, session: SessionDep):
    await get_owned_car(session, current_user, car_id)
    today = date.today()
    rows = (
        await session.execute(
            select(Vignette)
            .where(Vignette.car_id == car_id)
            .order_by(Vignette.valid_until.desc())
        )
    ).scalars().all()
    return [_out_vignette(r, today) for r in rows]


@router.post(
    "/cars/{car_id}/vignettes",
    response_model=VignetteOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_vignette(
    car_id: int, payload: VignetteCreate, current_user: CurrentUser, session: SessionDep
):
    await get_owned_car(session, current_user, car_id)
    row = Vignette(car_id=car_id, **payload.model_dump())
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return _out_vignette(row, date.today())


@router.patch("/vignettes/{vignette_id}", response_model=VignetteOut)
async def update_vignette(
    vignette_id: int,
    payload: VignetteUpdate,
    current_user: CurrentUser,
    session: SessionDep,
):
    row = await _load_owned(session, current_user, Vignette, vignette_id, "Vignette")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(row, field, value)
    await session.commit()
    await session.refresh(row)
    return _out_vignette(row, date.today())


@router.delete("/vignettes/{vignette_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_vignette(
    vignette_id: int, current_user: CurrentUser, session: SessionDep
):
    row = await _load_owned(session, current_user, Vignette, vignette_id, "Vignette")
    await session.delete(row)
    await session.commit()


# ── Combined view ──────────────────────────────────────────────────────────
@router.get("/cars/{car_id}/documents", response_model=DocumentsBundle)
async def documents_bundle(
    car_id: int, current_user: CurrentUser, session: SessionDep
) -> DocumentsBundle:
    await get_owned_car(session, current_user, car_id)
    today = date.today()
    stk_rows = (
        await session.execute(
            select(TechnicalInspection).where(TechnicalInspection.car_id == car_id)
        )
    ).scalars().all()
    ins_rows = (
        await session.execute(
            select(InsurancePolicy).where(InsurancePolicy.car_id == car_id)
        )
    ).scalars().all()
    vig_rows = (
        await session.execute(select(Vignette).where(Vignette.car_id == car_id))
    ).scalars().all()
    return DocumentsBundle(
        stk=[_out_stk(r, today) for r in stk_rows],
        insurance=[_out_insurance(r, today) for r in ins_rows],
        vignettes=[_out_vignette(r, today) for r in vig_rows],
    )
