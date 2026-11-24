"""Store durable role-specific specialist monitoring assignments."""
from alembic import op
import sqlalchemy as sa

revision = "20261121_specialist_assignments"
down_revision = "20261121_provider_evidence"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "prime_specialist_assignments",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("role", sa.String(40), nullable=False),
        sa.Column("scope_key", sa.String(64), nullable=False),
        sa.Column("scope", sa.JSON(), nullable=False),
        sa.Column("cadence_seconds", sa.Integer(), nullable=False),
        sa.Column("next_due_at", sa.DateTime(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("state", sa.String(20), nullable=False),
        sa.Column("pending_event_id", sa.String(80)),
        sa.Column("last_report_event_id", sa.String(80)),
        sa.UniqueConstraint("role", "scope_key", name="uq_specialist_role_scope"),
    )
    op.create_index("ix_specialist_assignment_due", "prime_specialist_assignments", ["role", "state", "next_due_at"])
    op.create_index("ix_specialist_assignment_scope", "prime_specialist_assignments", ["scope_key", "state"])


def downgrade():
    # Retain assignments during rollback of application code.
    pass
