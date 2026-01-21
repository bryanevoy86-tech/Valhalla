"""Create go-live core tables (system_metadata, go_live_state) + seed row 1

Idempotent migration using CREATE TABLE IF NOT EXISTS so it won't fail if tables
already exist. Also guarantees id=1 rows exist for code that queries WHERE id=1.

Revision ID: 20260121_go_live_core_tables
Revises: 20260113_golive_merge
Create Date: 2026-01-21
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "20260121_go_live_core_tables"
down_revision = "20260113_golive_merge"
branch_labels = None
depends_on = None


def upgrade():
    # Force public schema to avoid search_path surprises
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS public.system_metadata (
            id INTEGER PRIMARY KEY,
            version TEXT NOT NULL DEFAULT '1.0.0',
            backend_complete BOOLEAN NOT NULL DEFAULT FALSE,
            notes TEXT NULL,
            updated_at TIMESTAMP NULL,
            completed_at TIMESTAMP NULL
        );
        """
    )

    op.execute(
        """
        INSERT INTO public.system_metadata (id, version, backend_complete)
        VALUES (1, '1.0.0', FALSE)
        ON CONFLICT (id) DO NOTHING;
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS public.go_live_state (
            id INTEGER PRIMARY KEY,
            go_live_enabled BOOLEAN NOT NULL DEFAULT FALSE,
            kill_switch_engaged BOOLEAN NOT NULL DEFAULT TRUE,
            changed_by TEXT NULL,
            reason TEXT NULL,
            updated_at TIMESTAMP NULL
        );
        """
    )

    op.execute(
        """
        INSERT INTO public.go_live_state (id, go_live_enabled, kill_switch_engaged)
        VALUES (1, FALSE, TRUE)
        ON CONFLICT (id) DO NOTHING;
        """
    )


def downgrade():
    op.execute("DROP TABLE IF EXISTS public.go_live_state;")
    op.execute("DROP TABLE IF EXISTS public.system_metadata;")
