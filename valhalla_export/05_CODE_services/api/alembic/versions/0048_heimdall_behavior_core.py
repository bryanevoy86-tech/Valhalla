"""Pack 48: Heimdall Behavioral Core Upgrade

Revision ID: 0048_heimdall_behavior_core
Revises: 0047_provider_adapters
Create Date: 2025-11-06

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0048_heimdall_behavior_core'
down_revision = '0047_provider_adapters'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # behavior_weights: persona-based feature weights
    op.create_table(
        'behavior_weights',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('persona', sa.String(64), nullable=False),
        sa.Column('trust_weight', sa.Numeric(5, 2), server_default=sa.text("1.0"), nullable=False),
        sa.Column('urgency_weight', sa.Numeric(5, 2), server_default=sa.text("1.0"), nullable=False),
        sa.Column('resistance_weight', sa.Numeric(5, 2), server_default=sa.text("1.0"), nullable=False),
        sa.Column('sentiment_weight', sa.Numeric(5, 2), server_default=sa.text("1.0"), nullable=False),
        sa.Column('authority_weight', sa.Numeric(5, 2), server_default=sa.text("1.0"), nullable=False),
        sa.Column('tone_weight', sa.Numeric(5, 2), server_default=sa.text("1.0"), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('persona', name='uq_behavior_weights_persona')
    )

    # script_snippets: dynamic response templates
    op.create_table(
        'script_snippets',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('snippet_name', sa.String(128), nullable=False),
        sa.Column('persona', sa.String(64), nullable=False),
        sa.Column('intent', sa.String(64), nullable=False),
        sa.Column('tone', sa.String(64), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('confidence_threshold', sa.Numeric(5, 2), server_default=sa.text("0.5"), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('snippet_name', name='uq_script_snippets_name')
    )
    op.create_index('ix_script_snippets_persona_intent', 'script_snippets', ['persona', 'intent'])

    # negotiation_sessions: track conversation state
    op.create_table(
        'negotiation_sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.String(64), nullable=False),
        sa.Column('persona', sa.String(64), nullable=False),
        sa.Column('lead_id', sa.Integer(), nullable=True),
        sa.Column('deal_id', sa.Integer(), nullable=True),
        sa.Column('started_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('ended_at', sa.DateTime(), nullable=True),
        sa.Column('outcome', sa.String(64), nullable=True),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('session_id', name='uq_negotiation_sessions_session_id')
    )
    op.create_index('ix_negotiation_sessions_lead_id', 'negotiation_sessions', ['lead_id'])
    op.create_index('ix_negotiation_sessions_deal_id', 'negotiation_sessions', ['deal_id'])

    # behavior_events: log tone/intent changes during negotiation
    op.create_table(
        'behavior_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.String(64), nullable=False),
        sa.Column('event_type', sa.String(64), nullable=False),
        sa.Column('speaker', sa.String(32), nullable=False),
        sa.Column('text', sa.Text(), nullable=True),
        sa.Column('trust_score', sa.Numeric(5, 2), nullable=True),
        sa.Column('urgency_score', sa.Numeric(5, 2), nullable=True),
        sa.Column('resistance_score', sa.Numeric(5, 2), nullable=True),
        sa.Column('sentiment_score', sa.Numeric(5, 2), nullable=True),
        sa.Column('authority_score', sa.Numeric(5, 2), nullable=True),
        sa.Column('tone', sa.String(64), nullable=True),
        sa.Column('intent', sa.String(64), nullable=True),
        sa.Column('timestamp', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_behavior_events_session_id', 'behavior_events', ['session_id'])


def downgrade() -> None:
    op.drop_index('ix_behavior_events_session_id', table_name='behavior_events')
    op.drop_table('behavior_events')
    op.drop_index('ix_negotiation_sessions_deal_id', table_name='negotiation_sessions')
    op.drop_index('ix_negotiation_sessions_lead_id', table_name='negotiation_sessions')
    op.drop_table('negotiation_sessions')
    op.drop_index('ix_script_snippets_persona_intent', table_name='script_snippets')
    op.drop_table('script_snippets')
    op.drop_table('behavior_weights')
