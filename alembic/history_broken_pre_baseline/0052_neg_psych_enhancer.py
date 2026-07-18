"""Pack 52: Negotiation & Psychology AI Enhancer

Revision ID: 0052_neg_psych_enhancer
Revises: 0051_legal_document_engine
Create Date: 2025-11-06

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0052_neg_psych_enhancer"
down_revision = "0051_legal_document_engine"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "objection_catalog",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("code", sa.String(32), unique=True, nullable=False),
        sa.Column("pattern_regex", sa.Text, nullable=False),
        sa.Column("severity", sa.String(16), nullable=False, server_default="med"),
        sa.Column("notes", sa.Text)
    )
    op.create_table(
        "rebuttal_snippets",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("objection_code", sa.String(32), nullable=False),
        sa.Column("persona", sa.String(48), nullable=False),
        sa.Column("tone", sa.String(32), nullable=False),
        sa.Column("content", sa.Text, nullable=False)
    )
    op.create_table(
        "persona_knobs",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("persona", sa.String(48), unique=True, nullable=False),
        sa.Column("ask_softener_pct", sa.Float, nullable=False, server_default="0.15"),
        sa.Column("mirror_ack_rate", sa.Float, nullable=False, server_default="0.30"),
        sa.Column("probe_depth", sa.Integer, nullable=False, server_default="2")
    )
    op.create_table(
        "session_metrics",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("session_id", sa.Integer, sa.ForeignKey("negotiation_sessions.id", ondelete="CASCADE")),
        sa.Column("turn_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("last_tone", sa.String(32)),
        sa.Column("avg_sentiment", sa.Float, nullable=False, server_default="0"),
        sa.Column("conf_score", sa.Float, nullable=False, server_default="0"),
        sa.Column("objection_last", sa.String(32)),
        sa.Column("updated_at", sa.DateTime, server_default=sa.text("CURRENT_TIMESTAMP"))
    )
    op.create_table(
        "escalation_rules",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(64), nullable=False),
        sa.Column("threshold", sa.Float, nullable=False),
        sa.Column("action", sa.String(64), nullable=False),
        sa.Column("payload_json", sa.Text, nullable=True)
    )
    op.create_table(
        "neg_rewards",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("session_id", sa.Integer, sa.ForeignKey("negotiation_sessions.id", ondelete="CASCADE")),
        sa.Column("signal", sa.String(32), nullable=False),
        sa.Column("weight", sa.Float, nullable=False, server_default="1.0"),
        sa.Column("notes", sa.Text),
        sa.Column("created_at", sa.DateTime, server_default=sa.text("CURRENT_TIMESTAMP"))
    )


def downgrade():
    op.drop_table("neg_rewards")
    op.drop_table("escalation_rules")
    op.drop_table("session_metrics")
    op.drop_table("persona_knobs")
    op.drop_table("rebuttal_snippets")
    op.drop_table("objection_catalog")
