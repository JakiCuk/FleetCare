"""Notification engine: evaluation, dedup, dispatch, logging.

Used by the Celery tasks (document expiries, service intervals, tire
projections) and by the admin "test send" / "run now" endpoints.

Dedup (TECHNICAL_SPECIFICATION §7.6): before dispatching for a
``(car_id, rule_id, item_type, lead_bucket, channel)`` tuple, a successful
``notification_log`` entry within the last 23 hours short-circuits the send.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.car import UserCarGroup
from app.models.document import InsurancePolicy, TechnicalInspection, Vignette
from app.models.notification import NotificationLog, NotificationRule
from app.models.odometer import OdometerReading
from app.models.service import ServiceInterval
from app.models.tire import TireMeasurement, TireSet
from app.models.user import User
from app.services import (
    email_service,
    matrix_service,
    settings_service,
)
from app.services.dashboard_service import _add_months
from app.services.projection_service import compute_projection

DEDUP_WINDOW = timedelta(hours=23)


@dataclass(slots=True)
class Candidate:
    """A single thing worth notifying about."""

    car_id: int
    car_name: str
    rule: NotificationRule | None
    item_type: str
    lead_bucket: int  # 1/2/3 for documents, 0 for smart/overdue
    template_type: str  # expiring_document | overdue_document | service_due | tire_projection
    subject_sk: str
    subject_en: str
    context: dict


def _start_of_day(d: date) -> datetime:
    return datetime.combine(d, datetime.min.time(), tzinfo=timezone.utc)


async def _recipients(session: AsyncSession, car_id: int) -> list[User]:
    """Active users assigned to a car with notifications enabled."""
    rows = (
        await session.execute(
            select(User)
            .join(UserCarGroup, UserCarGroup.user_id == User.id)
            .where(
                UserCarGroup.car_id == car_id,
                UserCarGroup.notification_enabled.is_(True),
                User.is_active.is_(True),
            )
        )
    ).scalars().all()
    return list(rows)


async def _already_sent(
    session: AsyncSession,
    *,
    car_id: int,
    rule_id: int | None,
    item_type: str,
    lead_bucket: int,
    channel: str,
    now: datetime,
) -> bool:
    """Dedup check across the trailing 23h for a successful send."""
    since = now - DEDUP_WINDOW
    stmt = select(NotificationLog.id).where(
        NotificationLog.car_id == car_id,
        NotificationLog.item_type == item_type,
        NotificationLog.lead_bucket == lead_bucket,
        NotificationLog.channel == channel,
        NotificationLog.status == "sent",
        NotificationLog.sent_at >= since,
    )
    if rule_id is None:
        stmt = stmt.where(NotificationLog.rule_id.is_(None))
    else:
        stmt = stmt.where(NotificationLog.rule_id == rule_id)
    result = await session.execute(stmt)
    return result.first() is not None


# ── Candidate collection ────────────────────────────────────────────────
async def collect_document_candidates(
    session: AsyncSession, *, today: date | None = None
) -> list[Candidate]:
    """STK / insurance / vignette candidates vs. each rule's lead days."""
    today = today or date.today()
    rules = (
        await session.execute(
            select(NotificationRule).where(
                NotificationRule.is_active.is_(True),
                NotificationRule.is_smart.is_(False),
            )
        )
    ).scalars().all()

    candidates: list[Candidate] = []
    for rule in rules:
        base_type = rule.item_type.split(":", 1)[0]
        item, label, valid_until = await _latest_doc_for_rule(session, rule, today)
        if valid_until is None:
            continue
        days_left = (valid_until - today).days
        leads = [
            (1, rule.lead_days_1),
            (2, rule.lead_days_2),
            (3, rule.lead_days_3),
        ]
        car_name = await _car_name(session, rule.car_id)

        if days_left < 0:
            candidates.append(
                _doc_candidate(rule, base_type, label, valid_until, days_left, 0, car_name, overdue=True)
            )
            continue

        # Pick the smallest lead threshold that the item has reached.
        matched_bucket = None
        for bucket, lead in leads:
            if lead is not None and days_left <= lead:
                if matched_bucket is None or lead < matched_bucket[1]:
                    matched_bucket = (bucket, lead)
        if matched_bucket is not None:
            candidates.append(
                _doc_candidate(
                    rule, base_type, label, valid_until, days_left,
                    matched_bucket[0], car_name, overdue=False,
                )
            )
    return candidates


