"""Dashboard aggregation endpoint."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter
from sqlalchemy import select

from app.dependencies import CurrentUser, SessionDep
from app.models.car import Car, UserCarGroup
from app.schemas.dashboard import DashboardCar, DashboardResponse
from app.services import dashboard_service

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard", response_model=DashboardResponse)
async def dashboard(current_user: CurrentUser, session: SessionDep) -> DashboardResponse:
    stmt = select(Car).order_by(Car.name)
    if not current_user.is_admin:
        ids = (
            await session.execute(
                select(UserCarGroup.car_id).where(UserCarGroup.user_id == current_user.id)
            )
        ).scalars().all()
        if not ids:
            from app.schemas.dashboard import DashboardStats

            return DashboardResponse(stats=DashboardStats(), cars=[])
        stmt = stmt.where(Car.id.in_(ids))

    cars = (await session.execute(stmt)).scalars().all()
    stats, aggregates = await dashboard_service.build_dashboard(
        session, list(cars), today=date.today()
    )

    cars_out = [
        DashboardCar(
            id=a.id,
            name=a.name,
            license_plate=a.license_plate,
            current_odometer_km=a.current_odometer_km,
            chips=a.chips,
            next_service=a.next_service_label,
            tires=a.tires_label,
            overdue=a.overdue.any,
        )
        for a in aggregates
    ]
    return DashboardResponse(stats=stats, cars=cars_out)
