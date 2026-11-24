"""Persist independent specialist wake-ups without replacing pending work."""
from alembic import op
import sqlalchemy as sa

revision = "20261123_specialist_backlog"
down_revision = "20261123_owner_disposition"
branch_labels = None
depends_on = None


def upgrade():
    create_trigger_table("prime_specialist_triggers", "assignment_id", "prime_specialist_assignments",
                         "ix_specialist_trigger_order")
    create_trigger_table("prime_schedule_triggers", "schedule_id", "prime_specialist_schedules",
                         "ix_prime_schedule_trigger_order")
    # Keep the original slot during transition. The worker drains it before the new backlog.


def create_trigger_table(name, owner, parent, index):
    op.create_table(
        name,
        sa.Column(owner, sa.Uuid(), sa.ForeignKey(f"{parent}.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("event_id", sa.String(80), primary_key=True),
        sa.Column("queued_at", sa.DateTime(), nullable=False),
        sa.Column("failure_code", sa.String(48)),
    )
    op.create_index(index, name, [owner, "queued_at", "event_id"])


def downgrade():
    tables = ("prime_schedule_triggers", "prime_specialist_triggers")
    for table in tables:
        if op.get_bind().execute(sa.text(f"SELECT 1 FROM {table} LIMIT 1")).first():
            raise RuntimeError("Cannot downgrade while specialist research is recorded")
    for table in tables:
        op.drop_table(table)
