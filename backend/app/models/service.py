"""Service record and service interval ORM models."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.car import Car


class ServiceRecord(Base):
    """A service / repair record, optionally with service-book detail.

    Flexible checklist fields (``performed_items`` / ``additional_work``) are
    stored as JSONB; their exact structure is defined in the API contract.
    Most fields are optional and apply only to certain ``category`` values.
    """

    __tablename__ = "service_records"

    id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True
    )
    car_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("cars.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    performed_at: Mapped[date] = mapped_column(Date, nullable=False)
    odometer_km: Mapped[int | None] = mapped_column(Integer, nullable=True)
    category: Mapped[str] = mapped_column(String(16), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    cost: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    shop: Mapped[str | None] = mapped_column(String(128), nullable=True)
    warranty_until: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Flexible service-book checklists (list of strings / objects).
    performed_items: Mapped[Any | None] = mapped_column(JSONB, nullable=True)
    additional_work: Mapped[Any | None] = mapped_column(JSONB, nullable=True)

    oil_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    next_oil_change_km: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )
    defect_found: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false", default=False
    )
    defect_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    tire_action: Mapped[str | None] = mapped_column(String(32), nullable=True)
    season: Mapped[str | None] = mapped_column(String(16), nullable=True)
    create_reminder: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false", default=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    car: Mapped[Car] = relationship(back_populates="service_records")


class ServiceInterval(Base):
    """A recurring service interval (by km and/or by months).

    Derived fields (``next_due_km``, ``next_due_date``, ``km_left``,
    ``days_left``) are computed at the API layer, not stored.
    """

    __tablename__ = "service_intervals"

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
    interval_km: Mapped[int | None] = mapped_column(Integer, nullable=True)
    interval_months: Mapped[int | None] = mapped_column(Integer, nullable=True)
    last_performed_km: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )
    last_performed_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="true", default=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    car: Mapped[Car] = relationship(back_populates="service_intervals")
