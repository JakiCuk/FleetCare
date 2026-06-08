"""Car schemas, including the aggregated CarDetail."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.dashboard import OverdueFlags
from app.schemas.document import InsuranceOut, STKOut, VignetteOut


class CarBase(BaseModel):
    """Mutable car fields shared by create/update."""

    name: str = Field(min_length=1, max_length=128)
    make: str | None = Field(default=None, max_length=64)
    model: str | None = Field(default=None, max_length=64)
    year: int | None = Field(default=None, ge=1900, le=2100)
    license_plate: str = Field(min_length=1, max_length=16)
    vin: str | None = Field(default=None, max_length=32)
    current_odometer_km: int = Field(default=0, ge=0)


class CarCreate(CarBase):
    """Payload for ``POST /api/cars``."""


class CarUpdate(BaseModel):
    """Partial update for a car."""

    name: str | None = Field(default=None, min_length=1, max_length=128)
    make: str | None = Field(default=None, max_length=64)
    model: str | None = Field(default=None, max_length=64)
    year: int | None = Field(default=None, ge=1900, le=2100)
    license_plate: str | None = Field(default=None, min_length=1, max_length=16)
    vin: str | None = Field(default=None, max_length=32)
    current_odometer_km: int | None = Field(default=None, ge=0)


class CarOut(BaseModel):
    """Car object as returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    full_name: str | None = None
    make: str | None = None
    model: str | None = None
    year: int | None = None
    license_plate: str
    vin: str | None = None
    current_odometer_km: int


class TireSummary(BaseModel):
    """Compact active-tire-set summary for car detail/dashboard."""

    id: int
    name: str
    season: str
    avg_tread_mm: float | None = None
    projection_date: date | None = None


class NextServiceSummary(BaseModel):
    """Compact next-due service summary."""

    name: str
    km_left: int | None = None
    days_left: int | None = None
    label: str


class CarDetail(CarOut):
    """Car + aggregated document/service/tire fields (dashboard parity)."""

    stk: list[STKOut] = Field(default_factory=list)
    pzp: list[InsuranceOut] = Field(default_factory=list)
    kasko: list[InsuranceOut] = Field(default_factory=list)
    vignettes: list[VignetteOut] = Field(default_factory=list)
    active_tire_set: TireSummary | None = None
    next_service: NextServiceSummary | None = None
    overdue: OverdueFlags
    monthly_cost: float
