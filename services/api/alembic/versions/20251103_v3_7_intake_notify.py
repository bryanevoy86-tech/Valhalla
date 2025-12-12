"""v3.7 - lead intake + outbox"""

from alembic import op
import sqlalchemy as sa

revision = "v3_7_intake_notify"
down_revision = "v3_6_buyer_matching"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "lead_intake",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("source", sa.String(length=80), nullable=True),
        sa.Column("name", sa.String(length=160), nullable=True),
        sa.Column("email", sa.String(length=160), nullable=True),
        sa.Column("phone", sa.String(length=40), nullable=True),
        sa.Column("address", sa.String(length=240), nullable=True),
        sa.Column("region", sa.String(length=120), nullable=True),
        sa.Column("property_type", sa.String(length=40), nullable=True),
        sa.Column("price", sa.Numeric(18,2), nullable=True),
        sa.Column("beds", sa.Integer(), nullable=True),
        sa.Column("baths", sa.Integer(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False, server_default=sa.text("'new'")),
        sa.Column("raw_json", sa.Text(), nullable=True),
        sa.Column("deal_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )
    op.create_table(
        "outbox",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("kind", sa.String(length=20), nullable=False),
        sa.Column("target", sa.String(length=240), nullable=True),
        sa.Column("subject", sa.String(length=240), nullable=True),
        sa.Column("payload_json", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default=sa.text("'queued'")),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )


def downgrade():
    op.drop_table("outbox")
    op.drop_table("lead_intake")
