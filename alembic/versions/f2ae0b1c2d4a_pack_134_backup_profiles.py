"""pack_134_backup_profiles

Revision ID: f2ae0b1c2d4a
Revises: f2ad0b1c2d49
Create Date: 2025-11-24
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision: str = "f2ae0b1c2d4a"
down_revision: Union[str, Sequence[str], None] = "f2ad0b1c2d49"
branch_labels = None
depends_on = None

def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if "backup_profiles" not in inspector.get_table_names():
        op.create_table(
            "backup_profiles",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("name", sa.String(), nullable=False, unique=True),
            sa.Column("target_type", sa.String(), nullable=False),
            sa.Column("target_identifier", sa.String(), nullable=False),
            sa.Column("frequency", sa.String(), server_default="daily"),
            sa.Column("retention_days", sa.Integer(), server_default="30"),
            sa.Column("encrypted", sa.Boolean(), server_default=sa.text("true")),
            sa.Column("encryption_profile", sa.String()),
            sa.Column("offsite_copy", sa.Boolean(), server_default=sa.text("true")),
            sa.Column("notes", sa.Text()),
            sa.Column("created_at", sa.DateTime()),
            sa.Column("updated_at", sa.DateTime()),
        )
        op.create_index("ix_backup_profiles_name", "backup_profiles", ["name"], unique=True)
        op.create_index("ix_backup_profiles_target_type", "backup_profiles", ["target_type"])


def downgrade() -> None:
    op.drop_index("ix_backup_profiles_target_type", table_name="backup_profiles")
    op.drop_index("ix_backup_profiles_name", table_name="backup_profiles")
    op.drop_table("backup_profiles")
