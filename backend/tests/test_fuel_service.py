"""Unit tests for fuel consumption (l/100km) (TECHNICAL_SPECIFICATION §7.2).

Pure logic — ``FuelRecord`` ORM objects are built in memory. ``liters`` is given
as ``Decimal`` to match the model column type (the service accumulates Decimals).
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from app.models.fuel import FuelRecord
from app.services.fuel_service import compute_stats, consumption_map


def _record(
    *,
    rec_id: int,
    refueled_at: date,
    odometer_km: int,
    liters: str,
    full_tank: bool = True,
    total_cost: str | None = None,
    price_per_liter: str | None = None,
) -> FuelRecord:
    return FuelRecord(
        id=rec_id,
        car_id=1,
        refueled_at=refueled_at,
        odometer_km=odometer_km,
        liters=Decimal(liters),
        full_tank=full_tank,
        total_cost=Decimal(total_cost) if total_cost is not None else None,
        price_per_liter=Decimal(price_per_liter) if price_per_liter is not None else None,
    )


def test_consumption_only_between_consecutive_full_tanks() -> None:
    """l/100km = liters_N / (km_N - km_{N-1}) * 100, only on full-tank segments."""
    records = [
        _record(rec_id=1, refueled_at=date(2024, 1, 1), odometer_km=10_000, liters="40"),
        _record(rec_id=2, refueled_at=date(2024, 1, 11), odometer_km=10_500, liters="35"),
        _record(rec_id=3, refueled_at=date(2024, 1, 21), odometer_km=11_100, liters="42"),
    ]
    cmap = consumption_map(records)

    # First full tank seeds the baseline; it has no consumption value itself.
    assert 1 not in cmap
    # Record 2: 35 L over 500 km -> 7.0 l/100km.
    assert cmap[2] == round(35 / 500 * 100, 2)
    assert cmap[2] == 7.0
    # Record 3: 42 L over 600 km -> 7.0 l/100km.
    assert cmap[3] == round(42 / 600 * 100, 2)
    assert cmap[3] == 7.0


def test_partial_tank_rolls_into_next_full_segment() -> None:
    """A partial fill isn't a segment of its own; its litres join the next full tank."""
    records = [
        _record(rec_id=1, refueled_at=date(2024, 1, 1), odometer_km=10_000, liters="40"),
        # Partial fill mid-segment: 20 L, not full.
        _record(
            rec_id=2,
            refueled_at=date(2024, 1, 6),
            odometer_km=10_300,
            liters="20",
            full_tank=False,
        ),
        # Next full tank closes the segment from km 10_000.
        _record(rec_id=3, refueled_at=date(2024, 1, 11), odometer_km=10_800, liters="30"),
    ]
    cmap = consumption_map(records)

    # The partial fill gets no value of its own.
    assert 2 not in cmap
    assert 1 not in cmap
    # Segment distance is 800 km (10_800 - 10_000); litres = 20 (partial) + 30 (full) = 50.
    assert cmap[3] == round(50 / 800 * 100, 2)
    assert cmap[3] == 6.25


def test_compute_stats_aggregates() -> None:
    records = [
        _record(
            rec_id=1, refueled_at=date(2024, 1, 1), odometer_km=10_000,
            liters="40", total_cost="60.00",
        ),
        _record(
            rec_id=2, refueled_at=date(2024, 1, 11), odometer_km=10_500,
            liters="35", total_cost="52.50",
        ),
        _record(
            rec_id=3, refueled_at=date(2024, 2, 1), odometer_km=11_100,
            liters="42", total_cost="63.00",
        ),
    ]
    stats = compute_stats(records)

    # Only records 2 and 3 have consumption (both 7.0) -> average 7.0.
    assert stats["avg_consumption"] == 7.0
    assert stats["total_spent"] == 175.5
    assert stats["count"] == 3
    # Monthly buckets keyed by the closing record's month.
    months = {m["month"] for m in stats["monthly"]}
    assert months == {"2024-01", "2024-02"}


def test_compute_stats_without_full_pairs_has_no_avg() -> None:
    records = [
        _record(rec_id=1, refueled_at=date(2024, 1, 1), odometer_km=10_000, liters="40"),
    ]
    stats = compute_stats(records)
    assert stats["avg_consumption"] is None
    assert stats["count"] == 1
