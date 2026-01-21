from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import inspect

# revision identifiers
revision = "ops_enablers_001"
down_revision = "20260121_go_live_core_tables"
branch_labels = None
depends_on = None

def upgrade():
    bind = op.get_bind()
    insp = inspect(bind)
    existing_tables = set(insp.get_table_names())

    # leads: status + SLA (only if leads table exists)
    if "leads" in existing_tables:
        # add columns
        op.add_column("leads", sa.Column("status", sa.Text(), nullable=False, server_default="new"))
        op.add_column("leads", sa.Column("sla_expires_at", sa.TIMESTAMP(timezone=True), nullable=True))
        # add indexes if missing
        lead_indexes = {idx.get("name") for idx in insp.get_indexes("leads")}
        if "idx_leads_status" not in lead_indexes:
            op.create_index("idx_leads_status", "leads", ["status"], unique=False)
        if "idx_leads_sla_expires_at" not in lead_indexes:
            op.create_index("idx_leads_sla_expires_at", "leads", ["sla_expires_at"], unique=False)

    # offers: response due (only if offers table exists)
    if "offers" in existing_tables:
        op.add_column("offers", sa.Column("response_due_at", sa.TIMESTAMP(timezone=True), nullable=True))
        offer_indexes = {idx.get("name") for idx in insp.get_indexes("offers")}
        if "idx_offers_response_due_at" not in offer_indexes:
            op.create_index("idx_offers_response_due_at", "offers", ["response_due_at"], unique=False)

    # buyers: criteria box (only if buyers table exists)
    if "buyers" in existing_tables:
        op.add_column("buyers", sa.Column("buy_box", postgresql.JSONB(astext_type=sa.Text()), nullable=True))

    # feature flags (simple) — always safe to create
    if "feature_flags" not in existing_tables:
        op.create_table(
            "feature_flags",
            sa.Column("key", sa.Text(), primary_key=True),
            sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("note", sa.Text(), nullable=True),
            sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()")),
        )

def downgrade():
    bind = op.get_bind()
    insp = inspect(bind)
    existing_tables = set(insp.get_table_names())

    if "feature_flags" in existing_tables:
        op.drop_table("feature_flags")

    if "offers" in existing_tables:
        offer_indexes = {idx.get("name") for idx in insp.get_indexes("offers")}
        if "idx_offers_response_due_at" in offer_indexes:
            op.drop_index("idx_offers_response_due_at", table_name="offers")
        if any(col.get("name") == "response_due_at" for col in insp.get_columns("offers")):
            op.drop_column("offers", "response_due_at")

    if "leads" in existing_tables:
        lead_indexes = {idx.get("name") for idx in insp.get_indexes("leads")}
        if "idx_leads_sla_expires_at" in lead_indexes:
            op.drop_index("idx_leads_sla_expires_at", table_name="leads")
        if "idx_leads_status" in lead_indexes:
            op.drop_index("idx_leads_status", table_name="leads")
        lead_cols = {c.get("name") for c in insp.get_columns("leads")}
        if "sla_expires_at" in lead_cols:
            op.drop_column("leads", "sla_expires_at")
        if "status" in lead_cols:
            op.drop_column("leads", "status")

    if "buyers" in existing_tables:
        buyer_cols = {c.get("name") for c in insp.get_columns("buyers")}
        if "buy_box" in buyer_cols:
            op.drop_column("buyers", "buy_box")
