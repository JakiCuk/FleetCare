"""Expense endpoints + category breakdown."""

from __future__ import annotations

from collections import defaultdict
from datetime import date

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select

from app.dependencies import CurrentUser, SessionDep, get_owned_car, user_owns_car
from app.models.expense import Expense
from app.models.fuel import FuelRecord
from app.models.service import ServiceRecord
from app.schemas.expense import (
    ExpenseBreakdown,
    ExpenseBreakdownItem,
    ExpenseCreate,
    ExpenseOut,
    ExpenseUpdate,
)
from app.services.fuel_service import _total_cost as _fuel_total_cost

router = APIRouter(tags=["expenses"])


async def _load_owned(session, current_user, expense_id: int) -> Expense:
    obj = await session.get(Expense, expense_id)
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found")
    if not await user_owns_car(session, current_user, obj.car_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access to this car is forbidden",
        )
    return obj


@router.get("/cars/{car_id}/expenses", response_model=list[ExpenseOut])
async def list_expenses(
    car_id: int,
    current_user: CurrentUser,
    session: SessionDep,
    from_date: date | None = Query(default=None),
    to_date: date | None = Query(default=None),
):
    await get_owned_car(session, current_user, car_id)
    stmt = select(Expense).where(Expense.car_id == car_id)
    if from_date is not None:
        stmt = stmt.where(Expense.occurred_at >= from_date)
    if to_date is not None:
        stmt = stmt.where(Expense.occurred_at <= to_date)
    rows = (
        await session.execute(stmt.order_by(Expense.occurred_at.desc()))
    ).scalars().all()
    return [ExpenseOut.model_validate(r) for r in rows]


@router.post(
    "/cars/{car_id}/expenses",
    response_model=ExpenseOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_expense(
    car_id: int, payload: ExpenseCreate, current_user: CurrentUser, session: SessionDep
):
    await get_owned_car(session, current_user, car_id)
    row = Expense(car_id=car_id, **payload.model_dump())
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return ExpenseOut.model_validate(row)


@router.patch("/expenses/{expense_id}", response_model=ExpenseOut)
async def update_expense(
    expense_id: int,
    payload: ExpenseUpdate,
    current_user: CurrentUser,
    session: SessionDep,
):
    row = await _load_owned(session, current_user, expense_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(row, field, value)
    await session.commit()
    await session.refresh(row)
    return ExpenseOut.model_validate(row)


@router.delete("/expenses/{expense_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
async def delete_expense(
    expense_id: int, current_user: CurrentUser, session: SessionDep
):
    row = await _load_owned(session, current_user, expense_id)
    await session.delete(row)
    await session.commit()


@router.get("/cars/{car_id}/expenses/breakdown", response_model=ExpenseBreakdown)
async def expenses_breakdown(
    car_id: int,
    current_user: CurrentUser,
    session: SessionDep,
    from_date: date | None = Query(default=None),
    to_date: date | None = Query(default=None),
) -> ExpenseBreakdown:
    """Category breakdown summing manual expenses + fuel + service costs.

    Fuel records (``total_cost``, else liters*price) bucket into ``fuel`` and
    service records (``cost``) into ``service`` — the existing english category
    keys — so the FE colour map and totals stay consistent and avoid double rows.
    """
    await get_owned_car(session, current_user, car_id)
    totals: dict[str, float] = defaultdict(float)

    exp_stmt = select(Expense.category, Expense.amount).where(
        Expense.car_id == car_id
    )
    if from_date is not None:
        exp_stmt = exp_stmt.where(Expense.occurred_at >= from_date)
    if to_date is not None:
        exp_stmt = exp_stmt.where(Expense.occurred_at <= to_date)
    for category, amount in (await session.execute(exp_stmt)).all():
        totals[category] += float(amount) if amount is not None else 0.0

    fuel_stmt = select(FuelRecord).where(FuelRecord.car_id == car_id)
    if from_date is not None:
        fuel_stmt = fuel_stmt.where(FuelRecord.refueled_at >= from_date)
    if to_date is not None:
        fuel_stmt = fuel_stmt.where(FuelRecord.refueled_at <= to_date)
    for r in (await session.execute(fuel_stmt)).scalars().all():
        totals["fuel"] += _fuel_total_cost(r)

    svc_stmt = select(ServiceRecord.cost).where(ServiceRecord.car_id == car_id)
    if from_date is not None:
        svc_stmt = svc_stmt.where(ServiceRecord.performed_at >= from_date)
    if to_date is not None:
        svc_stmt = svc_stmt.where(ServiceRecord.performed_at <= to_date)
    for (cost,) in (await session.execute(svc_stmt)).all():
        if cost is not None:
            totals["service"] += float(cost)

    # Drop zero buckets so empty categories don't clutter the chart.
    totals = {k: v for k, v in totals.items() if round(v, 2) != 0.0}
    total = round(sum(totals.values()), 2)
    breakdown = [
        ExpenseBreakdownItem(category=cat, amount=round(amt, 2))
        for cat, amt in sorted(totals.items(), key=lambda kv: kv[1], reverse=True)
    ]
    return ExpenseBreakdown(total=total, breakdown=breakdown)
