"""
Pack 58: Resort Vault + Residency Timeline
"""
from alembic import op
import sqlalchemy as sa

revision = "0058_resort_residency"
down_revision = "0057_pantry_photo_inventory"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "resort_projects",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("currency", sa.String(8), nullable=False, server_default="USD"),
        sa.Column("target_budget", sa.Numeric(14,2), nullable=False, server_default="0"),
        sa.Column("vault_balance", sa.Numeric(14,2), nullable=False, server_default="0"),
        sa.Column("status", sa.String(24), nullable=False, server_default="planning"),
        sa.Column("notes", sa.Text)
    )
    op.create_table(
        "resort_vault_txns",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("project_id", sa.Integer, sa.ForeignKey("resort_projects.id", ondelete="CASCADE")),
        sa.Column("kind", sa.String(24), nullable=False),  # inflow|outflow|fx|grant
        sa.Column("amount", sa.Numeric(14,2), nullable=False),
        sa.Column("note", sa.String(256)),
        sa.Column("created_at", sa.DateTime, server_default=sa.text("CURRENT_TIMESTAMP"))
    )
    op.create_table(
        "resort_milestones",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("project_id", sa.Integer, sa.ForeignKey("resort_projects.id", ondelete="CASCADE")),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("due_date", sa.Date, nullable=True),
        sa.Column("status", sa.String(16), nullable=False, server_default="pending"),
        sa.Column("percent", sa.Float, nullable=False, server_default="0")
    )
    op.create_table(
        "resort_quotes",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("project_id", sa.Integer, sa.ForeignKey("resort_projects.id", ondelete="CASCADE")),
        sa.Column("vendor", sa.String(128), nullable=False),
        sa.Column("scope", sa.String(256), nullable=False),
        sa.Column("amount", sa.Numeric(14,2), nullable=False),
        sa.Column("currency", sa.String(8), nullable=False, server_default="USD"),
        sa.Column("status", sa.String(16), nullable=False, server_default="received")
    )
    op.create_table(
        "resort_funding",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("project_id", sa.Integer, sa.ForeignKey("resort_projects.id", ondelete="CASCADE")),
        sa.Column("source", sa.String(128), nullable=False),    # grant|loan|investor
        sa.Column("program_name", sa.String(128), nullable=True),
        sa.Column("amount", sa.Numeric(14,2), nullable=False),
        sa.Column("currency", sa.String(8), nullable=False, server_default="USD"),
        sa.Column("status", sa.String(16), nullable=False, server_default="prospect")
    )
    op.create_table(
        "residency_timeline",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("country", sa.String(64), nullable=False),    # Bahamas
        sa.Column("target_date", sa.Date, nullable=True),
        sa.Column("min_capital", sa.Numeric(14,2), nullable=False, server_default="0"),
        sa.Column("status", sa.String(16), nullable=False, server_default="planning"),
        sa.Column("note", sa.Text)
    )
    op.create_table(
        "residency_steps",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("timeline_id", sa.Integer, sa.ForeignKey("residency_timeline.id", ondelete="CASCADE")),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("due_date", sa.Date, nullable=True),
        sa.Column("status", sa.String(16), nullable=False, server_default="pending"),
        sa.Column("percent", sa.Float, nullable=False, server_default="0")
    )

def downgrade():
    op.drop_table("residency_steps")
    op.drop_table("residency_timeline")
    op.drop_table("resort_funding")
    op.drop_table("resort_quotes")
    op.drop_table("resort_milestones")
    op.drop_table("resort_vault_txns")
    op.drop_table("resort_projects")
