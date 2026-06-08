"""Document schemas: STK (technical inspection), insurance, vignettes."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


# ── STK / technical inspection ──────────────────────────────────────────
class STKBase(BaseModel):
    inspected_at: date | None = None
    valid_until: date
    cost: Decimal | None = None
    provider: str | None = Field(default=None, max_length=128)
    note: str | None = Field(default=None, max_length=255)


class STKCreate(STKBase):
    pass


class STKUpdate(BaseModel):
    inspected_at: date | None = None
    valid_until: date | None = None
    cost: Decimal | None = None
    provider: str | None = Field(default=None, max_length=128)
    note: str | None = Field(default=None, max_length=255)


class STKOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    inspected_at: date | None = None
    valid_until: date
    cost: Decimal | None = None
    provider: str | None = None
    note: str | None = None
    days_left: int | None = None


# ── Insurance ───────────────────────────────────────────────────────────
class InsuranceBase(BaseModel):
    type: Literal["PZP", "KASKO"]
    provider: str | None = Field(default=None, max_length=128)
    policy_number: str | None = Field(default=None, max_length=64)
    valid_from: date | None = None
    valid_until: date
    cost: Decimal | None = None


class InsuranceCreate(InsuranceBase):
    pass


class InsuranceUpdate(BaseModel):
    type: Literal["PZP", "KASKO"] | None = None
    provider: str | None = Field(default=None, max_length=128)
    policy_number: str | None = Field(default=None, max_length=64)
    valid_from: date | None = None
    valid_until: date | None = None
    cost: Decimal | None = None


class InsuranceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    type: str
    provider: str | None = None
    policy_number: str | None = None
    valid_from: date | None = None
    valid_until: date
    cost: Decimal | None = None
    days_left: int | None = None


# ── Vignette ────────────────────────────────────────────────────────────
class VignetteBase(BaseModel):
    country: str = Field(min_length=1, max_length=4)
    valid_from: date | None = None
    valid_until: date
    cost: Decimal | None = None
    provider: str | None = Field(default=None, max_length=128)


class VignetteCreate(VignetteBase):
    pass


class VignetteUpdate(BaseModel):
    country: str | None = Field(default=None, min_length=1, max_length=4)
    valid_from: date | None = None
    valid_until: date | None = None
    cost: Decimal | None = None
    provider: str | None = Field(default=None, max_length=128)


class VignetteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    country: str
    valid_from: date | None = None
    valid_until: date
    cost: Decimal | None = None
    provider: str | None = None
    days_left: int | None = None


class DocumentsBundle(BaseModel):
    """Combined documents view for ``GET /api/cars/{id}/documents``."""

    stk: list[STKOut] = Field(default_factory=list)
    insurance: list[InsuranceOut] = Field(default_factory=list)
    vignettes: list[VignetteOut] = Field(default_factory=list)
