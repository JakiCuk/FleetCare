"""Celery tasks for the daily notification run (TECHNICAL_SPECIFICATION §8, §10).

Each task opens its own async session via an ``asyncio.run`` wrapper and
delegates to ``notification_service`` (collection → dedup → dispatch → log).
"""

from __future__ import annotations

import asyncio

import structlog

from app.database import async_session_maker
from app.services import notification_service
from app.workers.celery_app import celery

log = structlog.get_logger(__name__)


def _run(coro):
    """Run an async coroutine to completion from a sync Celery task."""
    return asyncio.run(coro)


async def _check_documents() -> dict:
    async with async_session_maker() as session:
        return await notification_service.run_document_check(session)


async def _check_services() -> dict:
    async with async_session_maker() as session:
        return await notification_service.run_service_check(session)


async def _check_tires() -> dict:
    async with async_session_maker() as session:
        return await notification_service.run_tire_check(session)


@celery.task(name="app.workers.tasks.check_document_expiries")
def check_document_expiries() -> dict:
    """STK / insurance / vignette expiry checks vs. each rule's lead days."""
    summary = _run(_check_documents())
    log.info("check_document_expiries", **summary)
    return summary


@celery.task(name="app.workers.tasks.check_service_intervals")
def check_service_intervals() -> dict:
    """Smart service-interval due checks (km / time)."""
    summary = _run(_check_services())
    log.info("check_service_intervals", **summary)
    return summary


@celery.task(name="app.workers.tasks.check_tire_projections")
def check_tire_projections() -> dict:
    """Smart tire-wear projection checks (>= 3 measurements)."""
    summary = _run(_check_tires())
    log.info("check_tire_projections", **summary)
    return summary
