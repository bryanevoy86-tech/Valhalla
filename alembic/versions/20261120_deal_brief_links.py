"""Add source-backed links between canonical deals and independently sequenced briefs."""

from alembic import op
import sqlalchemy as sa

revision = "20261120_deal_brief_links"
down_revision = "20261119_auth_revocations"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "deal_brief_links",
        sa.Column("deal_id", sa.Integer(), nullable=False),
        sa.Column("brief_id", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("deal_id"),
        sa.UniqueConstraint("brief_id"),
        sa.ForeignKeyConstraint(["deal_id"], ["deals.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["brief_id"], ["deal_briefs.id"], ondelete="CASCADE"),
    )


def downgrade():
    # Keep explicitly established links if the application version is rolled back.
    pass
