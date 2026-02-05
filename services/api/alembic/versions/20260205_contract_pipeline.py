"""Add contract pipeline tables.

Revision ID: 20260205_contract_pipeline
Revises: 20260205_add_floor_control_plane
Create Date: 2026-02-05
"""
from alembic import op
import sqlalchemy as sa

revision = "20260205_contract_pipeline"
down_revision = "20260205_add_floor_control_plane"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "contract_templates",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("code", sa.String(), nullable=False, unique=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("merge_schema", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "contracts",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("template_id", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("state", sa.Enum("DRAFT", "READY_FOR_REVIEW", "IN_REVIEW", "APPROVED_FOR_SIGNATURE",
                                   "SENT_FOR_SIGNATURE", "PARTIALLY_SIGNED", "FULLY_EXECUTED",
                                   "DECLINED", "VOIDED", "ARCHIVED", name="contract_state"),
                  nullable=False, server_default="DRAFT"),
        sa.Column("deal_id", sa.String(), nullable=True),
        sa.Column("zone_id", sa.String(), nullable=True),
        sa.Column("merge_data", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("sign_provider", sa.Enum("sandbox", "docusign", name="sign_provider"),
                  nullable=False, server_default="sandbox"),
        sa.Column("active_envelope_id", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["template_id"], ["contract_templates.id"]),
        sa.ForeignKeyConstraint(["active_envelope_id"], ["contract_envelopes.id"]),
        sa.Index("ix_contracts_deal_id", "deal_id"),
        sa.Index("ix_contracts_zone_id", "zone_id"),
    )

    op.create_table(
        "contract_parties",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("contract_id", sa.String(), nullable=False),
        sa.Column("role", sa.Enum("SELLER", "BUYER", "ASSIGNOR", "ASSIGNEE", "WITNESS",
                                  "NOTARY", "OTHER", name="contract_party_role"),
                  nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("email", sa.String(), nullable=True),
        sa.Column("phone", sa.String(), nullable=True),
        sa.Column("provider_recipient_id", sa.String(), nullable=True),
        sa.Column("must_sign", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("signed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["contract_id"], ["contracts.id"]),
        sa.Index("ix_contract_parties_contract_id", "contract_id"),
        sa.Index("ix_contract_parties_contract_role", "contract_id", "role"),
    )

    op.create_table(
        "contract_documents",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("contract_id", sa.String(), nullable=False),
        sa.Column("kind", sa.Enum("DRAFT", "EXECUTED", "ATTACHMENT", name="contract_doc_kind"),
                  nullable=False),
        sa.Column("filename", sa.String(), nullable=False),
        sa.Column("content_type", sa.String(), nullable=False, server_default="application/pdf"),
        sa.Column("storage_key", sa.String(), nullable=False),
        sa.Column("sha256", sa.String(), nullable=True),
        sa.Column("bytes", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["contract_id"], ["contracts.id"]),
        sa.Index("ix_contract_documents_contract_id", "contract_id"),
    )

    op.create_table(
        "contract_envelopes",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("contract_id", sa.String(), nullable=False),
        sa.Column("provider", sa.Enum("sandbox", "docusign", name="sign_provider"),
                  nullable=False),
        sa.Column("provider_envelope_id", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="created"),
        sa.Column("raw", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["contract_id"], ["contracts.id"]),
        sa.Index("ix_contract_envelopes_contract_id", "contract_id"),
        sa.Index("ix_contract_envelopes_provider_envelope_id", "provider_envelope_id"),
        sa.UniqueConstraint("provider", "provider_envelope_id", name="uq_provider_envelope"),
    )

    op.create_table(
        "contract_events",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("contract_id", sa.String(), nullable=False),
        sa.Column("event_type", sa.String(), nullable=False),
        sa.Column("actor", sa.String(), nullable=True),
        sa.Column("meta", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["contract_id"], ["contracts.id"]),
        sa.Index("ix_contract_events_contract_id", "contract_id"),
        sa.Index("ix_contract_events_contract_time", "contract_id", "created_at"),
    )


def downgrade():
    op.drop_table("contract_events")
    op.drop_table("contract_envelopes")
    op.drop_table("contract_documents")
    op.drop_table("contract_parties")
    op.drop_table("contracts")
    op.drop_table("contract_templates")
