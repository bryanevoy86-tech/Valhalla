"""Add source registry governance fields for shadow-mode controls.

Revision ID: 20261007_shadow_source_governance
Revises: 8e43f380be7f
Create Date: 2026-10-07
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20261007_shadow_source_governance"
down_revision = "8e43f380be7f"
branch_labels = None
depends_on = None


def _column_names(table_name: str) -> set[str]:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not inspector.has_table(table_name):
        return set()
    return {col["name"] for col in inspector.get_columns(table_name)}


def _add_column_if_missing(table_name: str, column: sa.Column) -> None:
    if column.name not in _column_names(table_name):
        op.add_column(table_name, column)


def _drop_column_if_exists(table_name: str, column_name: str) -> None:
    if column_name in _column_names(table_name):
        op.drop_column(table_name, column_name)


def upgrade() -> None:
    table = "source_registry_items"

    _add_column_if_missing(table, sa.Column("permission_status", sa.String(length=80), nullable=True))
    _add_column_if_missing(table, sa.Column("license_status", sa.String(length=80), nullable=True))
    _add_column_if_missing(table, sa.Column("rights_statement_url", sa.String(length=500), nullable=True))
    _add_column_if_missing(table, sa.Column("robots_policy", sa.String(length=40), nullable=True))
    _add_column_if_missing(table, sa.Column("trust_tier", sa.String(length=40), nullable=True))
    _add_column_if_missing(table, sa.Column("provenance_method", sa.String(length=80), nullable=True))
    _add_column_if_missing(table, sa.Column("freshness_sla_hours", sa.Integer(), nullable=True))
    _add_column_if_missing(table, sa.Column("last_verified_at", sa.DateTime(), nullable=True))
    _add_column_if_missing(table, sa.Column("governance_status", sa.String(length=80), nullable=True))
    _add_column_if_missing(
        table,
        sa.Column("shadow_approved", sa.Boolean(), nullable=False, server_default=sa.text("true")),
    )


def downgrade() -> None:
    table = "source_registry_items"

    _drop_column_if_exists(table, "shadow_approved")
    _drop_column_if_exists(table, "governance_status")
    _drop_column_if_exists(table, "last_verified_at")
    _drop_column_if_exists(table, "freshness_sla_hours")
    _drop_column_if_exists(table, "provenance_method")
    _drop_column_if_exists(table, "trust_tier")
    _drop_column_if_exists(table, "robots_policy")
    _drop_column_if_exists(table, "rights_statement_url")
    _drop_column_if_exists(table, "license_status")
    _drop_column_if_exists(table, "permission_status")
