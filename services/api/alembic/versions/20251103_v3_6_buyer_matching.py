"""v3.6 - buyers + deal_briefs (matching)"""
from alembic import op
import sqlalchemy as sa

revision = "v3_6_buyer_matching"
down_revision = "v3_5_grants"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "buyers",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("email", sa.String(length=160), nullable=True),
        sa.Column("phone", sa.String(length=40), nullable=True),
        sa.Column("regions", sa.String(length=240), nullable=True),
        sa.Column("property_types", sa.String(length=160), nullable=True),
        sa.Column("min_price", sa.Numeric(18,2), nullable=True),
        sa.Column("max_price", sa.Numeric(18,2), nullable=True),
        sa.Column("min_beds", sa.Integer(), nullable=True),
        sa.Column("min_baths", sa.Integer(), nullable=True),
        sa.Column("tags", sa.String(length=240), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )
    op.create_table(
        "deal_briefs",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("headline", sa.String(length=240), nullable=False),
        sa.Column("region", sa.String(length=120), nullable=True),
        sa.Column("property_type", sa.String(length=40), nullable=True),
        sa.Column("price", sa.Numeric(18,2), nullable=True),
        sa.Column("beds", sa.Integer(), nullable=True),
        sa.Column("baths", sa.Integer(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False, server_default=sa.text("'active'")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )

def downgrade():
    op.drop_table("deal_briefs")
    op.drop_table("buyers")
