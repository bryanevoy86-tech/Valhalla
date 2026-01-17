"""Add tuning profiles and constraints for PACK CI5"""

from alembic import op
import sqlalchemy as sa

revision = "ci5_add_tuning_rules"
down_revision = "ci4_add_insights"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "tuning_profiles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False, unique=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("aggression", sa.Integer(), nullable=False, server_default="50"),
        sa.Column("risk_tolerance", sa.Integer(), nullable=False, server_default="50"),
        sa.Column("safety_bias", sa.Integer(), nullable=False, server_default="70"),
        sa.Column("growth_bias", sa.Integer(), nullable=False, server_default="70"),
        sa.Column("stability_bias", sa.Integer(), nullable=False, server_default="60"),
        sa.Column("weights", sa.JSON(), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )

    op.create_table(
        "tuning_constraints",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("profile_id", sa.Integer(), nullable=False, index=True),
        sa.Column("key", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("rules", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )


def downgrade():
    op.drop_table("tuning_constraints")
    op.drop_table("tuning_profiles")
