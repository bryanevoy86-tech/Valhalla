"""pack_121_whole_life_policies

Revision ID: f21b7c8d9e01
Revises: f20a6b7c8d90
Create Date: 2025-11-24
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "f21b7c8d9e01"
down_revision = "f20a6b7c8d90"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    if "whole_life_policies" not in inspect(bind).get_table_names():
        op.create_table(
            "whole_life_policies",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("insured_name", sa.String(), nullable=False),
            sa.Column("owner_entity", sa.String(), nullable=False),
            sa.Column("policy_number", sa.String(), nullable=False, unique=True),
            sa.Column("insurer", sa.String()),
            sa.Column("face_value", sa.Float(), server_default=sa.text("0.0")),
            sa.Column("annual_premium", sa.Float(), server_default=sa.text("0.0")),
            sa.Column("cash_value", sa.Float(), server_default=sa.text("0.0")),
            sa.Column("loan_available", sa.Float(), server_default=sa.text("0.0")),
            sa.Column("status", sa.String(), server_default=sa.text("'active'")),
            sa.Column("notes", sa.Text()),
            sa.Column("last_updated", sa.DateTime(timezone=True), server_default=sa.text("now()")),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        )
        op.create_index("ix_whole_life_policies_id", "whole_life_policies", ["id"], unique=False)
        op.create_index("ix_whole_life_policies_policy_number", "whole_life_policies", ["policy_number"], unique=True)
        op.create_index("ix_whole_life_policies_owner_entity", "whole_life_policies", ["owner_entity"], unique=False)


def downgrade():
    op.drop_index("ix_whole_life_policies_owner_entity", table_name="whole_life_policies")
    op.drop_index("ix_whole_life_policies_policy_number", table_name="whole_life_policies")
    op.drop_index("ix_whole_life_policies_id", table_name="whole_life_policies")
    op.drop_table("whole_life_policies")
