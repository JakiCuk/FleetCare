"""Health check: verifies DB + Redis connectivity."""

from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy import text

from app.config import settings
from app.database import async_session_maker

router = APIRouter(tags=["health"])

VERSION = "0.1.0"


@router.get("/health")
async def health() -> dict:
    """Report overall status plus DB and Redis sub-statuses."""
    db_status = "ok"
    try:
        async with async_session_maker() as session:
            await session.execute(text("SELECT 1"))
    except Exception:  # noqa: BLE001
        db_status = "error"

    redis_status = "ok"
    try:
        import redis.asyncio as aioredis

        client = aioredis.from_url(settings.redis_url)
        try:
            await client.ping()
        finally:
            await client.aclose()
    except Exception:  # noqa: BLE001
        redis_status = "error"

    overall = "ok" if db_status == "ok" and redis_status == "ok" else "degraded"
    return {
        "status": overall,
        "db": db_status,
        "redis": redis_status,
        "version": VERSION,
        "build": settings.build_version,
    }
