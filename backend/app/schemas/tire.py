"""Tire set, measurement, and trend/projection schemas."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


# ── Measurement ─────────────────────────────────────────────────────────
class MeasurementBase(BaseModel):
    measured_at: date
    odometer_km: int = Field(ge=0)
    tread_fl_mm: Decimal
    tread_fr_mm: Decimal
    tread_rl_mm: Decimal
    tread_rr_mm: Decimal
    pressure_fl_before_bar: Decimal | None = None
    pressure_fr_before_bar: Decimal | None = None
    pressure_rl_before_bar: Decimal | None = None
    pressure_rr_before_bar: Decimal | None = None
    pressure_fl_after_bar: Decimal | None = None
    pressure_fr_after_bar: Decimal | None = None
    pressure_rl_after_bar: Decimal | None = None
    pressure_rr_after_bar: Decimal | None = None


class MeasurementCreate(MeasurementBase):
    pass


class MeasurementUpdate(BaseModel):
    """Partial update for a measurement (all fields optional)."""

    measured_at: date | None = None
    odometer_km: int | None = Field(default=None, ge=0)
    tread_fl_mm: Decimal | None = None
    tread_fr_mm: Decimal | None = None
    tread_rl_mm: Decimal | None = None
    tread_rr_mm: Decimal | None = None
    pressure_fl_before_bar: Decimal | None = None
    pressure_fr_before_bar: Decimal | None = None
    pressure_rl_before_bar: Decimal | None = None
    pressure_rr_before_bar: Decimal | None = None
    pressure_fl_after_bar: Decimal | None = None
    pressure_fr_after_bar: Decimal | None = None
    pressure_rl_after_bar: Decimal | None = None
    pressure_rr_after_bar: Decimal | None = None


class MeasurementOut(BaseModel):
    # Numeric fields the FE computes on are serialized as JSON numbers (float),
    # not Decimal-as-string, to avoid NaN on the client.
    model_config = ConfigDict(from_attributes=True)

    id: int
    measured_at: date
    odometer_km: int
    tread_fl_mm: float | None = None
    tread_fr_mm: float | None = None
    tread_rl_mm: float | None = None
    tread_rr_mm: float | None = None
    pressure_fl_before_bar: float | None = None
    pressure_fr_before_bar: float | None = None
    pressure_rl_before_bar: float | None = None
    pressure_rr_before_bar: float | None = None
    pressure_fl_after_bar: float | None = None
    pressure_fr_after_bar: float | None = None
    pressure_rl_after_bar: float | None = None
    pressure_rr_after_bar: float | None = None
    avg_tread_mm: float | None = None


# ── Tire set ────────────────────────────────────────────────────────────
class TireSetCreate(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    season: Literal["winter", "summer", "all_season"]
    mounted_at: date | None = None
    mounted_odometer_km: int | None = Field(default=None, ge=0)
    expected_change_date: date | None = None
    initial_measurement: MeasurementCreate | None = None


class TireSetUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=128)
    season: Literal["winter", "summer", "all_season"] | None = None
    is_active: bool | None = None
    mounted_at: date | None = None
    mounted_odometer_km: int | None = Field(default=None, ge=0)
    expected_change_date: date | None = None


class TireSetOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    season: str
    is_active: bool
    mounted_at: date | None = None
    mounted_odometer_km: int | None = None
    expected_change_date: date | None = None
    avg_tread_mm: float | None = None
    mileage_km: int | None = None
    avg_pressure_bar: float | None = None
    projection_date: date | None = None
    measurements: list[MeasurementOut] = Field(default_factory=list)


# ── Trend / projection ──────────────────────────────────────────────────
class TrendPoint(BaseModel):
    km: float
    actual: float


class ProjectionPoint(BaseModel):
    km: float
    projected: float


class TrendResponse(BaseModel):
    points: list[TrendPoint] = Field(default_factory=list)
    projection: list[ProjectionPoint] = Field(default_factory=list)
    reference_mm: float = 1.6
    projection_date: date | None = None
    # Odometer reading at which the 1.6 mm reference is reached. Present even
    # when no calendar date can be computed (FE falls back to "≈ at X km").
    km_at_reference: float | None = None
