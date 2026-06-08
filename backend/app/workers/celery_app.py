"""Celery application + beat schedule.

The docker-compose worker/beat services run this as
``-A app.workers.celery_app.celery``.

The three daily checks run at the configured ``daily_send_time`` (default 08:00)
in the configured timezone. Because the schedule is built at import time (before
a DB connection is guaranteed), the time is read from the ``DAILY_SEND_TIME``
env var (falling back to 08:00); admins can still trigger an immediate run via
``POST /api/notifications/run``.
"""

from __future__ import annotations

import os

from celery import Celery
from celery.schedules import crontab

import app.models  # noqa: F401  # register all ORM mappers before any query
from app.config import settings


def _parse_hh_mm(value: str, default: tuple[int, int] = (8, 0)) -> tuple[int, int]:
    try:
        hh, mm = value.strip().split(":", 1)
        return int(hh), int(mm)
    except (ValueError, AttributeError):
        return default


_send_hour, _send_minute = _parse_hh_mm(os.environ.get("DAILY_SEND_TIME", "08:00"))

celery = Celery(
    "fleetcare",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.workers.tasks"],
)

celery.conf.update(
    timezone=settings.tz,
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_max_tasks_per_child=200,
    broker_connection_retry_on_startup=True,
)

celery.conf.beat_schedule = {
    "check-document-expiries": {
        "task": "app.workers.tasks.check_document_expiries",
        "schedule": crontab(hour=_send_hour, minute=_send_minute),
    },
    "check-service-intervals": {
        "task": "app.workers.tasks.check_service_intervals",
        "schedule": crontab(hour=_send_hour, minute=_send_minute),
    },
    "check-tire-projections": {
        "task": "app.workers.tasks.check_tire_projections",
        "schedule": crontab(hour=_send_hour, minute=_send_minute),
    },
}
