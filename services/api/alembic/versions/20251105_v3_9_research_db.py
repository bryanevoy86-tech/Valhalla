"""v3.9 - research DB persistence (tags on sources + research_playbooks)"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

revision = "v3_9_research_db"
down_revision = "v3_4_embeddings"
branch_labels = None
depends_on = None


def _table_exists(conn, name: str) -> bool:
    insp = Inspector.from_engine(conn)
    return name in insp.get_table_names()


def _column_exists(conn, table: str, column: str) -> bool:
    insp = Inspector.from_engine(conn)
    cols = [c["name"] for c in insp.get_columns(table)]
    return column in cols


def upgrade():
    bind = op.get_bind()

    # Add tags column to research_sources if missing
    if _table_exists(bind, "research_sources") and not _column_exists(bind, "research_sources", "tags"):
        op.add_column("research_sources", sa.Column("tags", sa.String(length=512), nullable=False, server_default=""))

    # Create research_playbooks if not exists
    if not _table_exists(bind, "research_playbooks"):
        op.create_table(
            "research_playbooks",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("key", sa.String(length=200), nullable=False, unique=True),
            sa.Column("title", sa.String(length=300), nullable=False),
            sa.Column("steps", sa.Text(), nullable=False),
            sa.Column("tags", sa.String(length=512), nullable=False, server_default=""),
            sa.Column("meta", sa.Text(), nullable=False, server_default="{}"),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        )
        op.create_index("ix_research_playbooks_id", "research_playbooks", ["id"]) 
        op.create_index("ix_research_playbooks_key", "research_playbooks", ["key"], unique=True)


def downgrade():
    bind = op.get_bind()
    if _table_exists(bind, "research_playbooks"):
        op.drop_index("ix_research_playbooks_key", table_name="research_playbooks")
        op.drop_index("ix_research_playbooks_id", table_name="research_playbooks")
        op.drop_table("research_playbooks")

    if _table_exists(bind, "research_sources") and _column_exists(bind, "research_sources", "tags"):
        op.drop_column("research_sources", "tags")
