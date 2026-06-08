"""Fuel record ORM model."""

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
    Integer,
    Numeric,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.car import Car


class FuelRecord(Base):
    """A single refuelling event.

    ``consumption_l_100km`` is computed at the API layer from consecutive
    ``full_tank=True`` records (see TECHNICAL_SPECIFICATION §7.2).
    """

    __tablename__ = "fuel_records"

    id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True
    )
    car_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("cars.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    refueled_at: Mapped[date] = mapped_column(Date, nullable=False)
    odometer_km: Mapped[int] = mapped_column(Integer, nullable=False)
    liters: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)
    price_per_liter: Mapped[Decimal | None] = mapped_column(
        Numeric(6, 3), nullable=True
    )
    total_cost: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2), nullable=True
    )
    full_tank: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="true", default=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    car: Mapped[Car] = relationship(back_populates="fuel_records")
