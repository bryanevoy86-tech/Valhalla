"""Add strategic modes and active mode for PACK CI7"""

from alembic import op
import sqlalchemy as sa

revision = "ci7_add_strategic_modes"
down_revision = "ci6_add_triggers"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "strategic_modes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False, unique=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("tuning_profile_name", sa.String(), nullable=True),
        sa.Column("parameters", sa.JSON(), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )

    op.create_table(
        "active_modes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("mode_name", sa.String(), nullable=False),
        sa.Column("changed_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("reason", sa.Text(), nullable=True),
    )


def downgrade():
    op.drop_table("active_modes")
    op.drop_table("strategic_modes")
