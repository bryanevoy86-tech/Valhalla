from alembic import op
import sqlalchemy as sa

revision = "0047_provider_adapters"
down_revision = "0046_clone_mirror_policies"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "provider_tokens",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("provider", sa.String(32), nullable=False),
        sa.Column("account_ref", sa.String(128), nullable=True),
        sa.Column("access_token", sa.Text, nullable=False),
        sa.Column("refresh_token", sa.Text, nullable=True),
        sa.Column("expires_at", sa.DateTime, nullable=True),
        sa.Column("scopes", sa.Text, nullable=True),
    )
    op.create_table(
        "provider_webhook_events",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("provider", sa.String(32), nullable=False),
        sa.Column("event_type", sa.String(128), nullable=False),
        sa.Column("payload", sa.Text, nullable=False),
        sa.Column("signature", sa.String(256), nullable=True),
        sa.Column("processed", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("error_msg", sa.Text, nullable=True),
    )


def downgrade():
    op.drop_table("provider_webhook_events")
    op.drop_table("provider_tokens")
