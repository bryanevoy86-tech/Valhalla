"""Support atomic owner attachment disposition with an audit tombstone."""

from alembic import op
import sqlalchemy as sa

revision = "20261123_owner_disposition"
down_revision = "20261123_builder_lease_cap"
branch_labels = None
depends_on = None

TABLE = "prime_owner_attachments"


def upgrade():
    with op.batch_alter_table(TABLE) as table:
        table.add_column(sa.Column("deleted_at", sa.DateTime(timezone=True)))
        table.add_column(sa.Column("deletion_reason", sa.String(24)))
        table.drop_constraint("ck_prime_owner_attachment_size", type_="check")
        table.alter_column("data", nullable=True, existing_type=sa.LargeBinary())
        table.create_check_constraint(
            "ck_prime_owner_attachment_state",
            "(deleted_at IS NULL AND deletion_reason IS NULL AND data IS NOT NULL "
            "AND length(data) BETWEEN 1 AND 5242880) OR "
            "(deleted_at IS NOT NULL AND deletion_reason IS NOT NULL AND data IS NULL "
            "AND deletion_reason IN ('OWNER_REQUEST', 'RETENTION_EXPIRED'))",
        )


def downgrade():
    if op.get_bind().execute(sa.text(
        "SELECT 1 FROM prime_owner_attachments WHERE deleted_at IS NOT NULL LIMIT 1"
    )).first():
        raise RuntimeError("Cannot downgrade owner attachments with recorded dispositions")
    with op.batch_alter_table(TABLE) as table:
        table.drop_constraint("ck_prime_owner_attachment_state", type_="check")
        table.alter_column("data", nullable=False, existing_type=sa.LargeBinary())
        table.drop_column("deletion_reason")
        table.drop_column("deleted_at")
        table.create_check_constraint("ck_prime_owner_attachment_size", "length(data) BETWEEN 1 AND 5242880")
