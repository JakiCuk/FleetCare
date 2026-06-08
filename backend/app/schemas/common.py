"""Shared Pydantic models and helpers."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict


class ORMModel(BaseModel):
    """Base model that reads attributes off ORM instances."""

    model_config = ConfigDict(from_attributes=True)


class MessageResponse(BaseModel):
    """Generic ``{"status": ...}`` style response."""

    status: str
    detail: str | None = None


class StatusResponse(BaseModel):
    """Response for test/run actions returning a status string."""

    status: str
    detail: str | None = None


def days_left(valid_until: date | None, today: date) -> int | None:
    """``(valid_until - today)`` in whole days; ``None`` if no date."""
    if valid_until is None:
        return None
    return (valid_until - today).days
