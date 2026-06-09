"""Car schemas, including the aggregated CarDetail."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict, Field

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


class CarCreate(BaseModel):
    """Payload for ``POST /api/cars``.

    ``name`` is optional at the API level; when omitted the router derives it
    from ``"{make} {model}"`` (the DB column stays NOT NULL).
    """

    name: str | None = Field(default=None, min_length=1, max_length=128)
    make: str | None = Field(default=None, max_length=64)
    model: str | None = Field(default=None, max_length=64)
    year: int | None = Field(default=None, ge=1900, le=2100)
    license_plate: str = Field(min_length=1, max_length=16)
    vin: str | None = Field(default=None, max_length=32)
    current_odometer_km: int = Field(default=0, ge=0)


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


class DocStatus(BaseModel):
    """Compact validity status for a single document type in the cars list."""

    valid_until: date
    days_left: int | None = None


class CarListItem(CarOut):
    """Enriched car-list row: ``CarOut`` + per-document validity + overdue flag.

    ``stk``/``pzp``/``kasko`` carry the current (latest ``valid_until``) record's
    ``valid_until`` + ``days_left`` (``null`` when the car has no such document),
    letting the fleet list show STK, PZP and KASKO separately with a detailed
    state. ``overdue`` mirrors the dashboard "any tracked item past due" flag.
    """

    stk: DocStatus | None = None
    pzp: DocStatus | None = None
    kasko: DocStatus | None = None
    overdue: bool = False


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
    """Car + aggregated document/service/tire fields (dashboard parity).

    ``stk``/``pzp``/``kasko`` are the single *current* (latest valid_until)
    records used by the Overview "upcoming deadlines" widget; the full history
    is available via the per-document endpoints. ``overdue`` is a simple flag
    (true if any tracked item is past due), matching the dashboard card.
    """

    stk: STKOut | None = None
    pzp: InsuranceOut | None = None
    kasko: InsuranceOut | None = None
    vignettes: list[VignetteOut] = Field(default_factory=list)
    active_tire_set: TireSummary | None = None
    next_service: NextServiceSummary | None = None
    overdue: bool = False
    monthly_cost: float
