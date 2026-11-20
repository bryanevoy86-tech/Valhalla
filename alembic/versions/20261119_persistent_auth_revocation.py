"""Persist WeWeb revoked JWT IDs across API restarts and instances.

Revision ID: 20261119_auth_revocations
Revises: 20261119_factory_legacy_work

Safe additive migration. No production mutation occurs by committing.
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20261119_auth_revocations"
down_revision = "20261119_factory_legacy_work"
branch_labels = None
depends_on = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if not inspector.has_table("auth_revoked_access_tokens"):
        op.create_table(
            "auth_revoked_access_tokens",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("jti_sha256", sa.String(length=64), nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        )
    indexes = {row["name"] for row in sa.inspect(op.get_bind()).get_indexes("auth_revoked_access_tokens")}
    for name, columns, unique in (
        ("ix_auth_revoked_access_tokens_jti_sha256", ["jti_sha256"], True),
        ("ix_auth_revoked_access_tokens_user_id", ["user_id"], False),
    ):
        if name not in indexes:
            op.create_index(name, "auth_revoked_access_tokens", columns, unique=unique)


def downgrade() -> None:
    # Deliberately non-destructive: downgrading auth code must never restore
    # previously revoked credentials by deleting revocation history.
    pass
