"""Persist tenant-bound internal SaaS trial entitlements."""
from alembic import op
import sqlalchemy as sa

revision = "20261122_saas_trial_entitlements"
down_revision = "20261121_foundry_evidence"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "saas_tenant_entitlements",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("subject_id", sa.Integer(), sa.ForeignKey("user_profiles.user_id"), nullable=False),
        sa.Column("plan_id", sa.Integer(), sa.ForeignKey("saas_plans.id"), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("revoked_at", sa.DateTime()),
        sa.Column("modules", sa.JSON(), nullable=False),
    )
    op.create_index("ix_saas_tenant_entitlements_tenant_id", "saas_tenant_entitlements", ["tenant_id"])


def downgrade():
    # Preserve trial authorization history.
    pass
