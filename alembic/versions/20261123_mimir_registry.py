"""Create the Mimir knowledge registry on canonically migrated installations."""

from alembic import op
import sqlalchemy as sa

revision = "20261123_mimir_registry"
down_revision = "20261123_loki_disposition_binding"
branch_labels = None
depends_on = None


def upgrade():
    name = "knowledge_registry_items"
    if sa.inspect(op.get_bind()).has_table(name):
        # Older installations could already have provisioned this table.
        return

    op.create_table(
        name,
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("item_id", sa.String(80), nullable=False),
        sa.Column("source", sa.String(255), nullable=False),
        sa.Column("source_type", sa.String(80), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("jurisdiction", sa.String(80)),
        sa.Column("market", sa.String(120)),
        sa.Column("effective_date", sa.Date()),
        sa.Column("retrieved_date", sa.Date()),
        sa.Column("review_date", sa.Date()),
        sa.Column("expires_date", sa.Date()),
        sa.Column("license_status", sa.String(80)),
        sa.Column("permission_status", sa.String(80)),
        sa.Column("quality_score", sa.Float()),
        sa.Column("confidence_score", sa.Float()),
        sa.Column("version", sa.String(40)),
        sa.Column("superseded_by", sa.String(80)),
        sa.Column("review_status", sa.String(80)),
        sa.Column("allowed_systems_json", sa.Text()),
        sa.Column("citation_ref", sa.String(255)),
        sa.Column("url", sa.String(500)),
        sa.Column("refresh_schedule", sa.String(120)),
        sa.Column("excluded", sa.Boolean(), nullable=False),
        sa.Column("terminal_state", sa.String(64), nullable=False),
        sa.Column("notes", sa.Text()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_knowledge_registry_items_id", name, ["id"])
    op.create_index("ix_knowledge_registry_items_item_id", name, ["item_id"], unique=True)


def downgrade():
    # An application rollback must retain both legacy and newly recorded evidence.
    pass
