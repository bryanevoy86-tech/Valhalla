"""Add narrative chapters, events, and active chapter for PACK CI8"""

from alembic import op
import sqlalchemy as sa

revision = "ci8_add_narrative"
down_revision = "ci7_add_strategic_modes"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "narrative_chapters",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("slug", sa.String(), nullable=False, unique=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("phase_order", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("goals", sa.JSON(), nullable=True),
        sa.Column("exit_conditions", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )

    op.create_table(
        "narrative_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("chapter_id", sa.Integer(), nullable=False, index=True),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("tags", sa.JSON(), nullable=True),
        sa.Column("occurred_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )

    op.create_table(
        "active_chapters",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("chapter_id", sa.Integer(), nullable=False),
        sa.Column("changed_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("reason", sa.Text(), nullable=True),
    )


def downgrade():
    op.drop_table("active_chapters")
    op.drop_table("narrative_events")
    op.drop_table("narrative_chapters")
