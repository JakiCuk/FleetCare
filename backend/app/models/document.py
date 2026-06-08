"""Document ORM models: technical inspections (STK), insurance, vignettes."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    Date,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.car import Car


class TechnicalInspection(Base):
    """Technical inspection record (STK)."""

    __tablename__ = "technical_inspections"

    id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True
    )
    car_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("cars.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    inspected_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    valid_until: Mapped[date] = mapped_column(Date, nullable=False)
    cost: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    provider: Mapped[str | None] = mapped_column(String(128), nullable=True)
    note: Mapped[str | None] = mapped_column(String(255), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    car: Mapped[Car] = relationship(back_populates="technical_inspections")


class InsurancePolicy(Base):
    """Insurance policy (PZP / KASKO)."""

    __tablename__ = "insurance_policies"

    id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True
    )
    car_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("cars.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    type: Mapped[str] = mapped_column(String(8), nullable=False)
    provider: Mapped[str | None] = mapped_column(String(128), nullable=True)
    policy_number: Mapped[str | None] = mapped_column(String(64), nullable=True)
    valid_from: Mapped[date | None] = mapped_column(Date, nullable=True)
    valid_until: Mapped[date] = mapped_column(Date, nullable=False)
    cost: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    car: Mapped[Car] = relationship(back_populates="insurance_policies")


class Vignette(Base):
    """Highway vignette (per country)."""

    __tablename__ = "vignettes"

    id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True
    )
    car_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("cars.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    country: Mapped[str] = mapped_column(String(4), nullable=False)
    valid_from: Mapped[date | None] = mapped_column(Date, nullable=True)
    valid_until: Mapped[date] = mapped_column(Date, nullable=False)
    cost: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    provider: Mapped[str | None] = mapped_column(String(128), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    car: Mapped[Car] = relationship(back_populates="vignettes")
