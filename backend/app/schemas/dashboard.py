"""Dashboard aggregation schemas."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field


class OverdueFlags(BaseModel):
    """Per-car overdue indicators (used in car detail + dashboard)."""

    any: bool = False
    stk: bool = False
    insurance: bool = False
    vignette: bool = False
    service: bool = False
    tires: bool = False


class DashboardChip(BaseModel):
    """A countdown chip on a dashboard car card (FE colours by ``days_left``)."""

    label: str
    days_left: int | None = None


class DashboardCar(BaseModel):
    """A single car entry on the dashboard grid."""

    id: int
    name: str
    license_plate: str
    current_odometer_km: int
    chips: list[DashboardChip] = Field(default_factory=list)
    next_service: str | None = None
    tires: str | None = None
    overdue: bool = False


class DashboardStats(BaseModel):
    """Top-row fleet statistics."""

    cars: int = 0
    notifications_today: int = 0
    overdue_items: int = 0
    monthly_cost: float = 0.0


class DashboardResponse(BaseModel):
    """``GET /api/dashboard`` payload."""

    stats: DashboardStats
    cars: list[DashboardCar] = Field(default_factory=list)


class CarAggregate(BaseModel):
    """Internal aggregate produced by the dashboard service for a single car.

    Reused by ``CarDetail`` assembly so the aggregation lives in one place.
    """

    id: int
    name: str
    license_plate: str
    current_odometer_km: int
    chips: list[DashboardChip] = Field(default_factory=list)
    next_service_label: str | None = None
    tires_label: str | None = None
    overdue: OverdueFlags = Field(default_factory=OverdueFlags)
    monthly_cost: float = 0.0
    active_tire_set_id: int | None = None
    active_tire_set_name: str | None = None
    active_tire_set_season: str | None = None
    active_tire_set_avg_tread_mm: float | None = None
    active_tire_set_projection_date: date | None = None
    next_service_name: str | None = None
    next_service_km_left: int | None = None
    next_service_days_left: int | None = None
