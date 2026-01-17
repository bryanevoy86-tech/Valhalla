"""v3.4 - research doc embeddings

Revision ID: v3_4_embeddings
Revises: v3_3_research
Create Date: 2025-11-02

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "v3_4_embeddings"
down_revision = "v3_3_research"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("research_docs", sa.Column("embedding_json", sa.Text(), nullable=True))


def downgrade():
    op.drop_column("research_docs", "embedding_json")
