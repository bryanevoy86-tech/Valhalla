"""Pack 65: Buyer Matching Engine (Preferences, Scoring, Distribution)"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import inspect
import logging

revision = "pack_65_buyer_match"
down_revision = "f358f8404d91"
branch_labels = None
depends_on = None

logger = logging.getLogger("alembic.runtime.migration")


def _table_exists(bind, name: str) -> bool:
    return name in inspect(bind).get_table_names()


def upgrade():
    bind = op.get_bind()

    if _table_exists(bind, "buyers"):
        logger.info("[migration 0065] buyers already exists; skipping create_table")
    else:
        op.create_table(
            "buyers",
            sa.Column("id", sa.BigInteger, primary_key=True),
            sa.Column("email", sa.String(256), unique=True, index=True),
            sa.Column("name", sa.String(128)),
            sa.Column("phone", sa.String(64)),
            sa.Column("status", sa.String(32), server_default="active"),
            sa.Column("created_ts", sa.DateTime, server_default=sa.text("now()")),
        )

    if _table_exists(bind, "buyer_preferences"):
        logger.info("[migration 0065] buyer_preferences already exists; skipping create_table")
    else:
        op.create_table(
            "buyer_preferences",
            sa.Column("id", sa.BigInteger, primary_key=True),
            sa.Column("buyer_id", sa.BigInteger, sa.ForeignKey("buyers.id", ondelete="CASCADE"), index=True),
            sa.Column("regions", postgresql.JSONB),
            sa.Column("asset_types", postgresql.JSONB),
            sa.Column("min_arv", sa.Numeric(14, 2)),
            sa.Column("max_arv", sa.Numeric(14, 2)),
            sa.Column("min_bed", sa.Integer),
            sa.Column("min_bath", sa.Float),
            sa.Column("max_repair_cost", sa.Numeric(14, 2)),
            sa.Column("yield_target_pct", sa.Float),
            sa.Column("notes", sa.Text),
        )

    if _table_exists(bind, "deal_buyer_matches"):
        logger.info("[migration 0065] deal_buyer_matches already exists; skipping create_table")
    else:
        op.create_table(
            "deal_buyer_matches",
            sa.Column("id", sa.BigInteger, primary_key=True),
            sa.Column("deal_id", sa.BigInteger, sa.ForeignKey("deals.id", ondelete="CASCADE"), index=True),
            sa.Column("buyer_id", sa.BigInteger, sa.ForeignKey("buyers.id", ondelete="CASCADE"), index=True),
            sa.Column("score", sa.Float),
            sa.Column("status", sa.String(32), index=True),
            sa.Column("notified_ts", sa.DateTime),
            sa.Column("claimed_ts", sa.DateTime),
            sa.Column("assigned_ts", sa.DateTime),
            sa.Column("meta", postgresql.JSONB),
        )

    if _table_exists(bind, "match_events"):
        logger.info("[migration 0065] match_events already exists; skipping create_table")
    else:
        op.create_table(
            "match_events",
            sa.Column("id", sa.BigInteger, primary_key=True),
            sa.Column("deal_id", sa.BigInteger, index=True),
            sa.Column("buyer_id", sa.BigInteger, index=True),
            sa.Column("ts", sa.DateTime, server_default=sa.text("now()")),
            sa.Column("event", sa.String(64)),
            sa.Column("payload", postgresql.JSONB),
        )


def downgrade():
    for t in ["match_events", "deal_buyer_matches", "buyer_preferences", "buyers"]:
        op.drop_table(t)
