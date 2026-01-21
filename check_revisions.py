import re
import os
import sys

versions_dir = "services/api/alembic/versions"

for f in sorted(os.listdir(versions_dir)):
    if not f.endswith('.py'): 
        continue
    try:
        with open(os.path.join(versions_dir, f)) as fp:
            txt = fp.read()
        m = re.search(r'revision[^=]*=\s*["\']([^"\'\n]+)', txt)
        d = re.search(r'down_revision[^=]*=\s*(.+?)(?:\n|$)', txt)
        if m:
            rev = m.group(1)
            down = d.group(1).strip() if d else 'None'
            if '84' in f or '73' in f or '84' in rev:
                print(f'{f}: {rev} -> {down}')
    except Exception as e:
        pass
