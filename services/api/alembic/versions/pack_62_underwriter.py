"""Pack 62: Underwriter Signals & Deal Risk Scoring"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "pack_62_underwriter"
down_revision = "pack_61_heimdall_training"
branch_labels = None
depends_on = None


def _table_exists(name: str, schema: str | None = None) -> bool:
    """Check if a table exists in the database."""
    bind = op.get_bind()
    insp = sa.inspect(bind)
    return name in insp.get_table_names(schema=schema)


def upgrade():
    if not _table_exists("deals"):
        op.create_table(
            "deals",
            sa.Column("id", sa.BigInteger, primary_key=True),
            sa.Column("ext_id", sa.String(64), unique=True, nullable=True),
            sa.Column("created_ts", sa.DateTime, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("address", sa.String(256)),
            sa.Column("city", sa.String(64)),
            sa.Column("province", sa.String(16)),
            sa.Column("postal_code", sa.String(16)),
            sa.Column("lat", sa.Float), sa.Column("lng", sa.Float),
            sa.Column("status", sa.String(32), index=True),
            sa.Column("ask_price", sa.Numeric(14,2)),
            sa.Column("notes", sa.Text),
            sa.Column("meta", postgresql.JSONB)
        )

    if not _table_exists("comps"):
        op.create_table(
            "comps",
            sa.Column("id", sa.BigInteger, primary_key=True),
            sa.Column("deal_id", sa.BigInteger, sa.ForeignKey("deals.id", ondelete="CASCADE"), index=True),
            sa.Column("address", sa.String(256)),
            sa.Column("sold_price", sa.Numeric(14,2)),
            sa.Column("sold_ts", sa.DateTime),
            sa.Column("bed", sa.Integer), sa.Column("bath", sa.Float),
            sa.Column("sqft", sa.Integer),
            sa.Column("distance_km", sa.Float),
            sa.Column("adj_factor", sa.Float, server_default="1.0"),
            sa.Column("meta", postgresql.JSONB)
        )

    if not _table_exists("underwriting_signals"):
        op.create_table(
            "underwriting_signals",
            sa.Column("id", sa.BigInteger, primary_key=True),
            sa.Column("deal_id", sa.BigInteger, sa.ForeignKey("deals.id", ondelete="CASCADE"), index=True),
            sa.Column("kind", sa.String(64)),
            sa.Column("value", sa.Float),
            sa.Column("unit", sa.String(16)),
            sa.Column("confidence", sa.Float),
            sa.Column("source", sa.String(64)),
            sa.Column("calc_ts", sa.DateTime, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("meta", postgresql.JSONB)
        )

    if not _table_exists("deal_scores"):
        op.create_table(
            "deal_scores",
            sa.Column("id", sa.BigInteger, primary_key=True),
            sa.Column("deal_id", sa.BigInteger, sa.ForeignKey("deals.id", ondelete="CASCADE"), index=True),
            sa.Column("score", sa.Float),
            sa.Column("roi_pct", sa.Float),
            sa.Column("ltv_pct", sa.Float),
            sa.Column("dti_pct", sa.Float),
            sa.Column("summary", sa.Text),
            sa.Column("recommendation", sa.String(32)),
            sa.Column("calc_ts", sa.DateTime, server_default=sa.text("CURRENT_TIMESTAMP"))
        )

def downgrade():
    for t in ["deal_scores","underwriting_signals","comps","deals"]:
        op.drop_table(t)
