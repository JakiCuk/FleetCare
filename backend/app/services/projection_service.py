"""Tire tread-wear projection (TECHNICAL_SPECIFICATION §7.1).

Linear regression over (odometer_km, avg_tread_mm) for the measurements of a
tire set, extrapolated down to the 1.6 mm legal reference, then converted to a
calendar date using the car's average daily mileage from odometer readings.

Guards:
    - < 2 measurements                       → no projection
    - non-decreasing trend (slope >= 0)      → no projection
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta

import numpy as np

from app.models.odometer import OdometerReading
from app.models.tire import TireMeasurement

REFERENCE_TREAD_MM = 1.6


def _avg_tread(m: TireMeasurement) -> float | None:
    """Average of the four per-wheel tread depths (None if all missing)."""
    vals = [
        m.tread_fl_mm,
        m.tread_fr_mm,
        m.tread_rl_mm,
        m.tread_rr_mm,
    ]
    present = [float(v) for v in vals if v is not None]
    if not present:
        return None
    return sum(present) / len(present)


def _avg_pressure(m: TireMeasurement) -> float | None:
    """Average of available 'after' pressures, else 'before' pressures."""
    after = [
        m.pressure_fl_after_bar,
        m.pressure_fr_after_bar,
        m.pressure_rl_after_bar,
        m.pressure_rr_after_bar,
    ]
    before = [
        m.pressure_fl_before_bar,
        m.pressure_fr_before_bar,
        m.pressure_rl_before_bar,
        m.pressure_rr_before_bar,
    ]
    for group in (after, before):
        present = [float(v) for v in group if v is not None]
        if present:
            return sum(present) / len(present)
    return None


@dataclass(slots=True)
class TrendPointData:
    km: float
    actual: float


@dataclass(slots=True)
class ProjectionPointData:
    km: float
    projected: float


@dataclass(slots=True)
class ProjectionResult:
    """Outcome of a projection computation for one tire set."""

    points: list[TrendPointData] = field(default_factory=list)
    projection: list[ProjectionPointData] = field(default_factory=list)
    reference_mm: float = REFERENCE_TREAD_MM
    projection_date: date | None = None
    km_at_reference: float | None = None
    slope: float | None = None
    intercept: float | None = None
    latest_avg_tread_mm: float | None = None
    mileage_km: int | None = None
    avg_pressure_bar: float | None = None


def avg_km_per_day(
    readings: list[OdometerReading],
    *,
    today: date | None = None,
) -> float | None:
    """Average daily kilometres from odometer readings.

    Uses (max_km - min_km) / (days between earliest and latest reading).
    Returns ``None`` when it cannot be computed (< 2 readings / zero span).
    """
    if len(readings) < 2:
        return None
    pairs = [
        (r.recorded_at.date() if hasattr(r.recorded_at, "date") else r.recorded_at, r.reading_km)
        for r in readings
    ]
    pairs.sort(key=lambda p: p[0])
    first_day, first_km = pairs[0]
    last_day, last_km = pairs[-1]
    span_days = (last_day - first_day).days
    if span_days <= 0:
        return None
    delta_km = last_km - first_km
    if delta_km <= 0:
        return None
    return delta_km / span_days


def compute_projection(
    measurements: list[TireMeasurement],
    odometer_readings: list[OdometerReading],
    *,
    current_odometer_km: int | None = None,
    today: date | None = None,
    reference_mm: float = REFERENCE_TREAD_MM,
) -> ProjectionResult:
    """Compute the tread projection for a tire set.

    Returns a :class:`ProjectionResult`. The ``projection`` list is empty when
    there are < 2 usable measurements or the regression slope is non-negative.
    """
    today = today or date.today()
    result = ProjectionResult(reference_mm=reference_mm)

    usable: list[tuple[int, float]] = []
    for m in sorted(measurements, key=lambda x: (x.odometer_km, x.measured_at)):
        avg = _avg_tread(m)
        if avg is not None:
            usable.append((m.odometer_km, avg))

    if usable:
        # Latest-by-mileage avg tread + mileage span + pressure.
        result.latest_avg_tread_mm = usable[-1][1]
        kms = [k for k, _ in usable]
        result.mileage_km = max(kms) - min(kms) if len(kms) > 1 else 0
        # Average pressure from the most-recent measurement that has any.
        for m in sorted(measurements, key=lambda x: x.measured_at, reverse=True):
            p = _avg_pressure(m)
            if p is not None:
                result.avg_pressure_bar = p
                break

    result.points = [TrendPointData(km=float(k), actual=float(v)) for k, v in usable]

    if len(usable) < 2:
        return result

    xs = np.array([k for k, _ in usable], dtype=float)
    ys = np.array([v for _, v in usable], dtype=float)

    # Degenerate input: all measurements at the same odometer → no usable slope.
    if float(xs.max()) == float(xs.min()):
        return result

    slope, intercept = np.polyfit(xs, ys, 1)
    result.slope = float(slope)
    result.intercept = float(intercept)

    # Non-decreasing trend / invalid slope → cannot extrapolate to the reference.
    if not np.isfinite(slope) or not np.isfinite(intercept) or slope >= 0:
        result.slope = float(slope) if np.isfinite(slope) else None
        result.intercept = float(intercept) if np.isfinite(intercept) else None
        return result

    km_at_ref = (reference_mm - intercept) / slope
    result.km_at_reference = float(km_at_ref)

    last_km = float(xs.max())
    if km_at_ref <= last_km:
        # Already at/below the reference per the model → project flat to "now".
        km_at_ref = last_km
        result.km_at_reference = float(km_at_ref)

    # Dashed projection line: from last actual point down to the reference.
    result.projection = [
        ProjectionPointData(km=last_km, projected=float(slope * last_km + intercept)),
        ProjectionPointData(km=float(km_at_ref), projected=reference_mm),
    ]

    # Convert km-at-reference to a calendar date via avg daily km.
    daily = avg_km_per_day(odometer_readings, today=today)
    ref_odo = current_odometer_km
    if ref_odo is None and odometer_readings:
        ref_odo = max(r.reading_km for r in odometer_readings)
    if ref_odo is None:
        ref_odo = int(last_km)

    if daily and daily > 0:
        km_remaining = km_at_ref - ref_odo
        days_remaining = km_remaining / daily
        # Clamp to a sane range to avoid overflow on near-flat slopes.
        days_remaining = max(-3650.0, min(days_remaining, 36500.0))
        result.projection_date = today + timedelta(days=round(days_remaining))

    return result