def _doc_candidate(
    rule, base_type, label, valid_until, days_left, bucket, car_name, *, overdue
):
    item_names = {
        "stk": ("STK", "MOT inspection"),
        "pzp": ("PZP poistenie", "liability insurance (PZP)"),
        "kasko": ("KASKO poistenie", "comprehensive insurance (KASKO)"),
        "vignette": ("Diaľničná známka", "highway vignette"),
    }
    name_sk, name_en = item_names.get(base_type, (base_type.upper(), base_type))
    template = "overdue_document" if overdue else "expiring_document"
    subj_sk = (
        f"FleetCare: {name_sk} ({car_name}) je po termíne"
        if overdue
        else f"FleetCare: {name_sk} ({car_name}) o {days_left} dní"
    )
    subj_en = (
        f"FleetCare: {name_en} for {car_name} has expired"
        if overdue
        else f"FleetCare: {name_en} for {car_name} expires in {days_left} days"
    )
    return Candidate(
        car_id=rule.car_id,
        car_name=car_name,
        rule=rule,
        item_type=rule.item_type,
        lead_bucket=bucket,
        template_type=template,
        subject_sk=subj_sk,
        subject_en=subj_en,
        context={
            "car_name": car_name,
            "item_label": label,
            "item_name_sk": name_sk,
            "item_name_en": name_en,
            "valid_until": valid_until.isoformat(),
            "days_left": days_left,
            "overdue": overdue,
        },
    )


async def _latest_doc_for_rule(session: AsyncSession, rule: NotificationRule, today: date):
    """Return ``(item, label, valid_until)`` of the latest relevant document."""
    base = rule.item_type.split(":", 1)[0]
    country = rule.item_type.split(":", 1)[1] if ":" in rule.item_type else None

    if base == "stk":
        rows = (
            await session.execute(
                select(TechnicalInspection).where(
                    TechnicalInspection.car_id == rule.car_id
                )
            )
        ).scalars().all()
        if not rows:
            return None, None, None
        latest = max(rows, key=lambda r: r.valid_until)
        return latest, "STK", latest.valid_until

    if base in ("pzp", "kasko"):
        ins_type = "PZP" if base == "pzp" else "KASKO"
        rows = (
            await session.execute(
                select(InsurancePolicy).where(
                    InsurancePolicy.car_id == rule.car_id,
                    InsurancePolicy.type == ins_type,
                )
            )
        ).scalars().all()
        if not rows:
            return None, None, None
        latest = max(rows, key=lambda r: r.valid_until)
        return latest, ins_type, latest.valid_until

    if base == "vignette":
        stmt = select(Vignette).where(Vignette.car_id == rule.car_id)
        if country:
            stmt = stmt.where(Vignette.country == country)
        rows = (await session.execute(stmt)).scalars().all()
        if not rows:
            return None, None, None
        latest = max(rows, key=lambda r: r.valid_until)
        return latest, f"Vignette {latest.country}", latest.valid_until

    return None, None, None


async def collect_service_candidates(
    session: AsyncSession, *, today: date | None = None
) -> list[Candidate]:
    """Service intervals that are due (km or time) for smart rules."""
    today = today or date.today()
    rules = (
        await session.execute(
            select(NotificationRule).where(
                NotificationRule.is_active.is_(True),
                NotificationRule.is_smart.is_(True),
                NotificationRule.item_type == "service",
            )
        )
    ).scalars().all()

    candidates: list[Candidate] = []
    for rule in rules:
        car = await _car(session, rule.car_id)
        if car is None:
            continue
        intervals = (
            await session.execute(
                select(ServiceInterval).where(
                    ServiceInterval.car_id == rule.car_id,
                    ServiceInterval.is_active.is_(True),
                )
            )
        ).scalars().all()
        for iv in intervals:
            km_left = None
            if iv.interval_km is not None and iv.last_performed_km is not None:
                km_left = (iv.last_performed_km + iv.interval_km) - car.current_odometer_km
            days_left = None
            if iv.interval_months is not None and iv.last_performed_at is not None:
                days_left = (_add_months(iv.last_performed_at, iv.interval_months) - today).days

            due = (km_left is not None and km_left <= 2000) or (
                days_left is not None and days_left <= 30
            )
            if not due:
                continue
            candidates.append(
                Candidate(
                    car_id=rule.car_id,
                    car_name=car.name,
                    rule=rule,
                    item_type="service",
                    lead_bucket=0,
                    template_type="service_due",
                    subject_sk=f"FleetCare: servis „{iv.name}“ ({car.name}) sa blíži",
                    subject_en=f"FleetCare: service '{iv.name}' for {car.name} is due",
                    context={
                        "car_name": car.name,
                        "interval_name": iv.name,
                        "km_left": km_left,
                        "days_left": days_left,
                    },
                )
            )
    return candidates


