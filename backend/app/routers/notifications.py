"""Notification rule, log, and test/run endpoints."""

from __future__ import annotations

import csv
import io
from datetime import date

from fastapi import APIRouter, HTTPException, Query, Response, status
from sqlalchemy import select

from app.dependencies import CurrentAdmin, CurrentUser, SessionDep, user_owns_car
from app.models.car import Car
from app.models.notification import NotificationLog, NotificationRule
from app.schemas.common import StatusResponse
from app.schemas.notification import (
    NotificationLogOut,
    NotificationRuleCreate,
    NotificationRuleOut,
    NotificationRuleUpdate,
    NotificationTestRequest,
)
from app.services import (
    email_service,
    matrix_service,
    notification_service,
    settings_service,
)

router = APIRouter(tags=["notifications"])


def _rule_status(rule: NotificationRule) -> str:
    if not rule.is_active:
        return "paused"
    if rule.is_smart:
        return "smart"
    return "active"


async def _rule_out(session, rule: NotificationRule) -> NotificationRuleOut:
    car = await session.get(Car, rule.car_id)
    return NotificationRuleOut(
        id=rule.id,
        car_id=rule.car_id,
        car_name=car.name if car else None,
        item_type=rule.item_type,
        lead_days_1=rule.lead_days_1,
        lead_days_2=rule.lead_days_2,
        lead_days_3=rule.lead_days_3,
        is_active=rule.is_active,
        is_smart=rule.is_smart,
        channel_email=rule.channel_email,
        channel_matrix=rule.channel_matrix,
        status=_rule_status(rule),
    )


# ── Rules ───────────────────────────────────────────────────────────────
@router.get("/notification-rules", response_model=list[NotificationRuleOut])
async def list_rules(
    current_user: CurrentUser,
    session: SessionDep,
    car_id: int | None = Query(default=None),
):
    stmt = select(NotificationRule).order_by(NotificationRule.id)
    if car_id is not None:
        if not await user_owns_car(session, current_user, car_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access to this car is forbidden",
            )
        stmt = stmt.where(NotificationRule.car_id == car_id)
    elif not current_user.is_admin:
        from app.models.car import UserCarGroup

        ids = (
            await session.execute(
                select(UserCarGroup.car_id).where(UserCarGroup.user_id == current_user.id)
            )
        ).scalars().all()
        if not ids:
            return []
        stmt = stmt.where(NotificationRule.car_id.in_(ids))
    rules = (await session.execute(stmt)).scalars().all()
    return [await _rule_out(session, r) for r in rules]


async def _assert_owns_car(session, current_user, car_id: int) -> None:
    """403 unless the user owns ``car_id`` (admins always pass)."""
    if not await user_owns_car(session, current_user, car_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access to this car is forbidden",
        )


