"""market policy tables

Revision ID: 20260113_market_policy
Revises: 20260113_regression_tripwire
"""
from alembic import op
import sqlalchemy as sa

revision = "20260113_market_policy"
down_revision = "20260113_regression_tripwire"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "market_policy",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("province", sa.String(), nullable=False),
        sa.Column("market", sa.String(), nullable=False, server_default=sa.text("'ALL'")),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("rules_json", sa.Text(), nullable=False),
        sa.Column("changed_by", sa.String(), nullable=True),
        sa.Column("reason", sa.String(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("province", "market", name="uq_market_policy_province_market"),
    )

    # Seed ALL-market policies (safe defaults - use string concatenation to avoid % formatting)
    for prov in ["BC","AB","SK","MB","ON","QC","NB","NS","PE","NL","YT","NT","NU"]:
        sql = (
            "INSERT INTO market_policy (province, market, enabled, rules_json, changed_by, reason, updated_at) "
            "VALUES ('" + prov + "','ALL',true,'{\"contact_windows_local\":[],\"channels_allowed\":[\"SMS\",\"CALL\",\"EMAIL\"],\"min_lead_score_to_contact\":0.5}',"
            "'system','Seed safe contact windows',CURRENT_TIMESTAMP)"
        )
        op.execute(sa.text(sql))

def downgrade():
    op.drop_table("market_policy")
