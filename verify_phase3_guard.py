#!/usr/bin/env python3
"""Verify Phase 3 guard enforcement."""
import os
import sys
sys.path.insert(0, '.')

from security.phase3_guard import assert_phase3_safety

# Load .env.sandbox
with open('.env.sandbox') as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            k, v = line.split('=', 1)
            os.environ[k] = v

print('[B4] Restoring safe settings and verifying...')
print('  VALHALLA_DRY_RUN=' + os.environ.get('VALHALLA_DRY_RUN'))
print('  VALHALLA_DISABLE_OUTBOUND=' + os.environ.get('VALHALLA_DISABLE_OUTBOUND'))

try:
    assert_phase3_safety()
    print('PASS: Safe settings restored, guard passes')
except Exception as e:
    print('FAIL: ' + str(e))
    sys.exit(1)
