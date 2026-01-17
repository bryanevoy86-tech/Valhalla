"""v3.10 - integrity_events telemetry ledger"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

revision = "v3_10_integrity_events"
down_revision = "v3_9_research_db"
branch_labels = None
depends_on = None


def _table_exists(conn, name: str) -> bool:
    insp = Inspector.from_engine(conn)
    return name in insp.get_table_names()


def upgrade() -> None:
    bind = op.get_bind()
    if not _table_exists(bind, "integrity_events"):
        op.create_table(
            "integrity_events",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("ts", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
            sa.Column("event", sa.String(length=200), nullable=False),
            sa.Column("level", sa.String(length=16), nullable=False, server_default="info"),
            sa.Column("actor", sa.String(length=120), nullable=False, server_default="system"),
            sa.Column("meta", sa.Text(), nullable=False, server_default="{}"),
        )
        op.create_index("ix_integrity_events_id", "integrity_events", ["id"]) 
        op.create_index("ix_integrity_events_event", "integrity_events", ["event"]) 
        op.create_index("ix_integrity_events_level", "integrity_events", ["level"]) 
        op.create_index("ix_integrity_events_actor", "integrity_events", ["actor"]) 


def downgrade() -> None:
    bind = op.get_bind()
    if _table_exists(bind, "integrity_events"):
        op.drop_index("ix_integrity_events_actor", table_name="integrity_events")
        op.drop_index("ix_integrity_events_level", table_name="integrity_events")
        op.drop_index("ix_integrity_events_event", table_name="integrity_events")
        op.drop_index("ix_integrity_events_id", table_name="integrity_events")
        op.drop_table("integrity_events")
