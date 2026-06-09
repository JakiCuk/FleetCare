"""Fuel consumption (l/100km) computation (TECHNICAL_SPECIFICATION §7.2).

Consumption is computed only across *consecutive* ``full_tank=True`` records:

    l/100km = liters_in_segment / (km_N - km_{N-1}) * 100

Partial fills are not counted on their own; their litres are rolled into the
following full-tank segment.
"""

from __future__ import annotations

from collections import defaultdict
from decimal import Decimal

from app.models.fuel import FuelRecord


def _total_cost(r: FuelRecord) -> float:
    """Resolved cost of a record (explicit total, else liters*price)."""
    if r.total_cost is not None:
        return float(r.total_cost)
    if r.price_per_liter is not None and r.liters is not None:
        return float(r.liters) * float(r.price_per_liter)
    return 0.0


def consumption_map(records: list[FuelRecord]) -> dict[int, float]:
    """Map of ``FuelRecord.id`` → consumption (l/100km) for full-tank records.

    Only records that close a segment between two full tanks get a value;
    others (the first full tank, partial fills) are absent from the map.
    """
    ordered = sorted(records, key=lambda r: (r.refueled_at, r.odometer_km, r.id))
    out: dict[int, float] = {}

    prev_full_km: int | None = None
    pending_liters = Decimal("0")

    for r in ordered:
        pending_liters += r.liters if r.liters is not None else Decimal("0")
        if not r.full_tank:
            # Partial fill: accumulate litres, carry forward.
            continue
        if prev_full_km is not None:
            dist = r.odometer_km - prev_full_km
            if dist > 0:
                out[r.id] = round(float(pending_liters) / dist * 100.0, 2)
        prev_full_km = r.odometer_km
        pending_liters = Decimal("0")

    return out


def compute_stats(records: list[FuelRecord], *, group_by: str = "month") -> dict:
    """Aggregate fuel statistics (avg consumption, total spent, trend).

    ``group_by`` controls the trend bucketing: ``"month"`` (``YYYY-MM``) or
    ``"year"`` (``YYYY``). The bucket label is returned under the ``month`` key
    of each point for backward compatibility with the existing schema.
    """
    cmap = consumption_map(records)

    consumptions = list(cmap.values())
    avg_consumption = (
        round(sum(consumptions) / len(consumptions), 2) if consumptions else None
    )
    total_spent = round(sum(_total_cost(r) for r in records), 2)
    count = len(records)

    fmt = "%Y" if group_by == "year" else "%Y-%m"
    # Average consumption per bucket, keyed by the record that closes a segment.
    by_bucket: dict[str, list[float]] = defaultdict(list)
    for r in records:
        if r.id in cmap:
            by_bucket[r.refueled_at.strftime(fmt)].append(cmap[r.id])

    monthly = [
        {
            "month": bucket,
            "consumption": round(sum(vals) / len(vals), 2) if vals else None,
        }
        for bucket, vals in sorted(by_bucket.items())
    ]

    return {
        "avg_consumption": avg_consumption,
        "total_spent": total_spent,
        "count": count,
        "monthly": monthly,
    }
