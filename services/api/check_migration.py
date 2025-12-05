from app.core.db import engine
from sqlalchemy import text

with engine.connect() as conn:
    result = conn.execute(text('SELECT version_num FROM alembic_version'))
    version = result.fetchone()[0]
    print(f"Current migration: {version}")
    
    # Verify tables exist
    tables_to_check = ['audit_events', 'governance_decisions', 'document_routes', 'contract_records']
    for table in tables_to_check:
        result = conn.execute(text(f"SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name='{table}')"))
        exists = result.fetchone()[0]
        status = "✓" if exists else "✗"
        print(f"{status} {table}")
