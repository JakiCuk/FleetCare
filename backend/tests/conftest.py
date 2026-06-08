"""Shared pytest fixtures for FleetCare backend integration tests.

Provides:
    * ``test_engine``     — an async engine bound to ``TEST_DATABASE_URL`` (falling
      back to ``DATABASE_URL``) that creates all tables once per session and drops
      them afterwards.
    * ``session``         — a per-test ``AsyncSession`` on the test engine.
    * ``client``          — an ``httpx.AsyncClient`` driving ``app.main:app`` via an
      ASGI transport, with the ``get_session`` dependency overridden to the test
      session so HTTP handlers and the test share one transaction-visible DB.
    * ``admin_user``      — a freshly created admin (hashed via ``app.security``).
    * ``admin_token``     — a bearer access token for ``admin_user``.
    * ``admin_client``    — ``client`` pre-loaded with the admin Authorization header.

Pure-logic unit tests do not use these fixtures; they import the service modules
directly and never touch the database.
"""

from __future__ import annotations

import os
import uuid
from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.database import Base, get_session
from app.main import app
from app.models.user import User
from app.security import create_access_token, hash_password

# Prefer a dedicated test DB; fall back to the app's DATABASE_URL so a single
# Postgres service can back both the module-level engine and these fixtures.
TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    os.environ.get(
        "DATABASE_URL",
        "postgresql+asyncpg://fleetcare:changeme@localhost:5432/fleetcare",
    ),
)


@pytest_asyncio.fixture
async def test_engine() -> AsyncIterator:
    """Function-scoped engine; creates a clean schema per test, drops it after.

    Function scope keeps every test on the same event loop as the engine
    (pytest-asyncio 0.23 uses a per-test loop) and guarantees DB isolation
    between tests at the cost of a create_all/drop_all per test.
    """
    engine = create_async_engine(TEST_DATABASE_URL, future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    try:
        yield engine
    finally:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await engine.dispose()


@pytest_asyncio.fixture
async def session(test_engine) -> AsyncIterator[AsyncSession]:
    """A per-test async session bound to the test engine."""
    maker = async_sessionmaker(
        bind=test_engine, class_=AsyncSession, expire_on_commit=False, autoflush=False
    )
    async with maker() as s:
        yield s


@pytest_asyncio.fixture
async def client(test_engine) -> AsyncIterator[AsyncClient]:
    """HTTP client for the ASGI app with ``get_session`` bound to the test engine."""
    maker = async_sessionmaker(
        bind=test_engine, class_=AsyncSession, expire_on_commit=False, autoflush=False
    )

    async def _override_get_session() -> AsyncIterator[AsyncSession]:
        async with maker() as s:
            yield s

    app.dependency_overrides[get_session] = _override_get_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac
    app.dependency_overrides.pop(get_session, None)


@pytest_asyncio.fixture
async def admin_user(session: AsyncSession) -> User:
    """Create and persist an admin user with a known password.

    The plaintext password is attached as ``user._plain_password`` so login
    fixtures/tests can authenticate against the real hashing path.
    """
    suffix = uuid.uuid4().hex[:8]
    plain = "admin-password-123"
    user = User(
        username=f"admin_{suffix}",
        email=f"admin_{suffix}@fleetcare.test",
        full_name="Test Admin",
        hashed_password=hash_password(plain),
        is_admin=True,
        is_active=True,
        locale="sk",
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    user._plain_password = plain  # type: ignore[attr-defined]
    return user


@pytest_asyncio.fixture
async def admin_token(admin_user: User) -> str:
    """A bearer access token for the admin user."""
    return create_access_token(admin_user.id)


@pytest_asyncio.fixture
async def admin_client(client: AsyncClient, admin_token: str) -> AsyncClient:
    """``client`` with the admin Authorization header pre-set."""
    client.headers["Authorization"] = f"Bearer {admin_token}"
    return client
