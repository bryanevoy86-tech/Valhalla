"""Store internal Product Foundry assets and their exact license attestations."""
from alembic import op
import sqlalchemy as sa


revision = "20261120_product_artifacts"
down_revision = "20261120_specialist_schedules"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "product_artifacts",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("legacy_instance_id", sa.String(80), nullable=False),
        sa.Column("business_id", sa.String(120), nullable=False),
        sa.Column("engine_id", sa.String(80), nullable=False),
        sa.Column("jurisdiction", sa.String(80), nullable=False),
        sa.Column("product_id", sa.String(80), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("media_type", sa.String(80), nullable=False),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column("data", sa.LargeBinary(), nullable=False),
        sa.Column("rights_reference", sa.String(240), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint(
            "legacy_instance_id", "business_id", "engine_id", "jurisdiction", "product_id", "version",
            name="uq_product_artifact_scope_version",
        ),
        sa.CheckConstraint("version > 0 AND length(data) BETWEEN 1 AND 5242880", name="ck_product_artifact_size_version"),
    )


def downgrade():
    # Preserve evidence and user-provided artifacts during an application rollback.
    pass
