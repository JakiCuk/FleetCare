"""Notification rule, log, and test/run schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


# ── Rules ───────────────────────────────────────────────────────────────
class NotificationRuleBase(BaseModel):
    car_id: int
    item_type: str = Field(min_length=1, max_length=32)
    lead_days_1: int | None = Field(default=30, ge=0)
    lead_days_2: int | None = Field(default=14, ge=0)
    lead_days_3: int | None = Field(default=7, ge=0)
    is_active: bool = True
    is_smart: bool = False
    channel_email: bool = True
    channel_matrix: bool = False


class NotificationRuleCreate(NotificationRuleBase):
    pass


class NotificationRuleUpdate(BaseModel):
    item_type: str | None = Field(default=None, min_length=1, max_length=32)
    lead_days_1: int | None = Field(default=None, ge=0)
    lead_days_2: int | None = Field(default=None, ge=0)
    lead_days_3: int | None = Field(default=None, ge=0)
    is_active: bool | None = None
    is_smart: bool | None = None
    channel_email: bool | None = None
    channel_matrix: bool | None = None


class NotificationRuleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    car_id: int
    car_name: str | None = None
    item_type: str
    lead_days_1: int | None = None
    lead_days_2: int | None = None
    lead_days_3: int | None = None
    is_active: bool
    is_smart: bool
    channel_email: bool
    channel_matrix: bool
    status: str = "active"


# ── Log ─────────────────────────────────────────────────────────────────
class NotificationLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sent_at: datetime
    car_name: str | None = None
    item_type: str | None = None
    channel: str
    recipient: str | None = None
    status: str
    subject: str | None = None


# ── Test / run ──────────────────────────────────────────────────────────
class NotificationTestRequest(BaseModel):
    channel: Literal["email", "matrix"]
    car_id: int | None = None
    to: str | None = None
