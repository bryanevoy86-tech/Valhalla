"""Add decision_outcomes table for PACK CL9"""

from alembic import op
import sqlalchemy as sa

revision = "cl9_add_decision_outcomes"
down_revision = "ci8_add_narrative"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "decision_outcomes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("decision_id", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("domain", sa.String(), nullable=False),
        sa.Column("action_taken", sa.String(), nullable=False),
        sa.Column("outcome_quality", sa.String(), nullable=True),
        sa.Column("impact_score", sa.Integer(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("context", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("occurred_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("ix_decision_outcomes_decision_id", "decision_outcomes", ["decision_id"])
    op.create_index("ix_decision_outcomes_domain", "decision_outcomes", ["domain"])


def downgrade():
    op.drop_index("ix_decision_outcomes_decision_id", table_name="decision_outcomes")
    op.drop_index("ix_decision_outcomes_domain", table_name="decision_outcomes")
    op.drop_table("decision_outcomes")
