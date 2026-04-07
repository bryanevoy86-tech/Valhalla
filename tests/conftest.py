"""Pytest configuration - set up Python path for app imports."""
import sys
import os
from pathlib import Path

print(f"DEBUG: conftest.py loaded from {__file__}")
print(f"DEBUG: Current working directory: {os.getcwd()}")

# Add repo root to sys.path so "from app..." imports work
# This should be FIRST so we import from d:\dev\app
repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root))

print(f"DEBUG: Added to sys.path (position 0): {str(repo_root)}")

# Check if app exists at repo root
if (repo_root / "app").exists():
    print(f"DEBUG: Found app at {repo_root / 'app'}")
    # Check for core_activation
    if (repo_root / "app" / "core_activation").exists():
        print(f"DEBUG: Found core_activation at {repo_root / 'app' / 'core_activation'}")

# Force a clean import cache
for module_name in ['app', 'app.core_activation', 'app.deal_analyzer', 'app.deal_analyzer.service']:
    if module_name in sys.modules:
        del sys.modules[module_name]
        
print("DEBUG: Module cache cleaned and paths configured")
