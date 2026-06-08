"""Authentication request/response schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.user import UserOut


class LoginRequest(BaseModel):
    """Credentials for ``POST /api/auth/login``."""

    username: str = Field(min_length=1)
    password: str = Field(min_length=1)


class LoginResponse(BaseModel):
    """Successful login response (refresh token is set as a cookie)."""

    access_token: str
    token_type: str = "bearer"
    user: UserOut


class RefreshResponse(BaseModel):
    """New access token from a valid refresh cookie."""

    access_token: str
    token_type: str = "bearer"
