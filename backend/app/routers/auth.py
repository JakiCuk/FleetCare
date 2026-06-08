"""Auth endpoints: login, refresh, logout, me."""

from __future__ import annotations

import jwt
from fastapi import APIRouter, Cookie, HTTPException, Request, Response, status

from app.config import settings
from app.dependencies import CurrentUser, SessionDep
from app.ratelimit import AUTH_RATE_LIMIT, limiter
from app.routers._serializers import serialize_user
from app.schemas.auth import LoginRequest, LoginResponse, RefreshResponse
from app.schemas.user import UserOut
from app.security import (
    REFRESH_TOKEN_TYPE,
    create_access_token,
    decode_token,
)
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])

REFRESH_COOKIE = "refresh_token"


def _set_refresh_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=REFRESH_COOKIE,
        value=token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=settings.jwt_refresh_ttl_days * 24 * 3600,
        path="/api/auth",
    )


@router.post("/login", response_model=LoginResponse)
@limiter.limit(AUTH_RATE_LIMIT)
async def login(
    request: Request,
    payload: LoginRequest,
    response: Response,
    session: SessionDep,
) -> LoginResponse:
    """Authenticate, set a refresh cookie, and return an access token + user."""
    user = await auth_service.authenticate(
        session, payload.username, payload.password
    )
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )
    access_token, refresh_token = auth_service.issue_tokens(user)
    _set_refresh_cookie(response, refresh_token)
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user=await serialize_user(session, user),
    )


@router.post("/refresh", response_model=RefreshResponse)
@limiter.limit(AUTH_RATE_LIMIT)
async def refresh(
    request: Request,
    session: SessionDep,
    refresh_token: str | None = Cookie(default=None, alias=REFRESH_COOKIE),
) -> RefreshResponse:
    """Issue a new access token from a valid refresh cookie."""
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing refresh token"
        )
    try:
        payload = decode_token(refresh_token, expected_type=REFRESH_TOKEN_TYPE)
        user_id = int(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        ) from exc

    from app.models.user import User

    user = await session.get(User, user_id)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        )
    return RefreshResponse(access_token=create_access_token(user.id))


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(response: Response) -> Response:
    """Clear the refresh cookie."""
    response.delete_cookie(REFRESH_COOKIE, path="/api/auth")
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


@router.get("/me", response_model=UserOut)
async def me(current_user: CurrentUser, session: SessionDep) -> UserOut:
    """Return the currently authenticated user."""
    return await serialize_user(session, current_user)
