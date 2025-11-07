"""
Pack 56: King’s Hub + Adaptive Vault Scaling
"""
from alembic import op
import sqlalchemy as sa

revision = "0056_kings_hub_adaptive_vaults"
down_revision = "0055_queen_hub_fun_vaults"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "king_profile",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(64), nullable=False, server_default="King"),
        sa.Column("currency", sa.String(8), nullable=False, server_default="CAD"),
        sa.Column("notes", sa.Text)
    )
    op.create_table(
        "king_vaults",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("label", sa.String(64), nullable=False),
        sa.Column("balance", sa.Numeric(14,2), nullable=False, server_default="0"),
        sa.Column("currency", sa.String(8), nullable=False, server_default="CAD")
    )
    op.create_table(
        "king_rules",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("active", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("rules_json", sa.Text, nullable=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.text("CURRENT_TIMESTAMP"))
    )
    op.create_table(
        "king_txns",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("vault_id", sa.Integer, sa.ForeignKey("king_vaults.id", ondelete="CASCADE")),
        sa.Column("kind", sa.String(24), nullable=False),
        sa.Column("amount", sa.Numeric(14,2), nullable=False),
        sa.Column("note", sa.String(256)),
        sa.Column("created_at", sa.DateTime, server_default=sa.text("CURRENT_TIMESTAMP"))
    )
    op.create_table(
        "bahamas_progress",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("target_amount", sa.Numeric(14,2), nullable=False, server_default="500000"),
        sa.Column("monthly_min", sa.Numeric(14,2), nullable=False, server_default="5000"),
        sa.Column("last_month_yyyymm", sa.String(7), nullable=True),
        sa.Column("status_note", sa.String(256), nullable=True)
    )


def downgrade():
    op.drop_table("bahamas_progress")
    op.drop_table("king_txns")
    op.drop_table("king_rules")
    op.drop_table("king_vaults")
    op.drop_table("king_profile")
