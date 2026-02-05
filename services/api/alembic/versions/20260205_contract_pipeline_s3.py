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
"""
from alembic import op
import sqlalchemy as sa


revision = "20260205_contract_pipeline_s3"
down_revision = "20260205_add_floor_control_plane"
branch_labels = None
depends_on = None


def upgrade():
    # contract_templates - check if it exists first (handles database reset scenarios)
    if not op.get_context().dialect.has_table(op.get_context().connection, "contract_templates"):
        op.create_table(
            "contract_templates",
            sa.Column("id", sa.String(), primary_key=True),
            sa.Column("code", sa.String(), nullable=False, unique=True),
            sa.Column("name", sa.String(), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("merge_schema", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        )

    # contract_envelopes (signature provider integration)
    if not op.get_context().dialect.has_table(op.get_context().connection, "contract_envelopes"):
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

    # contracts (state machine: DRAFT -> APPROVED_FOR_SIGNATURE -> SENT_FOR_SIGNATURE -> FULLY_EXECUTED)
    if not op.get_context().dialect.has_table(op.get_context().connection, "contracts"):
        op.create_table(
            "contracts",
            sa.Column("id", sa.String(), primary_key=True),
            sa.Column("template_id", sa.String(), sa.ForeignKey("contract_templates.id"), nullable=False),
            sa.Column("title", sa.String(), nullable=False),
            sa.Column("state", sa.String(), nullable=False, server_default="DRAFT"),
            sa.Column("deal_id", sa.String(), nullable=True, index=True),
            sa.Column("zone_id", sa.String(), nullable=True, index=True),
            sa.Column("merge_data", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("sign_provider", sa.String(), nullable=False, server_default="sandbox"),
            sa.Column("active_envelope_id", sa.String(), sa.ForeignKey("contract_envelopes.id"), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        )

    # contract_parties (signers with provider recipient IDs)
    if not op.get_context().dialect.has_table(op.get_context().connection, "contract_parties"):
        op.create_table(
            "contract_parties",
            sa.Column("id", sa.String(), primary_key=True),
            sa.Column("contract_id", sa.String(), sa.ForeignKey("contracts.id"), nullable=False, index=True),
            sa.Column("role", sa.String(), nullable=False),
            sa.Column("name", sa.String(), nullable=False),
            sa.Column("email", sa.String(), nullable=True),
            sa.Column("phone", sa.String(), nullable=True),
            sa.Column("provider_recipient_id", sa.String(), nullable=True),
            sa.Column("must_sign", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("signed_at", sa.DateTime(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        )
        op.create_index(
            "ix_contract_parties_contract_role",
            "contract_parties",
            ["contract_id", "role"]
        )

    # contract_documents (immutable, S3-addressed)
    if not op.get_context().dialect.has_table(op.get_context().connection, "contract_documents"):
        op.create_table(
            "contract_documents",
            sa.Column("id", sa.String(), primary_key=True),
            sa.Column("contract_id", sa.String(), sa.ForeignKey("contracts.id"), nullable=False, index=True),
            sa.Column("kind", sa.String(), nullable=False),
            sa.Column("filename", sa.String(), nullable=False),
            sa.Column("content_type", sa.String(), nullable=False, server_default="application/pdf"),
            sa.Column("storage_key", sa.String(), nullable=False),
            sa.Column("sha256", sa.String(), nullable=True),
            sa.Column("bytes", sa.Integer(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        )

    # contract_events (full audit trail)
    if not op.get_context().dialect.has_table(op.get_context().connection, "contract_events"):
        op.create_table(
            "contract_events",
            sa.Column("id", sa.String(), primary_key=True),
            sa.Column("contract_id", sa.String(), sa.ForeignKey("contracts.id"), nullable=False, index=True),
            sa.Column("event_type", sa.String(), nullable=False),
            sa.Column("actor", sa.String(), nullable=True),
            sa.Column("meta", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        )
        op.create_index(
            "ix_contract_events_contract_time",
            "contract_events",
            ["contract_id", "created_at"]
        )


def downgrade():
    # Reverse order of creation, with existence checks
    if op.get_context().dialect.has_table(op.get_context().connection, "contract_events"):
        op.drop_index("ix_contract_events_contract_time", table_name="contract_events")
        op.drop_table("contract_events")
    
    if op.get_context().dialect.has_table(op.get_context().connection, "contract_documents"):
        op.drop_table("contract_documents")
    
    if op.get_context().dialect.has_table(op.get_context().connection, "contract_parties"):
        op.drop_index("ix_contract_parties_contract_role", table_name="contract_parties")
        op.drop_table("contract_parties")
    
    if op.get_context().dialect.has_table(op.get_context().connection, "contracts"):
        op.drop_table("contracts")
    
    if op.get_context().dialect.has_table(op.get_context().connection, "contract_envelopes"):
        op.drop_constraint("uq_provider_envelope", "contract_envelopes", type_="unique")
        op.drop_table("contract_envelopes")
    
    if op.get_context().dialect.has_table(op.get_context().connection, "contract_templates"):
        op.drop_table("contract_templates")
