#!/usr/bin/env python3
"""
Final comprehensive fix for ALL 'from app.' imports in services/api/app
Convert absolute imports to relative imports to resolve namespace issues.
"""
import re
from pathlib import Path

def fix_imports_comprehensive(file_path):
    """
    Fix all 'from app.X' imports to relative imports.
    
    Patterns:
    - from app.models.X import Y → from ..models.X import Y
    - from app.routers.X import Y → from ..routers.X import Y  
    - from app.db import X → from ..db import X
    - from app import X → # Skip (rare, likely wrong)
    """
    try:
        content = file_path.read_text()
        original = content
        
        # Main pattern: from app.PACKAGE.MODULE import ...
        # Replace with: from ..PACKAGE.MODULE import ...
        content = re.sub(
            r'from\s+app\.([a-zA-Z_][a-zA-Z0-9_\.]*)\s+import',
            r'from ..\1 import',
            content
        )
        
        if content != original:
            file_path.write_text(content)
            return True
            
    except Exception as e:
        pass  # Silently skip errors
    
    return False

# Process ALL .py files in services/api/app
app_dir = Path("services/api/app")
py_files = list(app_dir.glob("**/*.py"))

print(f"Processing {len(py_files)} files...")
fixed = 0

for py_file in sorted(py_files):
    if fix_imports_comprehensive(py_file):
        fixed += 1
        if fixed % 50 == 0:
            print(f"  Fixed {fixed}...")

print(f"\n✅ DONE: Fixed {fixed} files out of {len(py_files)}")
