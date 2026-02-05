"""Add production contract pipeline (S3 storage, webhooks, templates).

Revision ID: 20260205_contract_pipeline_s3
Revises: 20260205_add_floor_control_plane
Create Date: 2026-02-05

This migration creates the production contract pipeline with:
- Contract templates (merge schema for document generation)
- Contracts with state machine (DRAFT -> FULLY_EXECUTED)
- Contract documents (immutable, S3-addressed)
- Contract envelopes (signature provider integration)
- Contract parties (signers with provider recipient IDs)
- Contract events (full audit trail)

TYPE STANDARDIZATION:
- contract_templates.id = INTEGER (to match existing DB state)
- contracts.template_id = INTEGER (matches contract_templates.id)
"""
from alembic import op
import sqlalchemy as sa


revision = "20260205_contract_pipeline_s3"
down_revision = "20260205_add_floor_control_plane"
branch_labels = None
depends_on = None


def upgrade():
    # ---- CLEAN SLATE (safe because this is new / no prod data yet) ----
    # Drop in CASCADE order to handle any partial state from previous attempts
    op.execute("DROP TABLE IF EXISTS contract_events CASCADE;")
    op.execute("DROP TABLE IF EXISTS contract_documents CASCADE;")
    op.execute("DROP TABLE IF EXISTS contract_parties CASCADE;")
    op.execute("DROP TABLE IF EXISTS contracts CASCADE;")
    op.execute("DROP TABLE IF EXISTS contract_envelopes CASCADE;")
    op.execute("DROP TABLE IF EXISTS contract_templates CASCADE;")

    # contract_templates: id is INTEGER to match existing DB state
    op.create_table(
        "contract_templates",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("code", sa.String(), nullable=False, unique=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("merge_schema", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    # contract_envelopes (signature provider integration)
    op.create_table(
        "contract_envelopes",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("contract_id", sa.String(), nullable=False, index=True),
        sa.Column("provider", sa.String(), nullable=False),
        sa.Column("provider_envelope_id", sa.String(), nullable=True, index=True),
        sa.Column("status", sa.String(), nullable=False, server_default="created"),
        sa.Column("raw", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_unique_constraint(
        "uq_provider_envelope",
        "contract_envelopes",
        ["provider", "provider_envelope_id"]
    )

    # contracts: template_id is INTEGER to match contract_templates.id type
    op.create_table(
        "contracts",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("template_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("state", sa.String(), nullable=False, server_default="DRAFT"),
        sa.Column("deal_id", sa.String(), nullable=True, index=True),
        sa.Column("zone_id", sa.String(), nullable=True, index=True),
        sa.Column("merge_data", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("sign_provider", sa.String(), nullable=False, server_default="sandbox"),
        sa.Column("active_envelope_id", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    # Add FK constraints after table creation
    op.create_foreign_key(
        "fk_contracts_template_id",
        "contracts",
        "contract_templates",
        ["template_id"],
        ["id"]
    )
    op.create_foreign_key(
        "fk_contracts_active_envelope_id",
        "contracts",
        "contract_envelopes",
        ["active_envelope_id"],
        ["id"]
    )

    # contract_parties (signers with provider recipient IDs)
    op.create_table(
        "contract_parties",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("contract_id", sa.String(), nullable=False, index=True),
        sa.Column("role", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("email", sa.String(), nullable=True),
        sa.Column("phone", sa.String(), nullable=True),
        sa.Column("provider_recipient_id", sa.String(), nullable=True),
        sa.Column("must_sign", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("signed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_foreign_key(
        "fk_contract_parties_contract_id",
        "contract_parties",
        "contracts",
        ["contract_id"],
        ["id"]
    )
    op.create_index(
        "ix_contract_parties_contract_role",
        "contract_parties",
        ["contract_id", "role"]
    )

    # contract_documents (immutable, S3-addressed)
    op.create_table(
        "contract_documents",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("contract_id", sa.String(), nullable=False, index=True),
        sa.Column("kind", sa.String(), nullable=False),
        sa.Column("filename", sa.String(), nullable=False),
        sa.Column("content_type", sa.String(), nullable=False, server_default="application/pdf"),
        sa.Column("storage_key", sa.String(), nullable=False),
        sa.Column("sha256", sa.String(), nullable=True),
        sa.Column("bytes", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_foreign_key(
        "fk_contract_documents_contract_id",
        "contract_documents",
        "contracts",
        ["contract_id"],
        ["id"]
    )

    # contract_events (full audit trail)
    op.create_table(
        "contract_events",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("contract_id", sa.String(), nullable=False, index=True),
        sa.Column("event_type", sa.String(), nullable=False),
        sa.Column("actor", sa.String(), nullable=True),
        sa.Column("meta", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_foreign_key(
        "fk_contract_events_contract_id",
        "contract_events",
        "contracts",
        ["contract_id"],
        ["id"]
    )
    op.create_index(
        "ix_contract_events_contract_time",
        "contract_events",
        ["contract_id", "created_at"]
    )


def downgrade():
    # Drop in reverse order (no type stuff needed)
    op.drop_index("ix_contract_events_contract_time", table_name="contract_events")
    op.drop_table("contract_events")
    op.drop_table("contract_documents")
    op.drop_index("ix_contract_parties_contract_role", table_name="contract_parties")
    op.drop_table("contract_parties")
    op.drop_table("contracts")
    op.drop_constraint("uq_provider_envelope", "contract_envelopes", type_="unique")
    op.drop_table("contract_envelopes")
    op.drop_table("contract_templates")
