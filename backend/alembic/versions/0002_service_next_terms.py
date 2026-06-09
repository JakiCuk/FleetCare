"""service record next-term fields

Revision ID: 0002
Revises: 0001
Create Date: 2026-06-08 00:00:00.000000

Adds the six nullable "next service terms" columns to ``service_records``
(service book "Vaše ďalšie termíny servisu"): a service inspection term
(date / km / by-indicator flag) and an additional-work term (description /
date / km). All columns are nullable; the ORM model must stay in sync.
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "service_records",
        sa.Column("next_service_date", sa.Date(), nullable=True),
    )
    op.add_column(
        "service_records",
        sa.Column("next_service_km", sa.Integer(), nullable=True),
    )
    op.add_column(
        "service_records",
        sa.Column("next_service_by_indicator", sa.Boolean(), nullable=True),
    )
    op.add_column(
        "service_records",
        sa.Column("next_additional_desc", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "service_records",
        sa.Column("next_additional_date", sa.Date(), nullable=True),
    )
    op.add_column(
        "service_records",
        sa.Column("next_additional_km", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("service_records", "next_additional_km")
    op.drop_column("service_records", "next_additional_date")
    op.drop_column("service_records", "next_additional_desc")
    op.drop_column("service_records", "next_service_by_indicator")
    op.drop_column("service_records", "next_service_km")
    op.drop_column("service_records", "next_service_date")
