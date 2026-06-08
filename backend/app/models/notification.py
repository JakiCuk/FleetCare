"""Notification rule and notification log ORM models."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.car import Car


class NotificationRule(Base):
    """A per-car notification rule for a given item type.

    Derived ``status`` (active/overdue/smart/paused) is computed at the API
    layer from ``is_active`` / ``is_smart`` and the underlying item state.
    """

    __tablename__ = "notification_rules"

    id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True
    )
    car_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("cars.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # e.g. 'stk' | 'pzp' | 'kasko' | 'vignette' | 'tires' | 'service'
    # (optionally with country, e.g. 'vignette:AT')
    item_type: Mapped[str] = mapped_column(String(32), nullable=False)
    lead_days_1: Mapped[int | None] = mapped_column(
        Integer, nullable=True, server_default="30", default=30
    )
    lead_days_2: Mapped[int | None] = mapped_column(
        Integer, nullable=True, server_default="14", default=14
    )
    lead_days_3: Mapped[int | None] = mapped_column(
        Integer, nullable=True, server_default="7", default=7
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="true", default=True
    )
    is_smart: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false", default=False
    )
    channel_email: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="true", default=True
    )
    channel_matrix: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false", default=False
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

    car: Mapped[Car] = relationship(back_populates="notification_rules")
    # Logs reference the rule via ON DELETE SET NULL — deleting a rule must NOT
    # delete its log entries, so no cascade/delete-orphan here.
    logs: Mapped[list[NotificationLog]] = relationship(
        back_populates="rule",
        passive_deletes=True,
    )


class NotificationLog(Base):
    """A record of an attempted/sent notification (for audit + dedup)."""

    __tablename__ = "notification_log"
    __table_args__ = (
        # Supports the 23h dedup lookup keyed on
        # (car_id, rule_id, item_type, lead_bucket, channel) ordered by sent_at.
        Index(
            "ix_notification_log_dedup",
            "car_id",
            "rule_id",
            "item_type",
            "lead_bucket",
            "channel",
            "sent_at",
        ),
    )

    id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True
    )
    car_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("cars.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    rule_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("notification_rules.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    item_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    # which lead bucket (1/2/3) or 0 for smart/overdue
    lead_bucket: Mapped[int | None] = mapped_column(Integer, nullable=True)
    channel: Mapped[str] = mapped_column(String(16), nullable=False)
    recipient: Mapped[str | None] = mapped_column(String(255), nullable=True)
    subject: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    sent_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    car: Mapped[Car] = relationship(back_populates="notification_logs")
    rule: Mapped[NotificationRule | None] = relationship(back_populates="logs")
