"""
Engine readiness state machine - deterministic promotion governance.
"""

from alembic import op
import sqlalchemy as sa


revision = "20260203_engine_readiness"
down_revision = "20260203_sandbox_visibility"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "engine_readiness",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("engine_name", sa.String(64), nullable=False),
        sa.Column("state", sa.String(16), nullable=False, server_default="DISABLED"),
        sa.Column("approval_rate", sa.Float(), nullable=True),
        sa.Column("false_positive_rate", sa.Float(), nullable=True),
        sa.Column("sample_size", sa.Integer(), nullable=True),
        sa.Column(
            "evaluated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("engine_name"),
    )
    op.create_index(op.f("ix_engine_readiness_engine_name"), "engine_readiness", ["engine_name"], unique=False)


def downgrade():
    op.drop_index(op.f("ix_engine_readiness_engine_name"), table_name="engine_readiness")
    op.drop_table("engine_readiness")
