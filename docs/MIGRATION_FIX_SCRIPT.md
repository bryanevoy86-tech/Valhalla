# SQLite Migration Fix - Comprehensive Guide

## Problem
20+ migration files use PostgreSQL-specific DateTime syntax that fails on SQLite:
- `sa.DateTime(timezone=True)` - SQLite doesn't support timezone
- `server_default=sa.text("now()")` - SQLite doesn't have now() function

## Solution Pattern
Replace all instances of:
```python
sa.Column("COLUMN_NAME", sa.DateTime(timezone=True), server_default=sa.text("now()"))
```

With SQLite-compatible version:
```python
sa.Column("COLUMN_NAME", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"))
```

## Files Fixed (✅)
1. `a10f5d7c3e01_pack_110_empire_snapshots.py`
2. `f24e0f123456_pack_124_knowledge_sources.py`
3. `f23d9e0f1234_pack_123_ai_training_jobs.py`
4. `f22c8d9e0f12_pack_122_legacy_clone_profiles.py`

## Files Remaining to Fix (❌)
1. `b21e6f8a4c12_pack_111_legacy_performance.py`
   - Replace 1 instance: line ~40

2. `f21b7c8d9e01_pack_121_whole_life_policies.py`
   - Replace 2 instances: last_updated, created_at

3. `f20a6b7c8d90_pack_120_bahamas_vault.py`
   - Replace 2 instances: updated_at, created_at

4. `f19e5f6a7b89_pack_119_shield_profiles.py`
   - Replace 2 instances: created_at, updated_at

5. `f18d4e5f6a78_pack_118_tax_risk_profiles.py`
   - Replace 2 instances: created_at, updated_at

6. `f17c3d4e5f67_pack_117_legal_profiles.py`
   - Replace 2 instances: created_at, updated_at

7. `c32f7a9b5d23_pack_112_brrrr_zones.py`
   - Replace 2 instances: created_at, updated_at

8. `f16b2d3e4f56_pack_116_tenants_leases_rent_payments.py`
   - Replace 3 instances: 3 tables with created_at

## Batch Fix Command (PowerShell)
```powershell
cd d:\dev\alembic\versions

# Pattern to replace
$pattern = 'sa\.DateTime\(timezone=True\), server_default=sa\.text\("now\(\)"\)'
$replacement = 'sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")'

# Fix all migration files
Get-ChildItem -Filter "*pack_11[0-9]*.py", "*pack_12[0-4]*.py" | ForEach-Object {
    $content = Get-Content $_.FullName -Raw
    if ($content -match $pattern) {
        $new_content = $content -replace $pattern, $replacement
        Set-Content -Path $_.FullName -Value $new_content
        Write-Host "Fixed: $($_.Name)"
    }
}
```

## Python Script (Alternative)
```python
import re
import os
from pathlib import Path

# Pattern and replacement
pattern = r"sa\.DateTime\(timezone=True\), server_default=sa\.text\(\"now\(\)\"\)"
replacement = 'sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")'

# Fix all migration files
versions_dir = Path("alembic/versions")
for migration_file in versions_dir.glob("*_pack_*.py"):
    content = migration_file.read_text()
    
    if re.search(pattern, content):
        new_content = re.sub(pattern, replacement, content)
        migration_file.write_text(new_content)
        print(f"Fixed: {migration_file.name}")
        
print("All migrations fixed!")
```

## Verification
After applying all fixes:
```bash
cd d:\dev
alembic upgrade head
```

Should run without SQLite syntax errors.
