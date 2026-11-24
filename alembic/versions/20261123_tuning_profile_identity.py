"""Keep named tuning profiles unique in the canonical rule table."""

from alembic import op
from sqlalchemy import text

revision = "20261123_tuning_profile_identity"
down_revision = "20261123_specialist_backlog"
branch_labels = None
depends_on = None


def upgrade():
    predicate = text("rule_type = 'profile'")
    op.create_index("uq_tuning_profile_name", "tuning_rules", ["tenant_id", "name"],
                    unique=True, postgresql_where=predicate, sqlite_where=predicate)


def downgrade():
    op.drop_index("uq_tuning_profile_name", table_name="tuning_rules")
