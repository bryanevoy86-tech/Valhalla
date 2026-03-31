"""Add missing updated_ts column to deals table"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime

revision = "add_updated_ts_to_deals"
down_revision = "20260205_final_consolidation"
branch_labels = None
depends_on = None


def upgrade():
    """Add updated_ts column to deals table."""
    # Check if column already exists before adding
    bind = op.get_bind()
    insp = sa.inspect(bind)
    
    if "deals" in insp.get_table_names():
        columns = [col['name'] for col in insp.get_columns("deals")]
        if "updated_ts" not in columns:
            op.add_column(
                "deals",
                sa.Column(
                    "updated_ts",
                    sa.DateTime,
                    nullable=True,
                    server_default=sa.text("CURRENT_TIMESTAMP"),
                    onupdate=sa.text("CURRENT_TIMESTAMP")
                )
            )
            print("✅ Added updated_ts column to deals table")
        else:
            print("✓ updated_ts column already exists in deals table")


def downgrade():
    """Remove updated_ts column from deals table."""
    bind = op.get_bind()
    insp = sa.inspect(bind)
    
    if "deals" in insp.get_table_names():
        columns = [col['name'] for col in insp.get_columns("deals")]
        if "updated_ts" in columns:
            op.drop_column("deals", "updated_ts")
            print("✅ Dropped updated_ts column from deals table")
