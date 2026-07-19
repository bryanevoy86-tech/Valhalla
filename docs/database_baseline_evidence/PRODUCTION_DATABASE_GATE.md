# Production Database Gate

## Hard Prohibition

No reset, drop, recreate, stamp, or upgrade of any existing database is allowed until that database is positively classified and fully backed up.

## Mandatory Inventory Before Any Action

Collect and review all of the following for each target environment:

1. Database and environment identity
2. alembic_version contents
3. Schemas
4. Tables
5. Row counts
6. Enum and domain types
7. Views
8. Materialized views
9. Functions
10. Triggers
11. Extensions
12. Data classification: test/demo or real/irreplaceable

## Decision Rule

Test/demo only:

Backup first, then a separately approved controlled recreation may be used.

Real or irreplaceable:

No reset and no blind stamp are allowed. A preservation migration plan is required.

## Approval Gate

Proceed only after explicit approval of:

1. Inventory completeness
2. Backup verification
3. Classification outcome
4. Chosen migration strategy
