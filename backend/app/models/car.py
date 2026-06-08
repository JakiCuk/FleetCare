"""Car and user<->car assignment ORM models."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.document import (
        InsurancePolicy,
        TechnicalInspection,
        Vignette,
    )
    from app.models.expense import Expense
    from app.models.fuel import FuelRecord
    from app.models.notification import NotificationLog, NotificationRule
    from app.models.odometer import OdometerReading
    from app.models.service import ServiceInterval, ServiceRecord
    from app.models.tire import TireSet
    from app.models.user import User


class Car(Base):
    """A vehicle in the fleet."""

    __tablename__ = "cars"

    id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    make: Mapped[str | None] = mapped_column(String(64), nullable=True)
    model: Mapped[str | None] = mapped_column(String(64), nullable=True)
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    license_plate: Mapped[str] = mapped_column(String(16), nullable=False)
    vin: Mapped[str | None] = mapped_column(String(32), nullable=True)
    current_odometer_km: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0", default=0
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # --- relationships (all children cascade-delete with the car) ---
    car_groups: Mapped[list[UserCarGroup]] = relationship(
        back_populates="car",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    odometer_readings: Mapped[list[OdometerReading]] = relationship(
        back_populates="car",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    tire_sets: Mapped[list[TireSet]] = relationship(
        back_populates="car",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    technical_inspections: Mapped[list[TechnicalInspection]] = relationship(
        back_populates="car",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    insurance_policies: Mapped[list[InsurancePolicy]] = relationship(
        back_populates="car",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    vignettes: Mapped[list[Vignette]] = relationship(
        back_populates="car",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    service_records: Mapped[list[ServiceRecord]] = relationship(
        back_populates="car",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    service_intervals: Mapped[list[ServiceInterval]] = relationship(
        back_populates="car",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    fuel_records: Mapped[list[FuelRecord]] = relationship(
        back_populates="car",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    expenses: Mapped[list[Expense]] = relationship(
        back_populates="car",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    notification_rules: Mapped[list[NotificationRule]] = relationship(
        back_populates="car",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    notification_logs: Mapped[list[NotificationLog]] = relationship(
        back_populates="car",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class UserCarGroup(Base):
    """Assignment of a car to a user (with per-assignment notification toggle)."""

    __tablename__ = "user_car_groups"
    __table_args__ = (
        UniqueConstraint("user_id", "car_id", name="uq_user_car_groups_user_car"),
    )

    id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    car_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("cars.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    notification_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="true", default=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    user: Mapped[User] = relationship(back_populates="car_groups")
    car: Mapped[Car] = relationship(back_populates="car_groups")
