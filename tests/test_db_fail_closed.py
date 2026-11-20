"""Invalid DB driver/configuration may never fall back to in-memory SQLite."""
from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]


class DatabaseFailClosedTests(unittest.TestCase):
    def test_invalid_database_driver_stops_process_instead_of_opening_empty_sqlite(self):
        env = dict(os.environ)
        env.update({
            "DATABASE_URL": "nonexistent-driver://no-db",
            "VALHALLA_JWT_SECRET": "ci-only-not-production",
            "PYTHONPATH": str(ROOT / "services/api"),
        })
        result = subprocess.run(
            [sys.executable, "-c", "from app.core.db import engine; print(engine.url.drivername)"],
            env=env,
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=15,
            check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("refusing in-memory fallback", result.stderr)
        self.assertNotIn("sqlite", result.stdout.lower())


if __name__ == "__main__":
    unittest.main()
