"""Pack N: Contract Lifecycle Engine

Revision ID: 0103_contract_lifecycle
Revises: 0102_professional_task_links
Create Date: 2025-12-05

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0103_contract_lifecycle"
down_revision = "0102_professional_task_links"
branch_labels = None
depends_on = None


def upgrade():
    # Create contract_records table (skip if already exists from another migration)
    from sqlalchemy import inspect
    from alembic import op
    
    conn = op.get_bind()
    inspector = inspect(conn)
    
    if "contract_records" not in inspector.get_table_names():
        op.create_table(
            "contract_records",
            sa.Column("id", sa.Integer, primary_key=True, index=True),
            sa.Column("deal_id", sa.Integer, nullable=False),
            sa.Column("professional_id", sa.Integer, nullable=True),
            sa.Column("status", sa.String(50), nullable=False, server_default="draft"),
            sa.Column("version", sa.Integer, nullable=False, server_default="1"),
            sa.Column("storage_url", sa.String(500), nullable=True),
            sa.Column("title", sa.String(200), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("signed_at", sa.DateTime(timezone=True), nullable=True),
        )

        # Create indexes for better query performance
        op.create_index("ix_contract_records_deal_id", "contract_records", ["deal_id"])
        op.create_index("ix_contract_records_professional_id", "contract_records", ["professional_id"])
        op.create_index("ix_contract_records_status", "contract_records", ["status"])
        op.create_index("ix_contract_records_signed_at", "contract_records", ["signed_at"])
    else:
        print("INFO: contract_records table already exists, skipping creation")


def downgrade():
    # Drop indexes
    op.drop_index("ix_contract_records_signed_at", "contract_records")
    op.drop_index("ix_contract_records_status", "contract_records")
    op.drop_index("ix_contract_records_professional_id", "contract_records")
    op.drop_index("ix_contract_records_deal_id", "contract_records")

    # Drop table
    op.drop_table("contract_records")
