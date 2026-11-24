"""Install persistent legacy work tables required by the governed Factory pilot.

Revision ID: 20261119_factory_legacy_work
Revises: 20261007_shadow_source_governance

The source models predate this migration. Existing tables are PRESERVED.
No production migration is performed by committing this file.
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20261119_factory_legacy_work"
down_revision = "20261007_shadow_source_governance"
branch_labels = None
depends_on = None


def _create_if_missing(table: str, *columns: sa.Column) -> None:
    if not sa.inspect(op.get_bind()).has_table(table):
        op.create_table(table, *columns)


def _index_if_missing(table: str, name: str, columns: list[str], *, unique: bool = False) -> None:
    inspector = sa.inspect(op.get_bind())
    existing = {i["name"] for i in inspector.get_indexes(table)}
    if name not in existing:
        op.create_index(name, table, columns, unique=unique)


def upgrade() -> None:
    # This migration intentionally does not attempt to create the entire
    # historical media schema. That belongs to the canonical baseline.
    if not sa.inspect(op.get_bind()).has_table("media_contents"):
        raise RuntimeError("media_contents missing: repair canonical baseline before factory migration")

    _create_if_missing(
        "legacy_instance_registry_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("legacy_instance_id", sa.String(80), nullable=False),
        sa.Column("display_name", sa.String(180), nullable=False),
        sa.Column("parent_instance_id", sa.String(80), nullable=True),
        sa.Column("assigned_businesses_json", sa.Text(), nullable=True),
        sa.Column("assigned_jurisdictions_json", sa.Text(), nullable=True),
        sa.Column("local_knowledge_context_json", sa.Text(), nullable=True),
        sa.Column("permissions_json", sa.Text(), nullable=True),
        sa.Column("integrations_json", sa.Text(), nullable=True),
        sa.Column("engines_json", sa.Text(), nullable=True),
        sa.Column("synchronization_status", sa.String(120), nullable=False, server_default="PENDING"),
        sa.Column("isolation_state", sa.String(80), nullable=False, server_default="ISOLATED"),
        sa.Column("failover_state", sa.String(80), nullable=False, server_default="NOT_TRIGGERED"),
        sa.Column("audit_state", sa.String(120), nullable=False, server_default="BASELINE_ONLY"),
        sa.Column("status", sa.String(80), nullable=False, server_default="PARTIAL"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    _index_if_missing(
        "legacy_instance_registry_items",
        "ix_legacy_instance_registry_items_legacy_instance_id",
        ["legacy_instance_id"],
        unique=True,
    )
    _index_if_missing(
        "legacy_instance_registry_items",
        "ix_legacy_instance_registry_items_id",
        ["id"],
    )

    _create_if_missing(
        "legacy_orchestration_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("event_id", sa.String(80), nullable=False),
        sa.Column("legacy_instance_id", sa.String(80), nullable=True),
        sa.Column("event_type", sa.String(80), nullable=False),
        sa.Column("severity", sa.String(40), nullable=False, server_default="info"),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("payload_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    _index_if_missing("legacy_orchestration_events", "ix_legacy_orchestration_events_event_id", ["event_id"], unique=True)
    _index_if_missing("legacy_orchestration_events", "ix_legacy_orchestration_events_legacy_instance_id", ["legacy_instance_id"])
    _index_if_missing("legacy_orchestration_events", "ix_legacy_orchestration_events_event_type", ["event_type"])

    _create_if_missing(
        "legacy_instance_work_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("action_id", sa.String(80), nullable=False),
        sa.Column("idempotency_key", sa.String(120), nullable=False),
        sa.Column("legacy_instance_id", sa.String(80), nullable=False),
        sa.Column("business_id", sa.String(120), nullable=False),
        sa.Column("industry", sa.String(120), nullable=False),
        sa.Column("jurisdiction", sa.String(80), nullable=False),
        sa.Column("engine_id", sa.String(80), nullable=False),
        sa.Column("objective", sa.String(255), nullable=False),
        sa.Column("status", sa.String(40), nullable=False, server_default="queued"),
        sa.Column("reassigned_from_instance_id", sa.String(80), nullable=True),
        sa.Column("risk_profile", sa.String(80), nullable=True),
        sa.Column("integration_profile", sa.String(120), nullable=True),
        sa.Column("namespace", sa.String(180), nullable=False),
        sa.Column("payload_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    for name, columns, unique in (
        ("ix_legacy_instance_work_items_action_id", ["action_id"], True),
        ("ix_legacy_instance_work_items_idempotency_key", ["idempotency_key"], True),
        ("ix_legacy_instance_work_items_legacy_instance_id", ["legacy_instance_id"], False),
        ("ix_legacy_instance_work_items_business_id", ["business_id"], False),
    ):
        _index_if_missing("legacy_instance_work_items", name, columns, unique=unique)


def downgrade() -> None:
    # Intentionally non-destructive. Tables may have existed before this
    # migration (created by earlier runtime registry code). Never drop
    # business records merely because a code version is rolled back.
    pass
