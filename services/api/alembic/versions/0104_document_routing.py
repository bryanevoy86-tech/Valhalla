"""Pack O: Document Routing Engine

Revision ID: 0104_document_routing
Revises: 0103_contract_lifecycle
Create Date: 2025-12-05

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0104_document_routing"
down_revision = "0103_contract_lifecycle"
branch_labels = None
depends_on = None


def upgrade():
    # Create document_routes table
    op.create_table(
        "document_routes",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column("deal_id", sa.Integer, nullable=False),
        sa.Column("contract_id", sa.Integer, sa.ForeignKey("contract_records.id"), nullable=True),
        sa.Column("professional_id", sa.Integer, sa.ForeignKey("professionals.id"), nullable=False),
        sa.Column("document_type", sa.String(100), nullable=False),
        sa.Column("storage_url", sa.String(500), nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("opened_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="sent"),
    )

    # Create indexes for better query performance
    op.create_index("ix_document_routes_deal_id", "document_routes", ["deal_id"])
    op.create_index("ix_document_routes_contract_id", "document_routes", ["contract_id"])
    op.create_index("ix_document_routes_professional_id", "document_routes", ["professional_id"])
    op.create_index("ix_document_routes_status", "document_routes", ["status"])
    op.create_index("ix_document_routes_document_type", "document_routes", ["document_type"])


def downgrade():
    # Drop indexes
    op.drop_index("ix_document_routes_document_type", "document_routes")
    op.drop_index("ix_document_routes_status", "document_routes")
    op.drop_index("ix_document_routes_professional_id", "document_routes")
    op.drop_index("ix_document_routes_contract_id", "document_routes")
    op.drop_index("ix_document_routes_deal_id", "document_routes")

    # Drop table
    op.drop_table("document_routes")
