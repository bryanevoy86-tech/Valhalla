"""Keep metered synthetic role probe receipts."""
from alembic import op
import sqlalchemy as sa

revision = "20261121_specialist_probes"
down_revision = "20261121_loki_result_digest"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "prime_specialist_probes",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("role", sa.String(40), nullable=False),
        sa.Column("provider_id", sa.Integer(), nullable=False),
        sa.Column("model", sa.String(160), nullable=False),
        sa.Column("case_id", sa.String(80), nullable=False),
        sa.Column("result", sa.String(20), nullable=False),
    )


def downgrade():
    # Retain receipts during application rollback.
    pass
