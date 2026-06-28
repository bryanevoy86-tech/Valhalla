#!/usr/bin/env python3
"""Fix 'from app.*' imports to local imports in services/api/app."""
import re
from pathlib import Path

def fix_imports_in_file(file_path):
    """Replace 'from app.X' imports with local/relative imports where possible."""
    try:
        content = file_path.read_text()
        original_content = content
        
        # Replace 'from app.models.X import Y' -> 'from .X import Y'
        content = re.sub(
            r'from\s+app\.models\.([a-zA-Z_][a-zA-Z0-9_]*)\s+import',
            r'from .\1 import',
            content
        )
        
        # Replace 'from app.models import X' -> 'from . import X'
        content = re.sub(
            r'from\s+app\.models\s+import\s+',
            r'from . import ',
            content
        )
        
        # Replace 'from app.X import Y' -> 'from ..X import Y' (for other packages)
        content = re.sub(
            r'from\s+app\.([a-zA-Z_][a-zA-Z0-9_]*)\s+import',
            r'from ..\1 import',
            content
        )
        
        # Replace 'from app import X' -> comment out (these are probably wrong)
        # Actually just leave them - they're rare
        
        # Only write if there were changes
        if content != original_content:
            file_path.write_text(content)
            return True
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
    return False

# Find and fix all Python files in services/api/app
app_dir = Path("services/api/app")
py_files = list(app_dir.glob("**/*.py"))

print(f"Found {len(py_files)} Python files in services/api/app")
fixed_count = 0

for py_file in py_files:
    if fix_imports_in_file(py_file):
        print(f"✅ Fixed: {py_file}")
        fixed_count += 1

print(f"\n✅ Fixed {fixed_count} files total")