async def collect_tire_candidates(
    session: AsyncSession, *, today: date | None = None
) -> list[Candidate]:
    """Smart tire-wear projections (>= 3 measurements) past their threshold."""
    today = today or date.today()
    rules = (
        await session.execute(
            select(NotificationRule).where(
                NotificationRule.is_active.is_(True),
                NotificationRule.is_smart.is_(True),
                NotificationRule.item_type == "tires",
            )
        )
    ).scalars().all()

    min_tread = await _min_tread(session)
    candidates: list[Candidate] = []
    for rule in rules:
        car = await _car(session, rule.car_id)
        if car is None:
            continue
        active_set = (
            await session.execute(
                select(TireSet).where(
                    TireSet.car_id == rule.car_id, TireSet.is_active.is_(True)
                )
            )
        ).scalars().first()
        if active_set is None:
            continue
        measurements = (
            await session.execute(
                select(TireMeasurement).where(
                    TireMeasurement.tire_set_id == active_set.id
                )
            )
        ).scalars().all()
        if len(measurements) < 3:
            continue
        readings = (
            await session.execute(
                select(OdometerReading).where(OdometerReading.car_id == rule.car_id)
            )
        ).scalars().all()
        proj = compute_projection(
            list(measurements), list(readings),
            current_odometer_km=car.current_odometer_km, today=today,
        )

        trigger = False
        if proj.latest_avg_tread_mm is not None and proj.latest_avg_tread_mm < min_tread:
            trigger = True
        if (
            proj.projection_date is not None
            and active_set.expected_change_date is not None
            and proj.projection_date < active_set.expected_change_date
        ):
            trigger = True
        if not trigger:
            continue

        candidates.append(
            Candidate(
                car_id=rule.car_id,
                car_name=car.name,
                rule=rule,
                item_type="tires",
                lead_bucket=0,
                template_type="tire_projection",
                subject_sk=f"FleetCare: pneumatiky ({car.name}) sa blížia k 1,6 mm",
                subject_en=f"FleetCare: tires for {car.name} are nearing 1.6 mm",
                context={
                    "car_name": car.name,
                    "tire_set_name": active_set.name,
                    "avg_tread_mm": proj.latest_avg_tread_mm,
                    "projection_date": (
                        proj.projection_date.isoformat()
                        if proj.projection_date
                        else None
                    ),
                    "expected_change_date": (
                        active_set.expected_change_date.isoformat()
                        if active_set.expected_change_date
                        else None
                    ),
                },
            )
        )
    return candidates


# ── Dispatch ────────────────────────────────────────────────────────────
async def dispatch_candidates(
    session: AsyncSession, candidates: list[Candidate]
) -> dict:
    """Send notifications for candidates, with dedup + logging.

    Returns a small summary dict: ``{sent, skipped, failed}``.
    """
    cfg = await settings_service.load_all(session)
    smtp = settings_service.smtp_config(cfg)
    matrix_cfg = settings_service.matrix_config(cfg)
    fleet_locale = cfg.get("default_locale", "sk")
    now = datetime.now(timezone.utc)

    summary = {"sent": 0, "skipped": 0, "failed": 0}

    for cand in candidates:
        recipients = await _recipients(session, cand.car_id)
        rule = cand.rule
        channels = []
        if rule is None or rule.channel_email:
            channels.append("email")
        if rule is not None and rule.channel_matrix:
            channels.append("matrix")

        for channel in channels:
            rule_id = rule.id if rule is not None else None
            if await _already_sent(
                session,
                car_id=cand.car_id,
                rule_id=rule_id,
                item_type=cand.item_type,
                lead_bucket=cand.lead_bucket,
                channel=channel,
                now=now,
            ):
                summary["skipped"] += 1
                continue

            if channel == "email":
                await _dispatch_email(
                    session, cand, recipients, smtp, fleet_locale, summary
                )
            elif channel == "matrix":
                await _dispatch_matrix(
                    session, cand, matrix_cfg, fleet_locale, summary
                )

    await session.commit()
    return summary


