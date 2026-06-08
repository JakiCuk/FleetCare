"""Authentication: credential verification + token issuance."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.security import create_access_token, create_refresh_token, verify_password


async def authenticate(
    session: AsyncSession, username: str, password: str
) -> User | None:
    """Return the active user for valid credentials, else ``None``."""
    result = await session.execute(
        select(User).where(User.username == username)
    )
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def issue_tokens(user: User) -> tuple[str, str]:
    """Create ``(access_token, refresh_token)`` for a user."""
    return create_access_token(user.id), create_refresh_token(user.id)
