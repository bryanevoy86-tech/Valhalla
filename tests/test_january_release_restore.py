"""Rehearse a cold Alembic upgrade and snapshot restore on disposable PostgreSQL."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
from uuid import uuid4
import unittest

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import make_url

ROOT = Path(__file__).resolve().parents[1]
POSTGRES = os.environ.get("FACTORY_TEST_POSTGRES_URL", "")
PRIOR = "20261123_stripe_order_binding"


@unittest.skipUnless(POSTGRES, "Disposable PostgreSQL database not supplied")
class JanuaryReleaseRestoreTests(unittest.TestCase):
    def test_fresh_migrate_restore_snapshot_and_reapply_release(self):
        base = make_url(POSTGRES)
        self.assertEqual((base.get_backend_name(), base.host, base.port, base.database),
                         ("postgresql", "127.0.0.1", 5432, "valhalla_factory_ci"))
        self.assertFalse(base.query, "Connection options are prohibited for this rehearsal")

        ident = uuid4().hex[:12]
        candidate, checkpoint, restored = (f"january_{ident}_{kind}" for kind in ("candidate", "checkpoint", "restored"))
        administration = create_engine(base, isolation_level="AUTOCOMMIT")
        self.addCleanup(administration.dispose)

        def drop(name):
            with administration.connect() as conn:
                conn.execute(text(f'DROP DATABASE "{name}"'))

        def create(name, template=None):
            with administration.connect() as conn:
                suffix = f' TEMPLATE "{template}"' if template else ""
                conn.execute(text(f'CREATE DATABASE "{name}"' + suffix))
            self.addCleanup(drop, name)
            return base.set(database=name)

        def migrate(database, revision):
            env = {**os.environ, "DATABASE_URL": database.render_as_string(hide_password=False),
                   "VALHALLA_JWT_SECRET": "isolated-january-migration", "PYTHONPATH": "services/api"}
            result = subprocess.run([sys.executable, "-m", "alembic", "upgrade", revision],
                                    cwd=ROOT, env=env, capture_output=True, text=True, timeout=90)
            self.assertEqual(result.returncode, 0, result.stderr[-8000:])

        def observe(database, *, marker=None):
            engine = create_engine(database)
            try:
                with engine.begin() as conn:
                    if marker:
                        conn.execute(text(
                            """INSERT INTO source_registry_items
                               (source_id, canonical_name, source_type, data_class, terminal_state)
                               VALUES (:marker, 'Isolated rehearsal', 'test', 'synthetic', 'INACTIVE')"""
                        ), {"marker": marker})
                    return (conn.scalar(text("SELECT version_num FROM alembic_version")),
                            inspect(conn).has_table("stripe_saas_bindings"),
                            "decision_sha256" in {column["name"] for column in inspect(conn).get_columns("loki_reconsiderations")},
                            conn.execute(text("SELECT source_id FROM source_registry_items ORDER BY source_id")).scalars().all())
            finally:
                engine.dispose()

        candidate_url = create(candidate)
        migrate(candidate_url, PRIOR)
        saved = observe(candidate_url, marker="pre-release")
        self.assertEqual(saved, (PRIOR, False, False, ["pre-release"]))
        create(checkpoint, template=candidate)

        migrate(candidate_url, "head")
        candidate_state = observe(candidate_url, marker="candidate-only")
        self.assertNotEqual(candidate_state[0], PRIOR)
        self.assertTrue(candidate_state[1])
        self.assertTrue(candidate_state[2])
        self.assertEqual(candidate_state[3], ["candidate-only", "pre-release"])

        restored_url = create(restored, template=checkpoint)
        self.assertEqual(observe(restored_url), saved)
        migrate(restored_url, "head")
        self.assertEqual(observe(restored_url), (candidate_state[0], True, True, ["pre-release"]))
