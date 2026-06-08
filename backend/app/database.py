"""SQLAlchemy 2.0 async database setup for FleetCare.

This module is intentionally dependency-light: it reads ``DATABASE_URL`` directly
from the environment (it does NOT import ``app.config``) so that ORM models and
Alembic migrations can import :data:`Base` / :data:`engine` without pulling in the
full application configuration stack.

Public import surface:
    - ``Base``                — declarative base for all ORM models
    - ``engine``              — async engine bound to ``DATABASE_URL``
    - ``async_session_maker`` — ``async_sessionmaker[AsyncSession]``
    - ``get_session``         — FastAPI dependency yielding an ``AsyncSession``
    - ``DATABASE_URL``        — resolved connection string (for diagnostics)
"""

from __future__ import annotations

import os
from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncAttrs,
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

# Default points at the docker-compose ``db`` service; matches the
# ``DATABASE_URL`` composed in ``docker-compose.yml``. Override via env.
DEFAULT_DATABASE_URL = (
    "postgresql+asyncpg://fleetcare:changeme@localhost:5432/fleetcare"
)

DATABASE_URL: str = os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL)


class Base(AsyncAttrs, DeclarativeBase):
    """Declarative base shared by every ORM model.

    Inherits :class:`AsyncAttrs` so lazy relationships can be awaited
    explicitly (``await obj.awaitable_attrs.relation``) in async sessions.
    """


# ``pool_pre_ping`` guards against stale connections after DB restarts.
engine: AsyncEngine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    future=True,
)

# ``expire_on_commit=False`` keeps attributes usable after commit (FastAPI
# response serialization happens after the session context closes).
async_session_maker: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_session() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency that yields a transactional :class:`AsyncSession`.

    Usage::

        @router.get(...)
        async def handler(session: AsyncSession = Depends(get_session)):
            ...
    """
    async with async_session_maker() as session:
        yield session
