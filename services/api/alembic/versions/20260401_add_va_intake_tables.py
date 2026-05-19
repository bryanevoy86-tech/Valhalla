"""VA Intake tables - VA leads and approval queue (using raw SQL to avoid FK issues)"""

from alembic import op
import sqlalchemy as sa

revision = "va_intake_tables_raw"
down_revision = "007_merge_all_heads_final"  # Attach to main migration chain
branch_labels = None
depends_on = None


def upgrade():
    """Create VA Intake tables using raw SQL to avoid foreign key issues with branched migrations."""
    bind = op.get_bind()
    
    # Create va_leads table
    if not bind.dialect.has_table(bind, "va_leads"):
        op.execute("""
            CREATE TABLE va_leads (
                id SERIAL PRIMARY KEY,
                source_platform VARCHAR(60) NOT NULL,
                source_type VARCHAR(60) NOT NULL,
                source_url VARCHAR(500),
                address VARCHAR(240),
                city VARCHAR(120),
                province VARCHAR(10),
                seller_name VARCHAR(160),
                seller_phone VARCHAR(40),
                seller_email VARCHAR(160),
                asking_price NUMERIC(15, 2),
                raw_text TEXT,
                va_notes TEXT,
                strategy_fit VARCHAR(60),
                submitted_by VARCHAR(80) NOT NULL DEFAULT 'va',
                heimdall_score INTEGER NOT NULL DEFAULT 0,
                risk_level VARCHAR(20) NOT NULL DEFAULT 'high',
                confidence DOUBLE PRECISION NOT NULL DEFAULT 0.0,
                recommended_action VARCHAR(255),
                status VARCHAR(60) NOT NULL DEFAULT 'pending',
                stage VARCHAR(60) NOT NULL DEFAULT 'intake',
                deal_id INTEGER,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                approved_at TIMESTAMP,
                converted_at TIMESTAMP
            )
        """)
        # Create indexes
        op.execute("CREATE INDEX idx_va_leads_created_at ON va_leads(created_at)")
        op.execute("CREATE INDEX idx_va_leads_deal_id ON va_leads(deal_id)")
    
    # Create va_approval_queue table
    if not bind.dialect.has_table(bind, "va_approval_queue"):
        op.execute("""
            CREATE TABLE va_approval_queue (
                id SERIAL PRIMARY KEY,
                entity_type VARCHAR(60) NOT NULL DEFAULT 'lead',
                entity_id INTEGER NOT NULL,
                va_lead_id INTEGER NOT NULL,
                status VARCHAR(60) NOT NULL DEFAULT 'pending',
                recommended_action VARCHAR(255),
                heimdall_score INTEGER,
                risk_level VARCHAR(20),
                assigned_to VARCHAR(80),
                approved_by VARCHAR(80),
                approved_at TIMESTAMP,
                denied_by VARCHAR(80),
                denied_at TIMESTAMP,
                denial_reason TEXT,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # Create indexes
        op.execute("CREATE INDEX idx_va_approval_queue_created_at ON va_approval_queue(created_at)")
        op.execute("CREATE INDEX idx_va_approval_queue_entity_id ON va_approval_queue(entity_id)")
        op.execute("CREATE INDEX idx_va_approval_queue_va_lead_id ON va_approval_queue(va_lead_id)")


def downgrade():
    """Drop VA Intake tables."""
    bind = op.get_bind()
    if bind.dialect.has_table(bind, "va_approval_queue"):
        op.drop_table("va_approval_queue")
    if bind.dialect.has_table(bind, "va_leads"):
        op.drop_table("va_leads")
