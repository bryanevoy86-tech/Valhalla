"""Pack 85: extend/create integrity_events table to new ledger spec

Revision ID: 85_integrity_events_table
Revises: 84_compliance_signals_table
Create Date: 2025-11-24
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "85_integrity_events_table"
down_revision = "84_compliance_signals_table"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = inspect(bind)
    tables = inspector.get_table_names()
    required = [
        ("source", sa.String(), False),
        ("category", sa.String(), False),
        ("action", sa.String(), False),
        ("entity_type", sa.String(), True),
        ("entity_id", sa.String(), True),
        ("severity", sa.String(), False),
        ("message", sa.String(), False),
        ("payload", sa.Text(), True),
        ("created_at", sa.DateTime(), False),
    ]

    if "integrity_events" not in tables:
        op.create_table(
            "integrity_events",
            sa.Column("id", sa.Integer, primary_key=True),
            *(sa.Column(n, t, nullable=nullable, server_default=None if n != "severity" else sa.text("'info'")) for n, t, nullable in required),
        )
    else:
        existing_cols = {c["name"] for c in inspector.get_columns("integrity_events")}
        for name, coltype, nullable in required:
            if name not in existing_cols:
                op.add_column("integrity_events", sa.Column(name, coltype, nullable=nullable))


def downgrade():
    # Only drop columns we added if they exist; keep legacy columns
    bind = op.get_bind()
    inspector = inspect(bind)
    existing_cols = {c["name"] for c in inspector.get_columns("integrity_events")}
    for col in ["source","category","action","entity_type","entity_id","severity","message","payload","created_at"]:
        if col in existing_cols:
            op.drop_column("integrity_events", col)
    # Do not drop table to preserve legacy data
