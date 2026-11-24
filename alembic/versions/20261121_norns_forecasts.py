"""Store forecasts before observable execution and retain measured outcomes."""
from alembic import op
import sqlalchemy as sa

revision = "20261121_norns_forecasts"
down_revision = "20261121_owner_extractions"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "prime_norns_forecasts",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("action_id", sa.String(80), nullable=False, unique=True),
        sa.Column("probability_bp", sa.Integer(), nullable=False),
        sa.Column("issued_at", sa.DateTime(), nullable=False),
        sa.Column("deadline_at", sa.DateTime(), nullable=False),
        sa.Column("resolved_at", sa.DateTime()),
        sa.Column("observed_outcome", sa.Integer()),
        sa.Column("evidence_ref", sa.String(180)),
        sa.CheckConstraint("probability_bp BETWEEN 0 AND 10000", name="ck_norns_probability_bp"),
        sa.CheckConstraint("observed_outcome IS NULL OR observed_outcome IN (0, 1)", name="ck_norns_binary_outcome"),
    )


def downgrade():
    # Keep predictions and observations available to the newer application.
    pass
