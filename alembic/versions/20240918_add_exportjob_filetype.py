"""
Alembic migration to add file_type column to export_jobs
"""

import sqlalchemy as sa
from alembic import op


def upgrade():
    op.add_column("export_jobs", sa.Column("file_type", sa.String(), nullable=True))


def downgrade():
    op.drop_column("export_jobs", "file_type")
