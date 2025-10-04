"""
Alembic migration for files storage tables
"""

import sqlalchemy as sa
from alembic import op


def upgrade():
    op.create_table(
        "file_objects",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("org_id", sa.Integer, index=True, nullable=False),
        sa.Column("owner_user_id", sa.Integer, index=True),
        sa.Column("kind", sa.String),
        sa.Column("key", sa.String, unique=True, index=True, nullable=False),
        sa.Column("filename", sa.String, nullable=False),
        sa.Column("mime", sa.String),
        sa.Column("size_bytes", sa.Integer),
        sa.Column("status", sa.String, nullable=False, server_default="pending"),
        sa.Column("checksum", sa.String),
        sa.Column("meta", sa.JSON),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            index=True,
        ),
        sa.Column(
            "updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")
        ),
    )
    op.create_table(
        "file_access_grants",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "file_id",
            sa.Integer,
            sa.ForeignKey("file_objects.id", ondelete="CASCADE"),
            index=True,
            nullable=False,
        ),
        sa.Column("user_id", sa.Integer, index=True),
        sa.Column("role", sa.String),
        sa.Column("can_read", sa.Boolean, server_default=sa.text("1")),
        sa.Column("can_write", sa.Boolean, server_default=sa.text("0")),
        sa.Column(
            "created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")
        ),
    )


def downgrade():
    op.drop_table("file_access_grants")
    op.drop_table("file_objects")
