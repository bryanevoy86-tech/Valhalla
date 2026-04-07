"""
Utility to detect and mark existing tables in alembic_version

This script detects tables that exist in the database but aren't marked as 
applied in alembic_version table, and marks them as applied.

This resolves schema state mismatches from partial/failed deployments.
"""

def mark_existing_tables_as_applied(bind):
    """
    Mark tables that exist in the database but aren't in alembic_version as applied.
    
    This handles situations where:
    - A deployment partially succeeded and left tables behind
    - Multiple branches created overlapping schema
    - Alembic version tracking got out of sync with actual schema
    
    Only marks migrations that have already been successfully applied by their code.
    """
    from sqlalchemy import text, inspect
    
    inspector = inspect(bind)
    existing_tables = set(inspector.get_table_names())
    
    if 'alembic_version' not in existing_tables:
        return  # Alembic not initialized yet
    
    # Tables that indicate specific migrations were applied
    migration_table_map = {
        'v3_4_capital_telemetry': ['telemetry_events', 'capital_intake'],
        'v3_5_grants': ['grant_sources', 'grant_records'],
        'v3_6_buyer_matching': ['buyers', 'deal_briefs'],
        # Add more as needed based on which tables each migration creates
    }
    
    # Get already-applied revisions
    result = bind.execute(text("SELECT version FROM alembic_version"))
    applied_revisions = {row[0] for row in result.fetchall()}
    
    # For each migration, check if its tables exist but it's not marked as applied
    for revision_id, table_names in migration_table_map.items():
        if revision_id not in applied_revisions:
            # Check if all this migration's tables exist
            if all(t in existing_tables for t in table_names):
                # Mark as applied
                bind.execute(text(f"INSERT INTO alembic_version (version) VALUES ('{revision_id}')"))
                print(f"Marked {revision_id} as applied (tables {table_names} exist)")
    
    bind.commit()
