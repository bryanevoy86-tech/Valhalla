#!/usr/bin/env python3
"""Convert from app.X imports to relative imports in routers and services."""
import re
from pathlib import Path

def fix_file(file_path):
    """Convert from app.X imports to relative imports."""
    try:
        content = file_path.read_text(encoding='utf-8')
        original = content
        
        # Convert "from app.X" to "from ..X" (up one level to app)
        # But keep "from app.heimdall" as-is (it's absolute)
        content = re.sub(
            r'^from app\.(?!heimdall)(\w+)',
            r'from ..\1',
            content,
            flags=re.MULTILINE
        )
        
        if content != original:
            file_path.write_text(content, encoding='utf-8')
            return True
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False
    
    return False

# Process both routers and services
target_dirs = [
    Path('services/api/app/routers'),
    Path('services/api/app/services'),
]

total_fixed = 0
for dir_path in target_dirs:
    if not dir_path.exists():
        print(f"Warning: {dir_path} does not exist")
        continue
    
    for py_file in sorted(dir_path.rglob('*.py')):
        if '__pycache__' in str(py_file):
            continue
        
        if fix_file(py_file):
            total_fixed += 1
            print(f"Fixed: {py_file.relative_to('.')}")

print(f"\nTotal files fixed: {total_fixed}")
