"""add research and playbooks tables

Revision ID: v3_3_research
Revises: v3_2_builder
Create Date: 2025-11-02

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'v3_3_research'
down_revision = 'v3_2_builder'
branch_labels = None
depends_on = None


def upgrade():
    # Create research_sources table
    op.create_table(
        'research_sources',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('url', sa.String(length=2048), nullable=False),
        sa.Column('kind', sa.String(length=50), nullable=True),
        sa.Column('ttl_seconds', sa.Integer(), nullable=True),
        sa.Column('enabled', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('last_ingested_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_research_sources_id'), 'research_sources', ['id'], unique=False)

    # Create research_docs table
    op.create_table(
        'research_docs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('source_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=512), nullable=True),
        sa.Column('url', sa.String(length=2048), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('chunk_index', sa.Integer(), nullable=True),
        sa.Column('ingested_at', sa.DateTime(), nullable=True),
        sa.Column('metadata_json', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['source_id'], ['research_sources.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_research_docs_id'), 'research_docs', ['id'], unique=False)

    # Create research_queries table
    op.create_table(
        'research_queries',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('query_text', sa.Text(), nullable=False),
        sa.Column('result_count', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('metadata_json', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_research_queries_id'), 'research_queries', ['id'], unique=False)

    # Create playbooks table
    op.create_table(
        'playbooks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('slug', sa.String(length=255), nullable=False),
        sa.Column('title', sa.String(length=512), nullable=False),
        sa.Column('body_md', sa.Text(), nullable=False),
        sa.Column('tags', sa.String(length=512), nullable=True),
        sa.Column('enabled', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_playbooks_id'), 'playbooks', ['id'], unique=False)
    op.create_index(op.f('ix_playbooks_slug'), 'playbooks', ['slug'], unique=True)


def downgrade():
    op.drop_index(op.f('ix_playbooks_slug'), table_name='playbooks')
    op.drop_index(op.f('ix_playbooks_id'), table_name='playbooks')
    op.drop_table('playbooks')
    
    op.drop_index(op.f('ix_research_queries_id'), table_name='research_queries')
    op.drop_table('research_queries')
    
    op.drop_index(op.f('ix_research_docs_id'), table_name='research_docs')
    op.drop_table('research_docs')
    
    op.drop_index(op.f('ix_research_sources_id'), table_name='research_sources')
    op.drop_table('research_sources')
