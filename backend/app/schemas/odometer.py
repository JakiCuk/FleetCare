"""Odometer reading schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class OdometerCreate(BaseModel):
    """Payload for ``POST /api/cars/{id}/odometer``."""

    reading_km: int = Field(ge=0)
    recorded_at: datetime | None = None
    note: str | None = Field(default=None, max_length=255)


class OdometerOut(BaseModel):
    """Odometer reading as returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    reading_km: int
    recorded_at: datetime
    note: str | None = None
