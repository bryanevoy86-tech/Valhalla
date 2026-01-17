"""Pack 61: Heimdall Intelligence Training & Evolution Core"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "pack_61_heimdall_training"
down_revision = "pack_60_tax_tracker"
branch_labels = None
depends_on = None


def _table_exists(name: str, schema: str | None = None) -> bool:
    """Check if a table exists in the database."""
    bind = op.get_bind()
    insp = sa.inspect(bind)
    return name in insp.get_table_names(schema=schema)


def upgrade():
    if not _table_exists("prompt_versions"):
        op.create_table(
            "prompt_versions",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("namespace", sa.String(64), index=True),
            sa.Column("version", sa.Integer, index=True),
            sa.Column("content", sa.Text),
            sa.Column("active", sa.Boolean, server_default=sa.text("false")),
            sa.Column("created_ts", sa.DateTime, server_default=sa.text("CURRENT_TIMESTAMP"))
        )

    if not _table_exists("training_corpus"):
        op.create_table(
            "training_corpus",
            sa.Column("id", sa.BigInteger, primary_key=True),
            sa.Column("source", sa.String(128)),
            sa.Column("text", sa.Text),
            sa.Column("meta", postgresql.JSONB),
            sa.Column("ts", sa.DateTime, server_default=sa.text("CURRENT_TIMESTAMP"))
        )

    if not _table_exists("feedback_events"):
        op.create_table(
            "feedback_events",
            sa.Column("id", sa.BigInteger, primary_key=True),
            sa.Column("ts", sa.DateTime, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("module", sa.String(64)),
            sa.Column("kind", sa.String(32)),
            sa.Column("label", sa.String(64)),
            sa.Column("score", sa.Float),
            sa.Column("payload", postgresql.JSONB)
        )

    if not _table_exists("ab_tests"):
        op.create_table(
            "ab_tests",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("namespace", sa.String(64), index=True),
            sa.Column("a_version", sa.Integer),
            sa.Column("b_version", sa.Integer),
            sa.Column("split_pct", sa.Integer, default=50),
            sa.Column("start_ts", sa.DateTime, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("end_ts", sa.DateTime),
            sa.Column("metrics", postgresql.JSONB)
        )

    if not _table_exists("model_evals"):
        op.create_table(
            "model_evals",
            sa.Column("id", sa.BigInteger, primary_key=True),
            sa.Column("namespace", sa.String(64), index=True),
            sa.Column("version", sa.Integer, index=True),
            sa.Column("metric", sa.String(64)),
            sa.Column("value", sa.Float),
            sa.Column("sample_size", sa.Integer),
            sa.Column("eval_ts", sa.DateTime, server_default=sa.text("CURRENT_TIMESTAMP"))
        )


def downgrade():
    for t in ["model_evals","ab_tests","feedback_events","training_corpus","prompt_versions"]:
        op.drop_table(t)
