"""Tire set and per-wheel measurement ORM models."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.car import Car


class TireSet(Base):
    """A mounted set of tires for a car (max one active set per car)."""

    __tablename__ = "tire_sets"

    id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True
    )
    car_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("cars.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    season: Mapped[str] = mapped_column(String(16), nullable=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="true", default=True
    )
    mounted_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    mounted_odometer_km: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )
    expected_change_date: Mapped[date | None] = mapped_column(
        Date, nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    car: Mapped[Car] = relationship(back_populates="tire_sets")
    measurements: Mapped[list[TireMeasurement]] = relationship(
        back_populates="tire_set",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class TireMeasurement(Base):
    """A tread + pressure (before/after inflation) measurement for a tire set.

    ``avg_tread = (fl + fr + rl + rr) / 4`` is computed at the API layer.
    """

    __tablename__ = "tire_measurements"
    __table_args__ = (
        Index("ix_tire_measurements_set_measured", "tire_set_id", "measured_at"),
    )

    id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True
    )
    tire_set_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("tire_sets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    measured_at: Mapped[date] = mapped_column(Date, nullable=False)
    odometer_km: Mapped[int] = mapped_column(Integer, nullable=False)

    # --- per-wheel tread depth (mm) ---
    tread_fl_mm: Mapped[Decimal | None] = mapped_column(
        Numeric(4, 2), nullable=True
    )
    tread_fr_mm: Mapped[Decimal | None] = mapped_column(
        Numeric(4, 2), nullable=True
    )
    tread_rl_mm: Mapped[Decimal | None] = mapped_column(
        Numeric(4, 2), nullable=True
    )
    tread_rr_mm: Mapped[Decimal | None] = mapped_column(
        Numeric(4, 2), nullable=True
    )

    # --- per-wheel pressure before inflation (bar, optional) ---
    pressure_fl_before_bar: Mapped[Decimal | None] = mapped_column(
        Numeric(4, 2), nullable=True
    )
    pressure_fr_before_bar: Mapped[Decimal | None] = mapped_column(
        Numeric(4, 2), nullable=True
    )
    pressure_rl_before_bar: Mapped[Decimal | None] = mapped_column(
        Numeric(4, 2), nullable=True
    )
    pressure_rr_before_bar: Mapped[Decimal | None] = mapped_column(
        Numeric(4, 2), nullable=True
    )

    # --- per-wheel pressure after inflation (bar, optional) ---
    pressure_fl_after_bar: Mapped[Decimal | None] = mapped_column(
        Numeric(4, 2), nullable=True
    )
    pressure_fr_after_bar: Mapped[Decimal | None] = mapped_column(
        Numeric(4, 2), nullable=True
    )
    pressure_rl_after_bar: Mapped[Decimal | None] = mapped_column(
        Numeric(4, 2), nullable=True
    )
    pressure_rr_after_bar: Mapped[Decimal | None] = mapped_column(
        Numeric(4, 2), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    tire_set: Mapped[TireSet] = relationship(back_populates="measurements")
