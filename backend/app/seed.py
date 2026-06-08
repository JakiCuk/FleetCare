"""Idempotent database seeding for FleetCare.

Run after migrations (``alembic upgrade head``) to ensure the database has:

* an **admin** user (from ``ADMIN_USERNAME`` / ``ADMIN_PASSWORD`` / ``ADMIN_EMAIL``),
* default ``app_settings`` rows (lead days 30/14/7, daily send time 08:00,
  tire min tread 2.5 mm, fleet name, timezone, locale, currency),
* optionally a small set of **demo** cars + records when ``SEED_DEMO`` is truthy.

Every step checks for existing rows first, so running ``seed()`` repeatedly is
safe. Invoke directly with ``python -m app.seed`` (or ``python app/seed.py``).

This module is import-safe: importing it does not touch the database or require
any env var to be set; all work happens inside :func:`seed`.
"""

from __future__ import annotations

import asyncio
import os
from datetime import date, datetime, timedelta, timezone

from passlib.context import CryptContext
from sqlalchemy import select

from app.database import async_session_maker
from app.models import (
    AppSetting,
    Car,
    FuelRecord,
    InsurancePolicy,
    NotificationRule,
    OdometerReading,
    ServiceInterval,
    TechnicalInspection,
    TireMeasurement,
    TireSet,
    User,
    Vignette,
)

# Same scheme the backend uses for password verification (argon2).
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

# Values that some test harnesses treat as "true".
_TRUTHY = {"1", "true", "t", "yes", "y", "on"}


def _is_truthy(value: str | None) -> bool:
    return (value or "").strip().lower() in _TRUTHY


# Default app_settings (key -> value). Secrets are intentionally NOT seeded;
# they come from env/admin panel at runtime.
def _default_settings() -> dict[str, str]:
    return {
        "fleet_name": "FleetCare",
        "timezone": os.environ.get("TZ", "Europe/Bratislava"),
        "default_locale": os.environ.get("DEFAULT_LOCALE", "sk"),
        "currency": "eur",
        "default_lead_days_1": "30",
        "default_lead_days_2": "14",
        "default_lead_days_3": "7",
        "daily_send_time": "08:00",
        "tire_min_tread_mm": "2.5",
    }


async def _seed_admin(session) -> None:
    """Create the admin user from env if no user with that username exists."""
    username = os.environ.get("ADMIN_USERNAME", "admin")
    password = os.environ.get("ADMIN_PASSWORD", "changeme")
    email = os.environ.get("ADMIN_EMAIL", "admin@fleetcare.local")

    existing = await session.scalar(
        select(User).where(User.username == username)
    )
    if existing is not None:
        return

    admin = User(
        username=username,
        email=email,
        full_name="Administrator",
        hashed_password=pwd_context.hash(password),
        is_admin=True,
        is_active=True,
        locale=os.environ.get("DEFAULT_LOCALE", "sk"),
    )
    session.add(admin)


async def _seed_settings(session) -> None:
    """Insert any missing default app_settings rows."""
    existing_keys = set(
        (await session.scalars(select(AppSetting.key))).all()
    )
    for key, value in _default_settings().items():
        if key not in existing_keys:
            session.add(AppSetting(key=key, value=value))


def _default_rules(item_types: list[str]) -> list[NotificationRule]:
    """Build default 30/14/7 email notification rules for the given items."""
    return [
        NotificationRule(
            item_type=item_type,
            lead_days_1=30,
            lead_days_2=14,
            lead_days_3=7,
            is_active=True,
            is_smart=item_type in {"tires", "service"},
            channel_email=True,
            channel_matrix=False,
        )
        for item_type in item_types
    ]