async def _dispatch_email(session, cand, recipients, smtp, fleet_locale, summary):
    targets = [(u.email, u.locale or fleet_locale) for u in recipients if u.email]
    if not targets:
        _log(session, cand, "email", recipient=None, status="skipped",
             subject=cand.subject_sk, error="no recipients")
        summary["skipped"] += 1
        return
    for email, locale in targets:
        subject = cand.subject_sk if locale == "sk" else cand.subject_en
        html = email_service.render_template(
            cand.template_type, locale, {**cand.context, "subject": subject}
        )
        try:
            await email_service.send_email(
                smtp=smtp, to=email, subject=subject, html_body=html
            )
            _log(session, cand, "email", recipient=email, status="sent", subject=subject)
            summary["sent"] += 1
        except Exception as exc:  # noqa: BLE001
            _log(session, cand, "email", recipient=email, status="failed",
                 subject=subject, error=str(exc)[:1000])
            summary["failed"] += 1


async def _dispatch_matrix(session, cand, matrix_cfg, fleet_locale, summary):
    subject = cand.subject_sk if fleet_locale == "sk" else cand.subject_en
    body = email_service.render_template(
        cand.template_type, fleet_locale, {**cand.context, "subject": subject}
    )
    room = matrix_cfg.get("default_room") or None
    try:
        await matrix_service.send_matrix(config=matrix_cfg, body=body, room=room)
        _log(session, cand, "matrix", recipient=room, status="sent", subject=subject)
        summary["sent"] += 1
    except matrix_service.MatrixDisabledError as exc:
        _log(session, cand, "matrix", recipient=room, status="skipped",
             subject=subject, error=str(exc))
        summary["skipped"] += 1
    except Exception as exc:  # noqa: BLE001
        _log(session, cand, "matrix", recipient=room, status="failed",
             subject=subject, error=str(exc)[:1000])
        summary["failed"] += 1


def _log(session, cand, channel, *, recipient, status, subject, error=None):
    session.add(
        NotificationLog(
            car_id=cand.car_id,
            rule_id=cand.rule.id if cand.rule is not None else None,
            item_type=cand.item_type,
            lead_bucket=cand.lead_bucket,
            channel=channel,
            recipient=recipient,
            subject=subject,
            status=status,
            error=error,
        )
    )


# ── small helpers ───────────────────────────────────────────────────────
async def _car(session: AsyncSession, car_id: int):
    from app.models.car import Car

    return await session.get(Car, car_id)


async def _car_name(session: AsyncSession, car_id: int) -> str:
    car = await _car(session, car_id)
    return car.name if car is not None else f"car #{car_id}"


async def _min_tread(session: AsyncSession) -> float:
    val = await settings_service.get_value(session, "tire_min_tread_mm", "2.5")
    try:
        return float(val)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return 2.5


# ── Orchestration entry points (used by Celery tasks + run-now) ─────────
async def run_document_check(session: AsyncSession) -> dict:
    candidates = await collect_document_candidates(session)
    return await dispatch_candidates(session, candidates)


async def run_service_check(session: AsyncSession) -> dict:
    candidates = await collect_service_candidates(session)
    return await dispatch_candidates(session, candidates)


async def run_tire_check(session: AsyncSession) -> dict:
    candidates = await collect_tire_candidates(session)
    return await dispatch_candidates(session, candidates)


async def run_all(session: AsyncSession) -> dict:
    docs = await collect_document_candidates(session)
    svc = await collect_service_candidates(session)
    tires = await collect_tire_candidates(session)
    return await dispatch_candidates(session, docs + svc + tires)
