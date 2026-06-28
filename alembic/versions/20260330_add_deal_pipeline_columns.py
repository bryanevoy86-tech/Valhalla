"""Add all missing deal pipeline columns to pack_62 deals table

pack_62_underwriter created deals table for underwriter focus (ext_id, address, etc.)
API expects table for lead-to-deal pipeline focus (lead_id, title, stage, arv, etc.)

This migration bridges the schemas by adding all missing columns the ORM expects.

Columns to add:
- lead_id: foreign key to leads table
- title: Theissue summary
- stage: pipeline stage (lead_received, intake_review, etc.)
- arv: after-repair value
- estimated_repair_cost: estimated repair cost
- max_allowable_offer: MAO
- target_assignment_fee: assignment fee target
- score: heimdall score
- disposition_status: matched, pending, expired, etc.
- updated_ts: timestamp for updates (if not already added)

This makes pack_62 table compatible with the API ORM without data loss.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "add_deal_pipeline_columns"
down_revision = "add_lead_id_to_deals"
branch_labels = None
depends_on = None


def upgrade():
    """Add pipeline-specific columns to deals table."""
    bind = op.get_bind()
    insp = inspect(bind)
    
    if "deals" not in insp.get_table_names():
        print("✓ deals table does not exist; skipping migration")
        return
    
    columns = [col['name'] for col in insp.get_columns("deals")]
    
    # Define missing columns we need to add
    columns_to_add = [
        ("title", sa.String(255), False),  # (name, type, nullable)
        ("stage", sa.String(50), False),
        ("arv", sa.Numeric(15, 2), True),
        ("estimated_repair_cost", sa.Numeric(15, 2), True),
        ("max_allowable_offer", sa.Numeric(15, 2), True),
        ("target_assignment_fee", sa.Numeric(15, 2), True),
        ("score", sa.Numeric(8, 2), True),
        ("disposition_status", sa.String(50), True),
    ]
    
    for col_name, col_type, is_nullable in columns_to_add:
        if col_name not in columns:
            if col_name == "title":
                # Default value for existing rows
                op.add_column(
                    "deals",
                    sa.Column(col_name, col_type, nullable=True, server_default=sa.text("'imported'"))
                )
            elif col_name == "stage":
                # Default to a reasonable pipeline stage
                op.add_column(
                    "deals",
                    sa.Column(col_name, col_type, nullable=True, server_default=sa.text("'lead_received'"))
                )
            else:
                op.add_column(
                    "deals",
                    sa.Column(col_name, col_type, nullable=is_nullable)
                )
            print(f"✅ Added {col_name} column to deals table")
        else:
            print(f"✓ {col_name} column already exists in deals table")


def downgrade():
    """Remove pipeline columns from deals table."""
    bind = op.get_bind()
    insp = inspect(bind)
    
    if "deals" not in insp.get_table_names():
        return
    
    columns = [col['name'] for col in insp.get_columns("deals")]
    
    columns_to_remove = [
        "title", "stage", "arv", "estimated_repair_cost", 
        "max_allowable_offer", "target_assignment_fee", "score", "disposition_status"
    ]
    
    for col_name in columns_to_remove:
        if col_name in columns:
            op.drop_column("deals", col_name)
            print(f"✅ Dropped {col_name} column from deals table")