async def _seed_demo(session) -> None:
    """Insert a small demo fleet (only if no cars exist yet)."""
    existing_car = await session.scalar(select(Car.id).limit(1))
    if existing_car is not None:
        return

    today = date.today()
    now = datetime.now(timezone.utc)

    # (name, make, model, year, plate, vin, odometer, tire season, tread mm,
    #  stk valid_until offset days, vignette country/offset, has_kasko)
    demo = [
        ("Škoda Octavia", "Škoda", "Octavia", 2019, "BA123AB",
         "TMBJJ7NE0K0000001", 127540, "winter", 4.2, 12, "SK", 4, True),
        ("VW Passat", "Volkswagen", "Passat", 2018, "BL456CD",
         "WVWZZZ3CZJE000002", 98230, "summer", 6.8, 187, "AT", 95, True),
        ("Ford Focus", "Ford", "Focus", 2020, "BB789EF",
         "WF0DXXGCHDJ000003", 54310, "all_season", 5.1, 60, "CZ", 30, False),
        ("Toyota Yaris", "Toyota", "Yaris", 2021, "NR012GH",
         "VNKKL3D3X0A000004", 31200, "summer", 7.4, 240, "SK", 200, False),
        ("Dacia Duster", "Dacia", "Duster", 2017, "ZA345IJ",
         "UU1HSDCVG56000005", 142880, "winter", 3.3, -5, "HU", 15, True),
        ("BMW 320d", "BMW", "320d", 2016, "KE678KL",
         "WBA8E11070K000006", 178540, "summer", 5.9, 95, "AT", 60, True),
    ]

    for (
        name, make, model, year, plate, vin, odo, season, tread,
        stk_off, vign_country, vign_off, has_kasko,
    ) in demo:
        car = Car(
            name=name,
            make=make,
            model=model,
            year=year,
            license_plate=plate,
            vin=vin,
            current_odometer_km=odo,
        )

        # Odometer history (a couple of readings).
        car.odometer_readings.append(
            OdometerReading(
                reading_km=max(0, odo - 1500),
                recorded_at=now - timedelta(days=30),
                note="seed",
            )
        )
        car.odometer_readings.append(
            OdometerReading(reading_km=odo, recorded_at=now, note="seed")
        )

        # STK.
        car.technical_inspections.append(
            TechnicalInspection(
                inspected_at=today + timedelta(days=stk_off - 730),
                valid_until=today + timedelta(days=stk_off),
                cost=45.00,
                provider="STK Bratislava",
            )
        )

        # Insurance: PZP always, KASKO for some.
        car.insurance_policies.append(
            InsurancePolicy(
                type="PZP",
                provider="Allianz",
                policy_number=f"PZP-{plate}",
                valid_from=today - timedelta(days=200),
                valid_until=today + timedelta(days=165),
                cost=320.00,
            )
        )
        if has_kasko:
            car.insurance_policies.append(
                InsurancePolicy(
                    type="KASKO",
                    provider="Generali",
                    policy_number=f"KASKO-{plate}",
                    valid_from=today - timedelta(days=200),
                    valid_until=today + timedelta(days=165),
                    cost=540.00,
                )
            )

        # Vignette.
        car.vignettes.append(
            Vignette(
                country=vign_country,
                valid_from=today - timedelta(days=365 - vign_off),
                valid_until=today + timedelta(days=vign_off),
                cost=60.00,
                provider="eznamka",
            )
        )

        # Active tire set with a few descending tread measurements.
        tire_set = TireSet(
            name="Nokian"
            if season == "winter"
            else ("Michelin" if season == "summer" else "Goodyear"),
            season=season,
            is_active=True,
            mounted_at=today - timedelta(days=300),
            mounted_odometer_km=max(0, odo - 12000),
            expected_change_date=today + timedelta(days=400),
        )
        # 3 measurements with a downward trend, ending near `tread`.
        for i, (km_back, days_back) in enumerate(
            [(8000, 180), (4000, 90), (0, 0)]
        ):
            depth = round(tread + (8000 - km_back) / 8000 * 2.0 + 0.5 - i * 0.5, 2)
            tire_set.measurements.append(
                TireMeasurement(
                    measured_at=today - timedelta(days=days_back),
                    odometer_km=max(0, odo - km_back),
                    tread_fl_mm=depth,
                    tread_fr_mm=depth,
                    tread_rl_mm=round(depth + 0.2, 2),
                    tread_rr_mm=round(depth + 0.2, 2),
                    pressure_fl_before_bar=2.1,
                    pressure_fr_before_bar=2.1,
                    pressure_rl_before_bar=2.0,
                    pressure_rr_before_bar=2.0,
                    pressure_fl_after_bar=2.4,
                    pressure_fr_after_bar=2.4,
                    pressure_rl_after_bar=2.3,
                    pressure_rr_after_bar=2.3,
                )
            )
        car.tire_sets.append(tire_set)

        # A simple oil-change service interval.
        car.service_intervals.append(
            ServiceInterval(
                name="Výmena oleja",
                interval_km=15000,
                interval_months=12,
                last_performed_km=max(0, odo - 8000),
                last_performed_at=today - timedelta(days=180),
                is_active=True,
            )
        )

        # A couple of fuel records (two full tanks for consumption calc).
        car.fuel_records.append(
            FuelRecord(
                refueled_at=today - timedelta(days=20),
                odometer_km=max(0, odo - 600),
                liters=48.50,
                price_per_liter=1.659,
                total_cost=80.46,
                full_tank=True,
            )
        )
        car.fuel_records.append(
            FuelRecord(
                refueled_at=today - timedelta(days=5),
                odometer_km=odo,
                liters=41.20,
                price_per_liter=1.679,
                total_cost=69.17,
                full_tank=True,
            )
        )

        # Default notification rules (STK, PZP, optional KASKO, vignette).
        item_types = ["stk", "pzp"]
        if has_kasko:
            item_types.append("kasko")
        item_types.append(f"vignette:{vign_country}")
        item_types.extend(["tires", "service"])
        car.notification_rules.extend(_default_rules(item_types))

        session.add(car)


async def seed() -> None:
    """Idempotently seed the database (admin + settings + optional demo)."""
    async with async_session_maker() as session:
        await _seed_admin(session)
        await _seed_settings(session)
        if _is_truthy(os.environ.get("SEED_DEMO")):
            await _seed_demo(session)
        await session.commit()


if __name__ == "__main__":
    asyncio.run(seed())
