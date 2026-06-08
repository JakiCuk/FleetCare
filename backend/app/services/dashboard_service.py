"""Dashboard / car aggregation (TECHNICAL_SPECIFICATION §7.3, §7.4, §8).

Produces, per car: days-to-expiry chips (STK/insurance/vignette), next due
service, active tire set summary, overdue flags, and a rolling 30-day cost.
Cars are returned sorted by urgency (overdue first, then smallest days_left).
"""

from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.car import Car
from app.models.document import InsurancePolicy, TechnicalInspection, Vignette
from app.models.expense import Expense
from app.models.notification import NotificationLog
from app.models.odometer import OdometerReading
from app.models.service import ServiceInterval
from app.models.tire import TireMeasurement, TireSet
from app.schemas.dashboard import (
    CarAggregate,
    DashboardChip,
    DashboardStats,
    OverdueFlags,
)
from app.services import projection_service


def _days_left(valid_until: date | None, today: date) -> int | None:
    if valid_until is None:
        return None
    return (valid_until - today).days


def _latest_doc(rows: list, key) -> object | None:
    """Latest (max valid_until) document of a list, or None."""
    if not rows:
        return None
    return max(rows, key=key)


async def aggregate_car(
    session: AsyncSession,
    car: Car,
    *,
    today: date | None = None,
) -> CarAggregate:
    """Build the aggregate view for a single car."""
    today = today or date.today()
    overdue_any = False
    chips: list[DashboardChip] = []
    flags = {"stk": False, "insurance": False, "vignette": False, "service": False, "tires": False}

    # ── STK ──────────────────────────────────────────────────────────────
    stk_rows = (
        await session.execute(
            select(TechnicalInspection).where(TechnicalInspection.car_id == car.id)
        )
    ).scalars().all()
    stk = _latest_doc(list(stk_rows), key=lambda r: r.valid_until)
    if stk is not None:
        d = _days_left(stk.valid_until, today)
        chips.append(DashboardChip(label="STK", days_left=d))
        if d is not None and d < 0:
            flags["stk"] = True
            overdue_any = True

    # ── Insurance (PZP / KASKO) ──────────────────────────────────────────
    ins_rows = (
        await session.execute(
            select(InsurancePolicy).where(InsurancePolicy.car_id == car.id)
        )
    ).scalars().all()
    for ins_type in ("PZP", "KASKO"):
        rows = [r for r in ins_rows if r.type == ins_type]
        latest = _latest_doc(rows, key=lambda r: r.valid_until)
        if latest is not None:
            d = _days_left(latest.valid_until, today)
            chips.append(DashboardChip(label=ins_type, days_left=d))
            if d is not None and d < 0:
                flags["insurance"] = True
                overdue_any = True

    # ── Vignettes (per country, latest each) ────────────────────────────
    vig_rows = (
        await session.execute(select(Vignette).where(Vignette.car_id == car.id))
    ).scalars().all()
    by_country: dict[str, Vignette] = {}
    for v in vig_rows:
        cur = by_country.get(v.country)
        if cur is None or v.valid_until > cur.valid_until:
            by_country[v.country] = v
    for country, v in sorted(by_country.items()):
        d = _days_left(v.valid_until, today)
        chips.append(DashboardChip(label=country, days_left=d))
        if d is not None and d < 0:
            flags["vignette"] = True
            overdue_any = True

    # ── Next due service interval ────────────────────────────────────────
    interval_rows = (
        await session.execute(
            select(ServiceInterval).where(
                ServiceInterval.car_id == car.id,
                ServiceInterval.is_active.is_(True),
            )
        )
    ).scalars().all()
    next_service_name: str | None = None
    next_service_km_left: int | None = None
    next_service_days_left: int | None = None
    next_service_label: str | None = None
    best_urgency: float | None = None
    for iv in interval_rows:
        km_left = None
        if iv.interval_km is not None and iv.last_performed_km is not None:
            next_due_km = iv.last_performed_km + iv.interval_km
            km_left = next_due_km - car.current_odometer_km
        days_left_iv = None
        if iv.interval_months is not None and iv.last_performed_at is not None:
            next_due_date = _add_months(iv.last_performed_at, iv.interval_months)
            days_left_iv = (next_due_date - today).days

        # Urgency: smaller is more urgent; normalise km vs days roughly.
        candidates = []
        if km_left is not None:
            candidates.append(km_left / 50.0)  # ~50km/day heuristic
        if days_left_iv is not None:
            candidates.append(float(days_left_iv))
        if not candidates:
            continue
        urgency = min(candidates)
        if best_urgency is None or urgency < best_urgency:
            best_urgency = urgency
            next_service_name = iv.name
            next_service_km_left = km_left
            next_service_days_left = days_left_iv
            if km_left is not None and (days_left_iv is None or km_left / 50.0 <= days_left_iv):
                next_service_label = f"{iv.name}: {km_left} km"
            else:
                next_service_label = f"{iv.name}: {days_left_iv} d"

        if (km_left is not None and km_left < 0) or (
            days_left_iv is not None and days_left_iv < 0
        ):
            flags["service"] = True
            overdue_any = True

    # ── Active tire set summary ──────────────────────────────────────────
    active_set = (
        await session.execute(
            select(TireSet).where(
                TireSet.car_id == car.id, TireSet.is_active.is_(True)
            )
        )
    ).scalars().first()
    tires_label: str | None = None
    ats_id = ats_name = ats_season = None
    ats_avg = None
    ats_proj = None
    if active_set is not None:
        measurements = (
            await session.execute(
                select(TireMeasurement).where(
                    TireMeasurement.tire_set_id == active_set.id
                )
            )
        ).scalars().all()
        odo_readings = (
            await session.execute(
                select(OdometerReading).where(OdometerReading.car_id == car.id)
            )
        ).scalars().all()
        proj = projection_service.compute_projection(
            list(measurements),
            list(odo_readings),
            current_odometer_km=car.current_odometer_km,
            today=today,
        )
        ats_id = active_set.id
        ats_name = active_set.name
        ats_season = active_set.season
        ats_avg = proj.latest_avg_tread_mm
        ats_proj = proj.projection_date
        season_label = {
            "winter": "Zima",
            "summer": "Leto",
            "all_season": "Celoročné",
        }.get(active_set.season, active_set.season)
        if ats_avg is not None:
            tires_label = f"{season_label} · {ats_avg:.1f} mm"
        else:
            tires_label = season_label
        if ats_avg is not None and ats_avg < 1.6:
            flags["tires"] = True
            overdue_any = True

    # ── Rolling 30-day cost ──────────────────────────────────────────────
    monthly_cost = await _monthly_cost(session, car.id, today)

    return CarAggregate(
        id=car.id,
        name=car.name,
        license_plate=car.license_plate,
        current_odometer_km=car.current_odometer_km,
        chips=_sort_chips(chips),
        next_service_label=next_service_label,
        tires_label=tires_label,
        overdue=OverdueFlags(
            any=overdue_any,
            stk=flags["stk"],
            insurance=flags["insurance"],
            vignette=flags["vignette"],
            service=flags["service"],
            tires=flags["tires"],
        ),
        monthly_cost=monthly_cost,
        active_tire_set_id=ats_id,
        active_tire_set_name=ats_name,
        active_tire_set_season=ats_season,
        active_tire_set_avg_tread_mm=ats_avg,
        active_tire_set_projection_date=ats_proj,
        next_service_name=next_service_name,
        next_service_km_left=next_service_km_left,
        next_service_days_left=next_service_days_left,
    )


