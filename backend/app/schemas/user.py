"""User and auth-embedded user schemas."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class CarRef(BaseModel):
    """Minimal car reference embedded in a User object."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class UserOut(BaseModel):
    """User object as returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    # Output is not strictly re-validated: already-stored admin emails may use
    # reserved/special-use domains (e.g. the default admin@fleetcare.local), which
    # EmailStr would reject. Input is still validated via UserCreate/UserUpdate.
    email: str
    full_name: str | None = None
    is_admin: bool
    is_active: bool
    locale: str
    cars: list[CarRef] = Field(default_factory=list)


class UserCreate(BaseModel):
    """Payload for creating a user (admin only)."""

    username: str = Field(min_length=1, max_length=64)
    email: EmailStr
    full_name: str | None = Field(default=None, max_length=128)
    password: str = Field(min_length=6, max_length=128)
    is_admin: bool = False
    locale: str = Field(default="sk", max_length=5)
    car_ids: list[int] = Field(default_factory=list)


class UserUpdate(BaseModel):
    """Partial update for a user (admin only)."""

    username: str | None = Field(default=None, min_length=1, max_length=64)
    email: EmailStr | None = None
    full_name: str | None = Field(default=None, max_length=128)
    password: str | None = Field(default=None, min_length=6, max_length=128)
    is_admin: bool | None = None
    is_active: bool | None = None
    locale: str | None = Field(default=None, max_length=5)
    car_ids: list[int] | None = None
