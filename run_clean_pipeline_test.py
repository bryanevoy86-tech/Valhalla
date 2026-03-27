#!/usr/bin/env python
"""
Full Pipeline - Clean Reset and Complete Test
"""
import sqlite3
from datetime import datetime

conn = sqlite3.connect('valhalla_local.db')
cursor = conn.cursor()

deal_id = 11

print("\n" + "="*80)
print("RESETTING DEAL 11 FOR CLEAN PIPELINE TEST")
print("="*80)

# Reset deal stage
cursor.execute('UPDATE deals SET stage = ? WHERE id = ?', ('preliminary_analysis', deal_id))

# Delete all contracts
cursor.execute('DELETE FROM contracts WHERE deal_id = ?', (deal_id,))

conn.commit()

print(f"✅ Deal  {deal_id} reset to preliminary_analysis")
print(f"✅ All contracts removed")
print(f"✅ Ready for full pipeline test\n")

conn.close()

# Now run the pipeline
import sys
import os
os.environ.setdefault("DATABASE_URL", "sqlite:///valhalla_local.db")
os.environ.setdefault("VALHALLA_JWT_SECRET", "test_secret_key")
os.environ.setdefault("BUILDER_KEY", "test-builder-key-v0.2-verification")

sys.path.insert(0, r'd:\dev\services\api')

# Execute the pipeline verification
exec(open('verify_full_pipeline.py').read())
