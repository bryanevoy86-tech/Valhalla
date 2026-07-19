"""
Pack 54: Children’s Hubs + Vault Guardians
"""
from alembic import op
import sqlalchemy as sa

revision = "0054_children_hubs"
down_revision = "0053_black_ice_tier2"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "child_profiles",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(64), nullable=False),
        sa.Column("age", sa.Integer, nullable=True),
        sa.Column("guardian_name", sa.String(64), nullable=True),
        sa.Column("avatar_theme", sa.String(32), nullable=True),
        sa.Column("save_pct", sa.Float, nullable=False, server_default="0.20"),
        sa.Column("invest_pct", sa.Float, nullable=False, server_default="0.00"),
        sa.Column("notes", sa.Text, nullable=True)
    )
    op.create_table(
        "vault_guardians",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("child_id", sa.Integer, sa.ForeignKey("child_profiles.id", ondelete="CASCADE")),
        sa.Column("name", sa.String(64), nullable=False),
        sa.Column("personality", sa.String(32), nullable=False),
        sa.Column("lore", sa.Text, nullable=True)
    )
    op.create_table(
        "chores",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("child_id", sa.Integer, sa.ForeignKey("child_profiles.id", ondelete="CASCADE")),
        sa.Column("title", sa.String(128), nullable=False),
        sa.Column("freq", sa.String(16), nullable=False),
        sa.Column("coins", sa.Integer, nullable=False),
        sa.Column("active", sa.Boolean, nullable=False, server_default=sa.text("true"))
    )
    op.create_table(
        "chore_logs",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("chore_id", sa.Integer, sa.ForeignKey("chores.id", ondelete="CASCADE")),
        sa.Column("completed_at", sa.DateTime, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("coins_awarded", sa.Integer, nullable=False)
    )
    op.create_table(
        "coin_wallets",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("child_id", sa.Integer, sa.ForeignKey("child_profiles.id", ondelete="CASCADE")),
        sa.Column("spendable", sa.Integer, nullable=False, server_default="0"),
        sa.Column("savings", sa.Integer, nullable=False, server_default="0"),
        sa.Column("invested", sa.Integer, nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime, server_default=sa.text("CURRENT_TIMESTAMP"))
    )
    op.create_table(
        "coin_txns",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("child_id", sa.Integer, sa.ForeignKey("child_profiles.id", ondelete="CASCADE")),
        sa.Column("kind", sa.String(24), nullable=False),
        sa.Column("amount", sa.Integer, nullable=False),
        sa.Column("memo", sa.String(256), nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.text("CURRENT_TIMESTAMP"))
    )
    op.create_table(
        "wishlist_items",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("child_id", sa.Integer, sa.ForeignKey("child_profiles.id", ondelete="CASCADE")),
        sa.Column("title", sa.String(128), nullable=False),
        sa.Column("priority", sa.Integer, nullable=False, server_default="3"),
        sa.Column("coins_target", sa.Integer, nullable=True)
    )
    op.create_table(
        "idea_submissions",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("child_id", sa.Integer, sa.ForeignKey("child_profiles.id", ondelete="CASCADE")),
        sa.Column("text", sa.Text, nullable=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.text("CURRENT_TIMESTAMP"))
    )

def downgrade():
    op.drop_table("idea_submissions")
    op.drop_table("wishlist_items")
    op.drop_table("coin_txns")
    op.drop_table("coin_wallets")
    op.drop_table("chore_logs")
    op.drop_table("chores")
    op.drop_table("vault_guardians")
    op.drop_table("child_profiles")
