"""Add maintenance tables for PACK UE"""

from alembic import op
import sqlalchemy as sa

revision = "0074_pack_ue_maintenance"
down_revision = "0073_pack_ud_api_clients"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "maintenance_windows",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("starts_at", sa.DateTime(), nullable=False),
        sa.Column("ends_at", sa.DateTime(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False, server_default="true"),
    )

    op.create_table(
        "maintenance_state",
        sa.Column("id", sa.Integer(), primary_key=True, default=1),
        sa.Column("mode", sa.String(), nullable=False, server_default="normal"),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    
    op.create_index("ix_maintenance_windows_starts_at", "maintenance_windows", ["starts_at"])


def downgrade():
    op.drop_table("maintenance_state")
    op.drop_table("maintenance_windows")
