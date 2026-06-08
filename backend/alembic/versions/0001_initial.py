"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-06-08 00:00:00.000000

Creates the complete FleetCare schema: users, cars and all car-dependent
tables (odometer, tires, documents, service, fuel, expenses, notifications)
plus app_settings. Consistent with the SQLAlchemy 2.0 ORM models in
``app/models``.
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ── users ───────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("username", sa.String(length=64), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=128), nullable=True),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column(
            "is_admin",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=False,
        ),
        sa.Column(
            "locale",
            sa.String(length=5),
            server_default=sa.text("'sk'"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_users_username", "users", ["username"], unique=True
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    # ── cars ────────────────────────────────────────────────────────────
    op.create_table(
        "cars",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("make", sa.String(length=64), nullable=True),
        sa.Column("model", sa.String(length=64), nullable=True),
        sa.Column("year", sa.Integer(), nullable=True),
        sa.Column("license_plate", sa.String(length=16), nullable=False),
        sa.Column("vin", sa.String(length=32), nullable=True),
        sa.Column(
            "current_odometer_km",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # ── user_car_groups ─────────────────────────────────────────────────
    op.create_table(
        "user_car_groups",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("car_id", sa.BigInteger(), nullable=False),
        sa.Column(
            "notification_enabled",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["car_id"], ["cars.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id", "car_id", name="uq_user_car_groups_user_car"
        ),
    )
    op.create_index(
        "ix_user_car_groups_user_id", "user_car_groups", ["user_id"]
    )
    op.create_index(
        "ix_user_car_groups_car_id", "user_car_groups", ["car_id"]
    )

    # ── odometer_readings ───────────────────────────────────────────────
    op.create_table(
        "odometer_readings",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("car_id", sa.BigInteger(), nullable=False),
        sa.Column("reading_km", sa.Integer(), nullable=False),
        sa.Column(
            "recorded_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("note", sa.String(length=255), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["car_id"], ["cars.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_odometer_readings_car_id", "odometer_readings", ["car_id"]
    )
    op.create_index(
        "ix_odometer_readings_car_recorded",
        "odometer_readings",
        ["car_id", "recorded_at"],
    )

    # ── tire_sets ───────────────────────────────────────────────────────
    op.create_table(
        "tire_sets",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("car_id", sa.BigInteger(), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("season", sa.String(length=16), nullable=False),
        sa.Column(
            "is_active",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=False,
        ),
        sa.Column("mounted_at", sa.Date(), nullable=True),
        sa.Column("mounted_odometer_km", sa.Integer(), nullable=True),
        sa.Column("expected_change_date", sa.Date(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["car_id"], ["cars.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_tire_sets_car_id", "tire_sets", ["car_id"])

    # ── tire_measurements ───────────────────────────────────────────────
    op.create_table(
        "tire_measurements",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("tire_set_id", sa.BigInteger(), nullable=False),
        sa.Column("measured_at", sa.Date(), nullable=False),
        sa.Column("odometer_km", sa.Integer(), nullable=False),
        sa.Column("tread_fl_mm", sa.Numeric(precision=4, scale=2), nullable=True),
        sa.Column("tread_fr_mm", sa.Numeric(precision=4, scale=2), nullable=True),
        sa.Column("tread_rl_mm", sa.Numeric(precision=4, scale=2), nullable=True),
        sa.Column("tread_rr_mm", sa.Numeric(precision=4, scale=2), nullable=True),
        sa.Column(
            "pressure_fl_before_bar",
            sa.Numeric(precision=4, scale=2),
            nullable=True,
        ),
        sa.Column(
            "pressure_fr_before_bar",
            sa.Numeric(precision=4, scale=2),
            nullable=True,
        ),
        sa.Column(
            "pressure_rl_before_bar",
            sa.Numeric(precision=4, scale=2),
            nullable=True,
        ),
        sa.Column(
            "pressure_rr_before_bar",
            sa.Numeric(precision=4, scale=2),
            nullable=True,
        ),
        sa.Column(
            "pressure_fl_after_bar",
            sa.Numeric(precision=4, scale=2),
            nullable=True,
        ),
        sa.Column(
            "pressure_fr_after_bar",
            sa.Numeric(precision=4, scale=2),
            nullable=True,
        ),
        sa.Column(
            "pressure_rl_after_bar",
            sa.Numeric(precision=4, scale=2),
            nullable=True,
        ),
        sa.Column(
            "pressure_rr_after_bar",
            sa.Numeric(precision=4, scale=2),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["tire_set_id"], ["tire_sets.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_tire_measurements_tire_set_id",
        "tire_measurements",
        ["tire_set_id"],
    )
    op.create_index(
        "ix_tire_measurements_set_measured",
        "tire_measurements",
        ["tire_set_id", "measured_at"],
    )

    # ── technical_inspections (STK) ─────────────────────────────────────
    op.create_table(
        "technical_inspections",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("car_id", sa.BigInteger(), nullable=False),
        sa.Column("inspected_at", sa.Date(), nullable=True),
        sa.Column("valid_until", sa.Date(), nullable=False),
        sa.Column("cost", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("provider", sa.String(length=128), nullable=True),
        sa.Column("note", sa.String(length=255), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["car_id"], ["cars.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_technical_inspections_car_id",
        "technical_inspections",
        ["car_id"],
    )

    # ── insurance_policies ──────────────────────────────────────────────
    op.create_table(
        "insurance_policies",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("car_id", sa.BigInteger(), nullable=False),
        sa.Column("type", sa.String(length=8), nullable=False),
        sa.Column("provider", sa.String(length=128), nullable=True),
        sa.Column("policy_number", sa.String(length=64), nullable=True),
        sa.Column("valid_from", sa.Date(), nullable=True),
        sa.Column("valid_until", sa.Date(), nullable=False),
        sa.Column("cost", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["car_id"], ["cars.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_insurance_policies_car_id", "insurance_policies", ["car_id"]
    )

    # ── vignettes ───────────────────────────────────────────────────────
    op.create_table(
        "vignettes",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("car_id", sa.BigInteger(), nullable=False),
        sa.Column("country", sa.String(length=4), nullable=False),
        sa.Column("valid_from", sa.Date(), nullable=True),
        sa.Column("valid_until", sa.Date(), nullable=False),
        sa.Column("cost", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("provider", sa.String(length=128), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["car_id"], ["cars.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_vignettes_car_id", "vignettes", ["car_id"])

    # ── service_records ─────────────────────────────────────────────────
    op.create_table(
        "service_records",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("car_id", sa.BigInteger(), nullable=False),
        sa.Column("performed_at", sa.Date(), nullable=False),
        sa.Column("odometer_km", sa.Integer(), nullable=True),
        sa.Column("category", sa.String(length=16), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("cost", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("shop", sa.String(length=128), nullable=True),
        sa.Column("warranty_until", sa.Date(), nullable=True),
        sa.Column(
            "performed_items",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column(
            "additional_work",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column("oil_name", sa.String(length=128), nullable=True),
        sa.Column("next_oil_change_km", sa.Integer(), nullable=True),
        sa.Column(
            "defect_found",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column("defect_description", sa.Text(), nullable=True),
        sa.Column("tire_action", sa.String(length=32), nullable=True),
        sa.Column("season", sa.String(length=16), nullable=True),
        sa.Column(
            "create_reminder",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["car_id"], ["cars.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_service_records_car_id", "service_records", ["car_id"]
    )

    # ── service_intervals ───────────────────────────────────────────────
    op.create_table(
        "service_intervals",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("car_id", sa.BigInteger(), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("interval_km", sa.Integer(), nullable=True),
        sa.Column("interval_months", sa.Integer(), nullable=True),
        sa.Column("last_performed_km", sa.Integer(), nullable=True),
        sa.Column("last_performed_at", sa.Date(), nullable=True),
        sa.Column(
            "is_active",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["car_id"], ["cars.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_service_intervals_car_id", "service_intervals", ["car_id"]
    )

    # ── fuel_records ────────────────────────────────────────────────────
    op.create_table(
        "fuel_records",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("car_id", sa.BigInteger(), nullable=False),
        sa.Column("refueled_at", sa.Date(), nullable=False),
        sa.Column("odometer_km", sa.Integer(), nullable=False),
        sa.Column("liters", sa.Numeric(precision=6, scale=2), nullable=False),
        sa.Column(
            "price_per_liter",
            sa.Numeric(precision=6, scale=3),
            nullable=True,
        ),
        sa.Column(
            "total_cost", sa.Numeric(precision=10, scale=2), nullable=True
        ),
        sa.Column(
            "full_tank",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["car_id"], ["cars.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_fuel_records_car_id", "fuel_records", ["car_id"])

    # ── expenses ────────────────────────────────────────────────────────
    op.create_table(
        "expenses",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("car_id", sa.BigInteger(), nullable=False),
        sa.Column("occurred_at", sa.Date(), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column("amount", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("category", sa.String(length=32), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["car_id"], ["cars.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_expenses_car_id", "expenses", ["car_id"])

    # ── notification_rules ──────────────────────────────────────────────
    op.create_table(
        "notification_rules",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("car_id", sa.BigInteger(), nullable=False),
        sa.Column("item_type", sa.String(length=32), nullable=False),
        sa.Column(
            "lead_days_1",
            sa.Integer(),
            server_default=sa.text("30"),
            nullable=True,
        ),
        sa.Column(
            "lead_days_2",
            sa.Integer(),
            server_default=sa.text("14"),
            nullable=True,
        ),
        sa.Column(
            "lead_days_3",
            sa.Integer(),
            server_default=sa.text("7"),
            nullable=True,
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=False,
        ),
        sa.Column(
            "is_smart",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column(
            "channel_email",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=False,
        ),
        sa.Column(
            "channel_matrix",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["car_id"], ["cars.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_notification_rules_car_id", "notification_rules", ["car_id"]
    )

    # ── notification_log ────────────────────────────────────────────────
    op.create_table(
        "notification_log",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("car_id", sa.BigInteger(), nullable=False),
        sa.Column("rule_id", sa.BigInteger(), nullable=True),
        sa.Column("item_type", sa.String(length=32), nullable=True),
        sa.Column("lead_bucket", sa.Integer(), nullable=True),
        sa.Column("channel", sa.String(length=16), nullable=False),
        sa.Column("recipient", sa.String(length=255), nullable=True),
        sa.Column("subject", sa.String(length=255), nullable=True),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column(
            "sent_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["car_id"], ["cars.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["rule_id"], ["notification_rules.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_notification_log_car_id", "notification_log", ["car_id"]
    )
    op.create_index(
        "ix_notification_log_rule_id", "notification_log", ["rule_id"]
    )
    op.create_index(
        "ix_notification_log_dedup",
        "notification_log",
        ["car_id", "rule_id", "item_type", "lead_bucket", "channel", "sent_at"],
    )

    # ── app_settings ────────────────────────────────────────────────────
    op.create_table(
        "app_settings",
        sa.Column("key", sa.String(length=64), nullable=False),
        sa.Column("value", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("key"),
    )


def downgrade() -> None:
    # Drop in reverse dependency order.
    op.drop_table("app_settings")
    op.drop_index("ix_notification_log_dedup", table_name="notification_log")
    op.drop_index("ix_notification_log_rule_id", table_name="notification_log")
    op.drop_index("ix_notification_log_car_id", table_name="notification_log")
    op.drop_table("notification_log")
    op.drop_index(
        "ix_notification_rules_car_id", table_name="notification_rules"
    )
    op.drop_table("notification_rules")
    op.drop_index("ix_expenses_car_id", table_name="expenses")
    op.drop_table("expenses")
    op.drop_index("ix_fuel_records_car_id", table_name="fuel_records")
    op.drop_table("fuel_records")
    op.drop_index(
        "ix_service_intervals_car_id", table_name="service_intervals"
    )
    op.drop_table("service_intervals")
    op.drop_index("ix_service_records_car_id", table_name="service_records")
    op.drop_table("service_records")
    op.drop_index("ix_vignettes_car_id", table_name="vignettes")
    op.drop_table("vignettes")
    op.drop_index(
        "ix_insurance_policies_car_id", table_name="insurance_policies"
    )
    op.drop_table("insurance_policies")
    op.drop_index(
        "ix_technical_inspections_car_id", table_name="technical_inspections"
    )
    op.drop_table("technical_inspections")
    op.drop_index(
        "ix_tire_measurements_set_measured", table_name="tire_measurements"
    )
    op.drop_index(
        "ix_tire_measurements_tire_set_id", table_name="tire_measurements"
    )
    op.drop_table("tire_measurements")
    op.drop_index("ix_tire_sets_car_id", table_name="tire_sets")
    op.drop_table("tire_sets")
    op.drop_index(
        "ix_odometer_readings_car_recorded", table_name="odometer_readings"
    )
    op.drop_index(
        "ix_odometer_readings_car_id", table_name="odometer_readings"
    )
    op.drop_table("odometer_readings")
    op.drop_index("ix_user_car_groups_car_id", table_name="user_car_groups")
    op.drop_index("ix_user_car_groups_user_id", table_name="user_car_groups")
    op.drop_table("user_car_groups")
    op.drop_table("cars")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_index("ix_users_username", table_name="users")
    op.drop_table("users")
