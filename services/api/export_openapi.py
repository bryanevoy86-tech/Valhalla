import json
import sys
import os
import contextlib

# Ensure the current directory is in sys.path
sys.path.append(os.getcwd())

@contextlib.contextmanager
def suppress_stdout_stderr():
    """Context manager to suppress stdout and stderr."""
    with open(os.devnull, "w") as devnull:
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        sys.stdout = devnull
        sys.stderr = devnull
        try:
            yield
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr

try:
    with suppress_stdout_stderr():
        from app.main import app
        schema = app.openapi()
        with open("openapi.json", "w", encoding="utf-8") as f:
            json.dump(schema, f, indent=2)
    
    print("✅ OpenAPI exported")
    print("Path count:", len(schema.get("paths", {})))
    print("Operation count:", sum(len(v) for v in schema.get("paths", {}).values()))
except Exception as e:
    print(f"Error: {e}")
