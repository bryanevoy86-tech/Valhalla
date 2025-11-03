"""v3.8 - contract templates + records"""
from alembic import op
import sqlalchemy as sa

revision = "v3_8_contracts"
down_revision = "v3_7_intake_notify"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "contract_templates",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("version", sa.String(length=40), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("body_text", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )
    op.create_table(
        "contract_records",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("template_id", sa.Integer, sa.ForeignKey("contract_templates.id", ondelete="SET NULL"), nullable=True),
        sa.Column("filename", sa.String(length=200), nullable=False),
        sa.Column("context_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )


def downgrade():
    op.drop_table("contract_records")
    op.drop_table("contract_templates")
