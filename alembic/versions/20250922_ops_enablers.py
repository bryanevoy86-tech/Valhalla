from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = "ops_enablers_001"
down_revision = None  # Set to previous revision if not first
branch_labels = None
depends_on = None

def upgrade():
    # leads: status + SLA
    op.add_column("leads", sa.Column("status", sa.Text(), nullable=False, server_default="new"))
    op.add_column("leads", sa.Column("sla_expires_at", sa.TIMESTAMP(timezone=True), nullable=True))
    op.create_index("idx_leads_status", "leads", ["status"], unique=False)
    op.create_index("idx_leads_sla_expires_at", "leads", ["sla_expires_at"], unique=False)

    # offers: response due
    op.add_column("offers", sa.Column("response_due_at", sa.TIMESTAMP(timezone=True), nullable=True))
    op.create_index("idx_offers_response_due_at", "offers", ["response_due_at"], unique=False)

    # buyers: criteria box
    op.add_column("buyers", sa.Column("buy_box", postgresql.JSONB(astext_type=sa.Text()), nullable=True))

    # feature flags (simple)
    op.create_table(
        "feature_flags",
        sa.Column("key", sa.Text(), primary_key=True),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()")),
    )

def downgrade():
    op.drop_table("feature_flags")
    op.drop_index("idx_offers_response_due_at", table_name="offers")
    op.drop_column("offers", "response_due_at")
    op.drop_index("idx_leads_sla_expires_at", table_name="leads")
    op.drop_index("idx_leads_status", table_name="leads")
    op.drop_column("leads", "sla_expires_at")
    op.drop_column("leads", "status")
    op.drop_column("buyers", "buy_box")
