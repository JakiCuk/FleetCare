"""Fuel record and fuel statistics schemas."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class FuelRecordBase(BaseModel):
    refueled_at: date
    odometer_km: int = Field(ge=0)
    liters: Decimal = Field(gt=0)
    price_per_liter: Decimal | None = None
    total_cost: Decimal | None = None
    full_tank: bool = True


class FuelRecordCreate(FuelRecordBase):
    pass


class FuelRecordUpdate(BaseModel):
    refueled_at: date | None = None
    odometer_km: int | None = Field(default=None, ge=0)
    liters: Decimal | None = Field(default=None, gt=0)
    price_per_liter: Decimal | None = None
    total_cost: Decimal | None = None
    full_tank: bool | None = None


class FuelRecordOut(BaseModel):
    # Numeric fields the FE computes/displays are serialized as JSON numbers
    # (float), not Decimal-as-string, to avoid NaN on the client.
    model_config = ConfigDict(from_attributes=True)

    id: int
    refueled_at: date
    odometer_km: int
    liters: float
    price_per_liter: float | None = None
    total_cost: float | None = None
    full_tank: bool
    consumption_l_100km: float | None = None


class FuelMonthlyPoint(BaseModel):
    month: str
    consumption: float | None = None


class FuelStats(BaseModel):
    avg_consumption: float | None = None
    total_spent: float = 0.0
    count: int = 0
    monthly: list[FuelMonthlyPoint] = Field(default_factory=list)
