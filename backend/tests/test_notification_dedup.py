"""Tests for notification deduplication (TECHNICAL_SPECIFICATION §7.6).

The 23h window constant is verified as a pure unit test. The dedup *decision*
lives in ``notification_service._already_sent`` and queries ``notification_log``,
so it is exercised as a small integration test against the test database.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app.models.car import Car
from app.models.notification import NotificationLog
from app.services.notification_service import DEDUP_WINDOW, _already_sent


# ── Pure unit: the dedup window is exactly 23 hours ─────────────────────────
def test_dedup_window_is_23_hours() -> None:
    assert DEDUP_WINDOW == timedelta(hours=23)
    assert DEDUP_WINDOW.total_seconds() == 23 * 3600


# ── Integration: the decision flips across the 23h boundary ─────────────────
@pytest.mark.asyncio
async def test_already_sent_dedup_decision(session) -> None:
    now = datetime(2024, 6, 1, 8, 0, tzinfo=timezone.utc)

    car = Car(name="Dedup Car", license_plate="BA-DEDUP", current_odometer_km=0)
    session.add(car)
    await session.commit()
    await session.refresh(car)

    key = dict(
        car_id=car.id,
        rule_id=None,
        item_type="stk",
        lead_bucket=1,
        channel="email",
    )

    # No log yet -> not a duplicate.
    assert await _already_sent(session, now=now, **key) is False

    # A successful send 1 hour ago -> inside the 23h window -> duplicate.
    session.add(
        NotificationLog(
            car_id=car.id,
            rule_id=None,
            item_type="stk",
            lead_bucket=1,
            channel="email",
            status="sent",
            sent_at=now - timedelta(hours=1),
        )
    )
    await session.commit()
    assert await _already_sent(session, now=now, **key) is True

    # A send just over 23h ago is outside the window -> not a duplicate.
    far_past = now + timedelta(hours=24)
    assert await _already_sent(session, now=far_past, **key) is False

    # A different channel does not match the email dedup key.
    assert (
        await _already_sent(
            session,
            now=now,
            car_id=car.id,
            rule_id=None,
            item_type="stk",
            lead_bucket=1,
            channel="matrix",
        )
        is False
    )

    # A 'failed' send must NOT suppress a retry (only 'sent' dedups).
    session.add(
        NotificationLog(
            car_id=car.id,
            rule_id=None,
            item_type="pzp",
            lead_bucket=2,
            channel="email",
            status="failed",
            sent_at=now - timedelta(hours=1),
        )
    )
    await session.commit()
    assert (
        await _already_sent(
            session,
            now=now,
            car_id=car.id,
            rule_id=None,
            item_type="pzp",
            lead_bucket=2,
            channel="email",
        )
        is False
    )
