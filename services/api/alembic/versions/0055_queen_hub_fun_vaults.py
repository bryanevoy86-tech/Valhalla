"""
Pack 55: Queen's Hub + Fun Fund Vaults
"""
from alembic import op
import sqlalchemy as sa

revision = "0055_queen_hub_fun_vaults"
down_revision = "0054_children_hubs"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "queen_profile",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(64), nullable=False),
        sa.Column("email", sa.String(128), nullable=True),
        sa.Column("currency", sa.String(8), nullable=False, server_default="CAD"),
        sa.Column("phase", sa.Integer, nullable=False, server_default="2"),
        sa.Column("cap_month", sa.Numeric(14, 2), nullable=False, server_default="10000"),
        sa.Column("tax_rate", sa.Float, nullable=False, server_default="0.18"),
        sa.Column("notes", sa.Text, nullable=True)
    )
    op.create_table(
        "queen_vaults",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("label", sa.String(64), nullable=False),
        sa.Column("balance", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("currency", sa.String(8), nullable=False, server_default="CAD")
    )
    op.create_table(
        "queen_vault_txns",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("vault_id", sa.Integer, sa.ForeignKey("queen_vaults.id", ondelete="CASCADE")),
        sa.Column("kind", sa.String(24), nullable=False),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("category", sa.String(64), nullable=True),
        sa.Column("note", sa.String(256), nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.text("CURRENT_TIMESTAMP"))
    )
    op.create_table(
        "queen_month_caps",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("yyyymm", sa.String(7), nullable=False),
        sa.Column("allowed", sa.Numeric(14, 2), nullable=False),
        sa.Column("used", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("phase", sa.Integer, nullable=False)
    )

def downgrade():
    op.drop_table("queen_month_caps")
    op.drop_table("queen_vault_txns")
    op.drop_table("queen_vaults")
    op.drop_table("queen_profile")
