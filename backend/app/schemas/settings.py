"""Application settings schemas (secrets masked on output)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class LeadDays(BaseModel):
    """Default lead days (keys named ``1``/``2``/``3`` in JSON)."""

    field_1: int = Field(default=30, alias="1")
    field_2: int = Field(default=14, alias="2")
    field_3: int = Field(default=7, alias="3")

    model_config = {"populate_by_name": True}


class SmtpOut(BaseModel):
    host: str | None = None
    port: int | None = None
    encryption: str | None = None
    username: str | None = None
    from_: str | None = Field(default=None, alias="from")
    password_set: bool = False

    model_config = {"populate_by_name": True}


class MatrixOut(BaseModel):
    enabled: bool = False
    homeserver: str | None = None
    default_room: str | None = None
    token_set: bool = False


class SettingsOut(BaseModel):
    fleet_name: str | None = None
    timezone: str | None = None
    default_locale: str | None = None
    currency: str | None = None
    default_lead_days: LeadDays = Field(default_factory=LeadDays)
    daily_send_time: str | None = None
    tire_min_tread_mm: float | None = None
    smtp: SmtpOut = Field(default_factory=SmtpOut)
    matrix: MatrixOut = Field(default_factory=MatrixOut)


class SmtpUpdate(BaseModel):
    host: str | None = None
    port: int | None = None
    encryption: Literal["tls", "ssl", "none"] | None = None
    username: str | None = None
    from_: str | None = Field(default=None, alias="from")
    password: str | None = None

    model_config = {"populate_by_name": True}


class MatrixUpdate(BaseModel):
    enabled: bool | None = None
    homeserver: str | None = None
    default_room: str | None = None
    token: str | None = None


class LeadDaysUpdate(BaseModel):
    field_1: int | None = Field(default=None, alias="1")
    field_2: int | None = Field(default=None, alias="2")
    field_3: int | None = Field(default=None, alias="3")

    model_config = {"populate_by_name": True}


class SettingsUpdate(BaseModel):
    """Partial/full settings update (PUT /api/settings)."""

    fleet_name: str | None = None
    timezone: str | None = None
    default_locale: str | None = None
    currency: str | None = None
    default_lead_days: LeadDaysUpdate | None = None
    daily_send_time: str | None = None
    tire_min_tread_mm: float | None = None
    smtp: SmtpUpdate | None = None
    matrix: MatrixUpdate | None = None


class WipeRequest(BaseModel):
    """Confirmation payload for the destructive wipe endpoint."""

    confirm: bool = False