def _sort_chips(chips: list[DashboardChip]) -> list[DashboardChip]:
    """Sort chips by urgency: overdue/soonest first, ``None`` (gray) last."""

    def key(c: DashboardChip):
        if c.days_left is None:
            return (1, 0)
        return (0, c.days_left)

    return sorted(chips, key=key)


async def _monthly_cost(session: AsyncSession, car_id: int, today: date) -> float:
    """Sum of expenses in the trailing 30 days for a car."""
    since = today - timedelta(days=30)
    rows = (
        await session.execute(
            select(Expense.amount).where(
                Expense.car_id == car_id,
                Expense.occurred_at >= since,
            )
        )
    ).scalars().all()
    return round(sum(float(a) for a in rows if a is not None), 2)


def _add_months(d: date, months: int) -> date:
    """Add ``months`` calendar months to a date (clamping the day)."""
    month_index = d.month - 1 + months
    year = d.year + month_index // 12
    month = month_index % 12 + 1
    # Clamp the day to the last day of the target month.
    if month == 12:
        next_month_first = date(year + 1, 1, 1)
    else:
        next_month_first = date(year, month + 1, 1)
    last_day = (next_month_first - timedelta(days=1)).day
    return date(year, month, min(d.day, last_day))


async def build_dashboard(
    session: AsyncSession,
    cars: list[Car],
    *,
    today: date | None = None,
) -> tuple[DashboardStats, list[CarAggregate]]:
    """Aggregate every car + compute fleet-level stats."""
    today = today or date.today()
    aggregates = [await aggregate_car(session, c, today=today) for c in cars]

    # Sort cars: overdue first, then by minimum positive days_left chip.
    def urgency(agg: CarAggregate):
        day_vals = [c.days_left for c in agg.chips if c.days_left is not None]
        soonest = min(day_vals) if day_vals else 10**9
        return (0 if agg.overdue.any else 1, soonest)

    aggregates.sort(key=urgency)

    overdue_items = sum(1 for a in aggregates if a.overdue.any)
    monthly_cost = round(sum(a.monthly_cost for a in aggregates), 2)

    # Notifications sent today.
    notif_today = (
        await session.execute(
            select(NotificationLog.id).where(
                NotificationLog.sent_at >= _start_of_day(today),
                NotificationLog.status == "sent",
            )
        )
    ).scalars().all()

    stats = DashboardStats(
        cars=len(cars),
        notifications_today=len(notif_today),
        overdue_items=overdue_items,
        monthly_cost=monthly_cost,
    )
    return stats, aggregates


def _start_of_day(d: date):
    from datetime import datetime, time, timezone

    return datetime.combine(d, time.min, tzinfo=timezone.utc)
