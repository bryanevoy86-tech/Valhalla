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
    inspector = sa.inspect(op.get_bind())
    if inspector.has_table("alembic_version"):
        version_type = next(column["type"] for column in inspector.get_columns("alembic_version")
                            if column["name"] == "version_num")
        if isinstance(version_type, sa.String) and version_type.length and version_type.length < len(revision):
            op.alter_column("alembic_version", "version_num", existing_type=version_type, type_=sa.String(80))

    # Older databases may already have this registry from the application bootstrap.
    if not inspector.has_table(table):
        op.create_table(
            table,
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("source_id", sa.String(80), nullable=False),
            sa.Column("canonical_name", sa.String(180), nullable=False),
            sa.Column("source_type", sa.String(80), nullable=False),
            sa.Column("data_class", sa.String(40), nullable=False),
            sa.Column("owner", sa.String(120)),
            sa.Column("jurisdiction", sa.String(80)),
            sa.Column("market", sa.String(120)),
            sa.Column("citation_ref", sa.String(255)),
            sa.Column("mode_allowlist_json", sa.Text()),
            sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("terminal_state", sa.String(64), nullable=False),
            sa.Column("notes", sa.Text()),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        )
        op.create_index("ix_source_registry_items_source_id", table, ["source_id"], unique=True)

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