@router.post(
    "/notification-rules",
    response_model=NotificationRuleOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_rule(
    payload: NotificationRuleCreate,
    current_user: CurrentUser,
    session: SessionDep,
):
    car = await session.get(Car, payload.car_id)
    if car is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Car not found")
    # A rule may be managed by the owner of its car (admins manage any car).
    await _assert_owns_car(session, current_user, payload.car_id)
    rule = NotificationRule(**payload.model_dump())
    session.add(rule)
    await session.commit()
    await session.refresh(rule)
    return await _rule_out(session, rule)


@router.patch("/notification-rules/{rule_id}", response_model=NotificationRuleOut)
async def update_rule(
    rule_id: int,
    payload: NotificationRuleUpdate,
    current_user: CurrentUser,
    session: SessionDep,
):
    rule = await session.get(NotificationRule, rule_id)
    if rule is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rule not found")
    await _assert_owns_car(session, current_user, rule.car_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(rule, field, value)
    await session.commit()
    await session.refresh(rule)
    return await _rule_out(session, rule)


@router.delete("/notification-rules/{rule_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
async def delete_rule(
    rule_id: int, current_user: CurrentUser, session: SessionDep
):
    rule = await session.get(NotificationRule, rule_id)
    if rule is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rule not found")
    await _assert_owns_car(session, current_user, rule.car_id)
    await session.delete(rule)
    await session.commit()


# ── Log ─────────────────────────────────────────────────────────────────
async def _log_out(session, row: NotificationLog) -> NotificationLogOut:
    car = await session.get(Car, row.car_id)
    return NotificationLogOut(
        id=row.id,
        sent_at=row.sent_at,
        car_name=car.name if car else None,
        item_type=row.item_type,
        channel=row.channel,
        recipient=row.recipient,
        status=row.status,
        subject=row.subject,
    )


async def _accessible_car_ids(session, user) -> list[int] | None:
    """Car ids the user may see (``None`` = all, for admins)."""
    if user.is_admin:
        return None
    from app.models.car import UserCarGroup

    rows = (
        await session.execute(
            select(UserCarGroup.car_id).where(UserCarGroup.user_id == user.id)
        )
    ).scalars().all()
    return list(rows)


@router.get("/notification-log", response_model=list[NotificationLogOut])
async def list_log(
    current_user: CurrentUser,
    session: SessionDep,
    limit: int = Query(default=100, ge=1, le=1000),
    status_filter: str | None = Query(default=None, alias="status"),
):
    # Non-admins see only the log entries for cars assigned to them.
    ids = await _accessible_car_ids(session, current_user)
    stmt = select(NotificationLog).order_by(NotificationLog.sent_at.desc())
    if ids is not None:
        if not ids:
            return []
        stmt = stmt.where(NotificationLog.car_id.in_(ids))
    if status_filter:
        stmt = stmt.where(NotificationLog.status == status_filter)
    stmt = stmt.limit(limit)
    rows = (await session.execute(stmt)).scalars().all()
    return [await _log_out(session, r) for r in rows]


@router.get("/notification-log/export.csv")
async def export_log_csv(_: CurrentAdmin, session: SessionDep) -> Response:
    rows = (
        await session.execute(
            select(NotificationLog).order_by(NotificationLog.sent_at.desc())
        )
    ).scalars().all()
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(
        ["id", "sent_at", "car_id", "item_type", "channel", "recipient", "status", "subject"]
    )
    for r in rows:
        writer.writerow(
            [
                r.id,
                r.sent_at.isoformat() if r.sent_at else "",
                r.car_id,
                r.item_type or "",
                r.channel,
                r.recipient or "",
                r.status,
                r.subject or "",
            ]
        )
    return Response(
        content=buf.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=notification-log.csv"},
    )


# ── Test / run ──────────────────────────────────────────────────────────
@router.post("/notifications/test", response_model=StatusResponse)
async def test_notification(
    payload: NotificationTestRequest, _: CurrentAdmin, session: SessionDep
) -> StatusResponse:
    cfg = await settings_service.load_all(session)
    locale = cfg.get("default_locale", "sk")
    car_name = "Test"
    if payload.car_id is not None:
        car = await session.get(Car, payload.car_id)
        if car is not None:
            car_name = car.name
    context = {
        "car_name": car_name,
        "item_label": "STK",
        "item_name_sk": "STK",
        "item_name_en": "MOT inspection",
        "valid_until": date.today().isoformat(),
        "days_left": 10,
        "overdue": False,
        "subject": "FleetCare test",
    }
    html = email_service.render_template("expiring_document", locale, context)

    if payload.channel == "email":
        smtp = settings_service.smtp_config(cfg)
        to = payload.to
        if not to:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A recipient 'to' is required for an email test",
            )
        try:
            await email_service.send_email(
                smtp=smtp, to=to, subject="FleetCare test", html_body=html
            )
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Email send failed: {exc}",
            ) from exc
        return StatusResponse(status="sent", detail=f"email sent to {to}")

    # Matrix
    matrix_cfg = settings_service.matrix_config(cfg)
    try:
        await matrix_service.send_matrix(
            config=matrix_cfg, body=html, room=payload.to or None
        )
    except matrix_service.MatrixDisabledError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Matrix send failed: {exc}",
        ) from exc
    return StatusResponse(status="sent", detail="matrix message sent")


@router.post(
    "/notifications/run", response_model=StatusResponse, status_code=status.HTTP_202_ACCEPTED
)
async def run_now(_: CurrentAdmin, session: SessionDep) -> StatusResponse:
    """Manually trigger the full daily notification run."""
    summary = await notification_service.run_all(session)
    return StatusResponse(status="accepted", detail=str(summary))
