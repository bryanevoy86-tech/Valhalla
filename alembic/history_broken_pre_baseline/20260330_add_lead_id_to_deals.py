"""Add lead_id column to deals table to bridge pack_62 schema gap

The pack_62_underwriter migration created deals table with ext_id (underwriter focus).
The ORM/service layer expects lead_id (lead-to-deal pipeline focus).
This migration adds the missing lead_id column to reconcile the schemas.

Production Issue: psycopg2.errors.UndefinedColumn: column deals.lead_id does not exist
Root Cause: ORM query selects deals.lead_id but production table only has ext_id
Solution: Add nullable lead_id column to deals table
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "add_lead_id_to_deals"
down_revision = "add_updated_ts_to_deals"
branch_labels = None
depends_on = None


def upgrade():
    """Add lead_id column to deals table."""
    bind = op.get_bind()
    insp = inspect(bind)
    
    if "deals" in insp.get_table_names():
        columns = [col['name'] for col in insp.get_columns("deals")]
        
        # Add lead_id column if it doesn't exist
        if "lead_id" not in columns:
            op.add_column(
                "deals",
                sa.Column(
                    "lead_id",
                    sa.Integer,
                    nullable=True,  # Nullable initially for backward compatibility
                    index=True
                )
            )
            print("✅ Added lead_id column to deals table")
        else:
            print("✓ lead_id column already exists in deals table")


def downgrade():
    """Remove lead_id column from deals table."""
    bind = op.get_bind()
    insp = inspect(bind)
    
    if "deals" in insp.get_table_names():
        columns = [col['name'] for col in insp.get_columns("deals")]
        if "lead_id" in columns:
            op.drop_column("deals", "lead_id")
            print("✅ Dropped lead_id column from deals table")
