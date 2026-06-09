"""Service record and service interval schemas."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

ServiceCategory = Literal["service", "repair", "tires", "other"]


# ── Service records ─────────────────────────────────────────────────────
class ServiceRecordBase(BaseModel):
    performed_at: date
    odometer_km: int | None = Field(default=None, ge=0)
    category: ServiceCategory
    description: str | None = None
    cost: Decimal | None = None
    shop: str | None = Field(default=None, max_length=128)
    warranty_until: date | None = None
    performed_items: list[str] | None = None
    additional_work: list[str] | None = None
    oil_name: str | None = Field(default=None, max_length=128)
    next_oil_change_km: int | None = Field(default=None, ge=0)
    defect_found: bool | None = None
    defect_description: str | None = None
    tire_action: str | None = Field(default=None, max_length=32)
    season: str | None = Field(default=None, max_length=16)
    create_reminder: bool | None = None
    # --- next service terms (service book "Vaše ďalšie termíny servisu") ---
    next_service_date: date | None = None
    next_service_km: int | None = Field(default=None, ge=0)
    next_service_by_indicator: bool | None = None
    next_additional_desc: str | None = Field(default=None, max_length=255)
    next_additional_date: date | None = None
    next_additional_km: int | None = Field(default=None, ge=0)


class ServiceRecordCreate(ServiceRecordBase):
    pass


class ServiceRecordUpdate(BaseModel):
    performed_at: date | None = None
    odometer_km: int | None = Field(default=None, ge=0)
    category: ServiceCategory | None = None
    description: str | None = None
    cost: Decimal | None = None
    shop: str | None = Field(default=None, max_length=128)
    warranty_until: date | None = None
    performed_items: list[str] | None = None
    additional_work: list[str] | None = None
    oil_name: str | None = Field(default=None, max_length=128)
    next_oil_change_km: int | None = Field(default=None, ge=0)
    defect_found: bool | None = None
    defect_description: str | None = None
    tire_action: str | None = Field(default=None, max_length=32)
    season: str | None = Field(default=None, max_length=16)
    create_reminder: bool | None = None
    # --- next service terms (service book "Vaše ďalšie termíny servisu") ---
    next_service_date: date | None = None
    next_service_km: int | None = Field(default=None, ge=0)
    next_service_by_indicator: bool | None = None
    next_additional_desc: str | None = Field(default=None, max_length=255)
    next_additional_date: date | None = None
    next_additional_km: int | None = Field(default=None, ge=0)


class ServiceRecordOut(BaseModel):
    # ``cost`` is serialized as a JSON number (float), not Decimal-as-string,
    # so the FE can compute on it without NaN.
    model_config = ConfigDict(from_attributes=True)

    id: int
    performed_at: date
    odometer_km: int | None = None
    category: str
    description: str | None = None
    cost: float | None = None
    shop: str | None = None
    warranty_until: date | None = None
    performed_items: list[str] | None = None
    additional_work: list[str] | None = None
    oil_name: str | None = None
    next_oil_change_km: int | None = None
    defect_found: bool | None = None
    defect_description: str | None = None
    tire_action: str | None = None
    season: str | None = None
    create_reminder: bool | None = None
    # --- next service terms (service book "Vaše ďalšie termíny servisu") ---
    next_service_date: date | None = None
    next_service_km: int | None = None
    next_service_by_indicator: bool | None = None
    next_additional_desc: str | None = None
    next_additional_date: date | None = None
    next_additional_km: int | None = None


# ── Service intervals ───────────────────────────────────────────────────
class ServiceIntervalBase(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    interval_km: int | None = Field(default=None, ge=0)
    interval_months: int | None = Field(default=None, ge=0)
    last_performed_km: int | None = Field(default=None, ge=0)
    last_performed_at: date | None = None
    is_active: bool = True


class ServiceIntervalCreate(ServiceIntervalBase):
    pass


class ServiceIntervalUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=128)
    interval_km: int | None = Field(default=None, ge=0)
    interval_months: int | None = Field(default=None, ge=0)
    last_performed_km: int | None = Field(default=None, ge=0)
    last_performed_at: date | None = None
    is_active: bool | None = None


class ServiceIntervalOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    interval_km: int | None = None
    interval_months: int | None = None
    last_performed_km: int | None = None
    last_performed_at: date | None = None
    next_due_km: int | None = None
    next_due_date: date | None = None
    km_left: int | None = None
    days_left: int | None = None
    is_active: bool
