"""FastAPI dependencies: current user, admin guard, car-ownership guard."""

from __future__ import annotations

from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models.car import Car, UserCarGroup
from app.models.user import User
from app.security import ACCESS_TOKEN_TYPE, decode_token

# auto_error=False so we can return a uniform 401 with our own detail.
_bearer = HTTPBearer(auto_error=False)

SessionDep = Annotated[AsyncSession, Depends(get_session)]

_CREDENTIALS_EXC = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Not authenticated",
    headers={"WWW-Authenticate": "Bearer"},
)


async def get_current_user(
    session: SessionDep,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)] = None,
) -> User:
    """Resolve the authenticated, active user from the Bearer access token."""
    if credentials is None or not credentials.credentials:
        raise _CREDENTIALS_EXC
    try:
        payload = decode_token(credentials.credentials, expected_type=ACCESS_TOKEN_TYPE)
        user_id = int(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError) as exc:
        raise _CREDENTIALS_EXC from exc

    user = await session.get(User, user_id)
    if user is None or not user.is_active:
        raise _CREDENTIALS_EXC
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


async def get_current_admin(current_user: CurrentUser) -> User:
    """Require the current user to be an admin."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return current_user


CurrentAdmin = Annotated[User, Depends(get_current_admin)]


async def user_owns_car(session: AsyncSession, user: User, car_id: int) -> bool:
    """Whether a non-admin user is assigned to ``car_id`` via user_car_groups."""
    if user.is_admin:
        return True
    result = await session.execute(
        select(UserCarGroup.id).where(
            UserCarGroup.user_id == user.id,
            UserCarGroup.car_id == car_id,
        )
    )
    return result.scalar_one_or_none() is not None


async def get_owned_car(session: AsyncSession, user: User, car_id: int) -> Car:
    """Load a car, asserting it exists (404) and the user may access it (403)."""
    car = await session.get(Car, car_id)
    if car is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Car not found",
        )
    if not await user_owns_car(session, user, car_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access to this car is forbidden",
        )
    return car


async def assert_car_access(session: AsyncSession, user: User, car_id: int) -> None:
    """Raise 404/403 if the user cannot access ``car_id`` (without loading the row)."""
    await get_owned_car(session, user, car_id)
