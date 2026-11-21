"""Subscribe scoped specialist schedules to verified outcomes."""
from alembic import op
import sqlalchemy as sa

revision = "20261120_specialist_triggers"
down_revision = "20261120_owner_conversation"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("prime_specialist_schedules", sa.Column("outcome_scope_key", sa.String(64)))
    op.add_column("prime_specialist_schedules", sa.Column("pending_outcome_event_id", sa.String(80)))
    op.create_index("ix_specialist_outcome_scope", "prime_specialist_schedules", ["outcome_scope_key", "state"])
    op.create_index(
        "ix_specialist_pending_outcome", "prime_specialist_schedules", ["pending_outcome_event_id"],
        postgresql_where=sa.text("pending_outcome_event_id IS NOT NULL"),
    )


def downgrade():
    # Keep pending subscriptions available after application rollback.
    pass
