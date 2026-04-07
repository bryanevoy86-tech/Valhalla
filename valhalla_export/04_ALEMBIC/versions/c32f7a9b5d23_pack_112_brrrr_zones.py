"""pack_112_brrrr_zones

Revision ID: c32f7a9b5d23
Revises: b21e6f8a4c12
Create Date: 2025-11-24
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision: str = "c32f7a9b5d23"
down_revision: Union[str, Sequence[str], None] = "b21e6f8a4c12"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = inspect(bind)
    if "brrrr_zones" not in insp.get_table_names():
        op.create_table(
            "brrrr_zones",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("code", sa.String(), nullable=False, unique=True),
            sa.Column("name", sa.String(), nullable=False),
            sa.Column("country", sa.String(), nullable=False),
            sa.Column("min_properties_before_team", sa.Integer(), server_default=sa.text("5")),
            sa.Column("current_property_count", sa.Integer(), server_default=sa.text("0")),
            sa.Column("currency", sa.String(), server_default=sa.text("'CAD'")),
            sa.Column("language", sa.String(), server_default=sa.text("'en'")),
            sa.Column("timezone", sa.String(), server_default=sa.text("'UTC'")),
            sa.Column("active", sa.Boolean(), server_default=sa.text("false")),
            sa.Column("legal_profile_code", sa.String()),
            sa.Column("notes", sa.Text()),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        )
        op.create_index("ix_brrrr_zones_id", "brrrr_zones", ["id"], unique=False)
        op.create_index("ix_brrrr_zones_code", "brrrr_zones", ["code"], unique=True)
        op.create_index("ix_brrrr_zones_active", "brrrr_zones", ["active"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_brrrr_zones_active", table_name="brrrr_zones")
    op.drop_index("ix_brrrr_zones_code", table_name="brrrr_zones")
    op.drop_index("ix_brrrr_zones_id", table_name="brrrr_zones")
    op.drop_table("brrrr_zones")
