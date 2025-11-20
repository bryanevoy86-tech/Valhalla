"""Pack 63: Behavioral Closer Engine & Script Orchestrator"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects import postgresql

revision = "pack_63_closer_engine"
down_revision = "pack_62_underwriter"
branch_labels = None
depends_on = None

def upgrade():
    bind = op.get_bind()
    inspector = inspect(bind)
    existing = set(inspector.get_table_names())
    
    if "seller_profiles" not in existing:
        op.create_table(
            "seller_profiles",
            sa.Column("id", sa.BigInteger, primary_key=True),
            sa.Column("contact_id", sa.String(64), index=True),
            sa.Column("tone", sa.String(32)),
            sa.Column("objections", postgresql.JSONB),
            sa.Column("sentiment", sa.Float),
            sa.Column("last_seen", sa.DateTime, server_default=sa.text("CURRENT_TIMESTAMP"))
        )
    
    if "script_blocks" not in existing:
        op.create_table(
            "script_blocks",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("namespace", sa.String(64), index=True),
            sa.Column("version", sa.Integer, index=True),
            sa.Column("content", sa.Text),
            sa.Column("active", sa.Boolean, server_default=sa.text("true"))
        )
    
    if "playbooks" not in existing:
        op.create_table(
            "playbooks",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("name", sa.String(128), unique=True),
            sa.Column("graph", postgresql.JSONB),
            sa.Column("active", sa.Boolean, server_default=sa.text("true"))
        )
    
    if "closer_sessions" not in existing:
        op.create_table(
            "closer_sessions",
            sa.Column("id", sa.BigInteger, primary_key=True),
            sa.Column("deal_id", sa.BigInteger, sa.ForeignKey("deals.id", ondelete="SET NULL"), index=True),
            sa.Column("seller_profile_id", sa.BigInteger, sa.ForeignKey("seller_profiles.id", ondelete="SET NULL")),
            sa.Column("state", sa.String(32), index=True),
            sa.Column("current_block_id", sa.Integer, sa.ForeignKey("script_blocks.id")),
            sa.Column("started_ts", sa.DateTime, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("updated_ts", sa.DateTime, server_default=sa.text("CURRENT_TIMESTAMP"))
        )
    
    if "closer_events" not in existing:
        op.create_table(
            "closer_events",
            sa.Column("id", sa.BigInteger, primary_key=True),
            sa.Column("session_id", sa.BigInteger, sa.ForeignKey("closer_sessions.id", ondelete="CASCADE"), index=True),
            sa.Column("ts", sa.DateTime, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("event", sa.String(64)),
            sa.Column("payload", postgresql.JSONB)
        )

def downgrade():
    for t in ["closer_events","closer_sessions","playbooks","script_blocks","seller_profiles"]:
        op.drop_table(t)
