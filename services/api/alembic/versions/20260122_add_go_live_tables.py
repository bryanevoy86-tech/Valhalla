"""Add go-live tables (system_metadata, go_live_state) + seed rows.

This fixes:
- psycopg2.errors.UndefinedTable: relation "system_metadata" does not exist
- transaction aborted cascade after the first failure
"""

from alembic import op
import sqlalchemy as sa

# IMPORTANT:
# Replace DOWN_REVISION with your current single head revision.
# Run locally: alembic heads
# Use the one head revision you see.
revision = "20260122_add_go_live_tables"
down_revision = "20260113_golive_merge"
branch_labels = None
depends_on = None


def upgrade():
    # Use raw SQL with IF NOT EXISTS for idempotency in prod
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS system_metadata (
            id INTEGER PRIMARY KEY,
            version VARCHAR NOT NULL DEFAULT '1.0.0',
            backend_complete BOOLEAN NOT NULL DEFAULT FALSE,
            notes VARCHAR NULL,
            updated_at TIMESTAMP NULL,
            completed_at TIMESTAMP NULL
        );
        """
    )

    op.execute(
        """
        INSERT INTO system_metadata (id, version, backend_complete)
        VALUES (1, '1.0.0', FALSE)
        ON CONFLICT (id) DO NOTHING;
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS go_live_state (
            id INTEGER PRIMARY KEY,
            go_live_enabled BOOLEAN NOT NULL DEFAULT FALSE,
            kill_switch_engaged BOOLEAN NOT NULL DEFAULT TRUE,
            changed_by VARCHAR NULL,
            reason VARCHAR NULL,
            updated_at TIMESTAMP NULL
        );
        """
    )

    op.execute(
        """
        INSERT INTO go_live_state (id, go_live_enabled, kill_switch_engaged)
        VALUES (1, FALSE, TRUE)
        ON CONFLICT (id) DO NOTHING;
        """
    )


def downgrade():
    op.execute("DROP TABLE IF EXISTS go_live_state;")
    op.execute("DROP TABLE IF EXISTS system_metadata;")
