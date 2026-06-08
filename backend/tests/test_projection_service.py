"""Unit tests for the tire tread-wear projection (TECHNICAL_SPECIFICATION §7.1).

Pure logic — no database. ORM objects are constructed in memory and fed straight
to ``compute_projection`` / ``avg_km_per_day``.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from app.models.odometer import OdometerReading
from app.models.tire import TireMeasurement
from app.services.projection_service import (
    REFERENCE_TREAD_MM,
    avg_km_per_day,
    compute_projection,
)


def _measurement(
    *,
    odometer_km: int,
    tread: float,
    measured_at: date,
    pressure_after: float | None = None,
) -> TireMeasurement:
    """A measurement with all four wheels at the same tread (and optional pressure)."""
    return TireMeasurement(
        tire_set_id=1,
        measured_at=measured_at,
        odometer_km=odometer_km,
        tread_fl_mm=tread,
        tread_fr_mm=tread,
        tread_rl_mm=tread,
        tread_rr_mm=tread,
        pressure_fl_after_bar=pressure_after,
        pressure_fr_after_bar=pressure_after,
        pressure_rl_after_bar=pressure_after,
        pressure_rr_after_bar=pressure_after,
    )


def _reading(*, reading_km: int, recorded_at: datetime) -> OdometerReading:
    return OdometerReading(car_id=1, reading_km=reading_km, recorded_at=recorded_at)


# ── avg_km_per_day ──────────────────────────────────────────────────────────
def test_avg_km_per_day_basic() -> None:
    today = date(2024, 1, 31)
    readings = [
        _reading(reading_km=10_000, recorded_at=datetime(2024, 1, 1, tzinfo=timezone.utc)),
        _reading(reading_km=13_000, recorded_at=datetime(2024, 1, 31, tzinfo=timezone.utc)),
    ]
    # 3000 km over 30 days == 100 km/day.
    assert avg_km_per_day(readings, today=today) == 100.0


def test_avg_km_per_day_guards() -> None:
    one = [_reading(reading_km=10_000, recorded_at=datetime(2024, 1, 1, tzinfo=timezone.utc))]
    assert avg_km_per_day(one) is None  # < 2 readings

    same_day = [
        _reading(reading_km=10_000, recorded_at=datetime(2024, 1, 1, tzinfo=timezone.utc)),
        _reading(reading_km=10_500, recorded_at=datetime(2024, 1, 1, tzinfo=timezone.utc)),
    ]
    assert avg_km_per_day(same_day) is None  # zero day span


# ── compute_projection: happy path ──────────────────────────────────────────
def test_projection_projects_a_date_and_crosses_reference() -> None:
    """A clear decreasing trend yields a projection that reaches 1.6 mm + a date."""
    base = date(2024, 1, 1)
    # tread drops 1mm per 10_000 km: 8 -> 7 -> 6 -> 5 mm.
    measurements = [
        _measurement(odometer_km=100_000, tread=8.0, measured_at=base, pressure_after=2.3),
        _measurement(odometer_km=110_000, tread=7.0, measured_at=base + timedelta(days=60)),
        _measurement(odometer_km=120_000, tread=6.0, measured_at=base + timedelta(days=120)),
        _measurement(odometer_km=130_000, tread=5.0, measured_at=base + timedelta(days=180)),
    ]
    readings = [
        _reading(reading_km=100_000, recorded_at=datetime(2024, 1, 1, tzinfo=timezone.utc)),
        _reading(reading_km=130_000, recorded_at=datetime(2024, 6, 29, tzinfo=timezone.utc)),
    ]
    today = date(2024, 6, 29)

    result = compute_projection(
        measurements, readings, current_odometer_km=130_000, today=today
    )

    # Regression captured a negative slope.
    assert result.slope is not None and result.slope < 0
    assert result.reference_mm == REFERENCE_TREAD_MM

    # Actual points: one per measurement, in km order.
    assert [round(p.km) for p in result.points] == [100_000, 110_000, 120_000, 130_000]

    # Projection is a 2-point dashed line ending exactly on the 1.6 mm reference.
    assert len(result.projection) == 2
    assert result.projection[-1].projected == REFERENCE_TREAD_MM
    # The km-at-reference is beyond the last actual reading (still wearing down).
    assert result.km_at_reference is not None
    assert result.km_at_reference > 130_000
    # 5mm at 130k, slope -1mm/10k -> 1.6mm reached at ~164_000 km.
    assert abs(result.km_at_reference - 164_000) < 1_000

    # A calendar date was projected into the future.
    assert result.projection_date is not None
    assert result.projection_date > today

    # Latest avg tread + pressure surfaced from the most-recent data.
    assert result.latest_avg_tread_mm == 5.0
    assert result.avg_pressure_bar == 2.3
    assert result.mileage_km == 30_000


# ── compute_projection: guards ──────────────────────────────────────────────
def test_projection_requires_two_measurements() -> None:
    base = date(2024, 1, 1)
    result = compute_projection(
        [_measurement(odometer_km=100_000, tread=8.0, measured_at=base)],
        [],
    )
    assert result.projection == []
    assert result.projection_date is None
    # The single point is still echoed back for the chart.
    assert len(result.points) == 1


def test_projection_no_measurements_is_empty() -> None:
    result = compute_projection([], [])
    assert result.points == []
    assert result.projection == []
    assert result.slope is None


def test_projection_non_decreasing_trend_has_no_projection() -> None:
    """A flat / increasing trend (slope >= 0) cannot reach the 1.6 mm reference."""
    base = date(2024, 1, 1)
    flat = [
        _measurement(odometer_km=100_000, tread=6.0, measured_at=base),
        _measurement(odometer_km=110_000, tread=6.0, measured_at=base + timedelta(days=30)),
        _measurement(odometer_km=120_000, tread=6.0, measured_at=base + timedelta(days=60)),
    ]
    result = compute_projection(flat, [])
    assert result.slope is not None and result.slope >= 0
    assert result.projection == []
    assert result.projection_date is None

    increasing = [
        _measurement(odometer_km=100_000, tread=5.0, measured_at=base),
        _measurement(odometer_km=110_000, tread=6.0, measured_at=base + timedelta(days=30)),
    ]
    result2 = compute_projection(increasing, [])
    assert result2.slope is not None and result2.slope > 0
    assert result2.projection == []


def test_projection_same_odometer_is_degenerate() -> None:
    """All measurements at the same odometer give no usable slope."""
    base = date(2024, 1, 1)
    measurements = [
        _measurement(odometer_km=120_000, tread=7.0, measured_at=base),
        _measurement(odometer_km=120_000, tread=6.0, measured_at=base + timedelta(days=30)),
    ]
    result = compute_projection(measurements, [])
    assert result.projection == []
    assert result.slope is None
