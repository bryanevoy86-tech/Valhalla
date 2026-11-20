"""Replay new Factory + JWT revocation migrations on disposable PostgreSQL.

Never run on a live Render database. This test explicitly restricts the URL
to a local CI database and preserves a preexisting media-content record.
"""
from __future__ import annotations

import importlib.util
import os
from pathlib import Path
import unittest
from unittest.mock import patch

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import IntegrityError

ROOT = Path(__file__).resolve().parents[1]
url = os.environ.get("FACTORY_TEST_POSTGRES_URL", "")
if url and not url.endswith("@127.0.0.1:5432/valhalla_factory_ci"):
    raise RuntimeError("PostgreSQL migration test refuses non-disposable database URL")


def load(path: str):
    source = ROOT / path
    name = source.stem
    spec = importlib.util.spec_from_file_location(name, source)
    if not spec or not spec.loader:
        raise RuntimeError(f"Could not load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


FACTORY = load("alembic/versions/20261119_factory_legacy_work_schema.py")
REVOCATION = load("alembic/versions/20261119_persistent_auth_revocation.py")
DEAL_LINKS = load("alembic/versions/20261120_deal_brief_links.py")
FREEZE_EVIDENCE = load("alembic/versions/20261120_freeze_event_evidence.py")
CLOSER = load("alembic/versions/20261120_closer_sessions.py")
BUYER_CLAIM = load("alembic/versions/20261120_buyer_claim_expiry.py")
LOKI_RECEIPTS = load("alembic/versions/20261120_loki_review_receipts.py")


SPECIALIST = load("alembic/versions/20261120_specialist_schedules.py")
PRODUCT = load("alembic/versions/20261120_product_artifacts.py")


@unittest.skipUnless(url, "Disposable PostgreSQL database not supplied")
class PostgresMigrationChainTests(unittest.TestCase):
    def test_migrations_preserve_baseline_and_repeat_without_duplicate_tables(self):
        engine = create_engine(url, pool_pre_ping=True)
        try:
            with engine.begin() as conn:
                conn.execute(text("CREATE TABLE media_contents (id INTEGER PRIMARY KEY, title TEXT NOT NULL)"))
                conn.execute(text("INSERT INTO media_contents(id,title) VALUES(9,'keep preexisting content')"))
                operations = Operations(MigrationContext.configure(conn))
                for module in (FACTORY, REVOCATION):
                    with (
                        patch.object(module.op, "get_bind", return_value=conn),
                        patch.object(module.op, "create_table", side_effect=operations.create_table),
                        patch.object(module.op, "create_index", side_effect=operations.create_index),
                    ):
                        module.upgrade()
                        module.upgrade()
                tables = set(inspect(conn).get_table_names())
                for expected in (
                    "legacy_instance_registry_items",
                    "legacy_instance_work_items",
                    "legacy_orchestration_events",
                    "auth_revoked_access_tokens",
                ):
                    self.assertIn(expected, tables)
                self.assertEqual(
                    conn.execute(text("SELECT title FROM media_contents WHERE id=9")).scalar_one(),
                    "keep preexisting content",
                )
                indexes = {
                    item["name"] for item in inspect(conn).get_indexes("auth_revoked_access_tokens")
                }
                self.assertIn("ix_auth_revoked_access_tokens_jti_sha256", indexes)
        finally:
            engine.dispose()

        # The dedicated Postgres service is discarded after this job.
        # Never drop a DB simply because this schema test completed.


    def test_deal_brief_link_migration_preserves_existing_rows_and_rejects_wrong_links(self):
        engine = create_engine(url, pool_pre_ping=True)
        try:
            # Roll back this test's DDL so the shared disposable CI database
            # remains usable by the migration above, regardless of test order.
            with engine.connect() as conn:
                transaction = conn.begin()
                try:
                    conn.execute(text("CREATE TABLE deals (id INTEGER PRIMARY KEY)"))
                    conn.execute(text("CREATE TABLE deal_briefs (id INTEGER PRIMARY KEY)"))
                    conn.execute(text("INSERT INTO deals (id) VALUES (7), (8)"))
                    conn.execute(text("INSERT INTO deal_briefs (id) VALUES (11), (7)"))
                    op = Operations(MigrationContext.configure(conn))
                    with patch.object(DEAL_LINKS, "op", op):
                        DEAL_LINKS.upgrade()
                        self.assertEqual(conn.execute(text("SELECT COUNT(*) FROM deal_brief_links")).scalar_one(), 0)
                        conn.execute(text("INSERT INTO deal_brief_links VALUES (7, 11)"))
                        for statement in (
                            "INSERT INTO deal_brief_links VALUES (8, 11)",
                            "INSERT INTO deal_brief_links VALUES (8, 12345)",
                        ):
                            with self.assertRaises(IntegrityError), conn.begin_nested():
                                conn.execute(text(statement))
                        DEAL_LINKS.downgrade()
                    self.assertEqual(conn.execute(text("SELECT brief_id FROM deal_brief_links")).scalar_one(), 11)
                    self.assertEqual(conn.execute(text("SELECT COUNT(*) FROM deals")).scalar_one(), 2)
                    self.assertEqual(conn.execute(text("SELECT COUNT(*) FROM deal_briefs")).scalar_one(), 2)
                finally:
                    transaction.rollback()
        finally:
            engine.dispose()


    def test_freeze_evidence_migration_preserves_an_existing_freeze(self):
        engine = create_engine(url, pool_pre_ping=True)
        try:
            with engine.connect() as conn:
                transaction = conn.begin()
                try:
                    conn.execute(text("CREATE TABLE freeze_events (id INTEGER PRIMARY KEY, notes VARCHAR, completed_at TIMESTAMP)"))
                    conn.execute(text("INSERT INTO freeze_events VALUES (1, 'existing review', NULL)"))
                    with patch.object(FREEZE_EVIDENCE, "op", Operations(MigrationContext.configure(conn))):
                        FREEZE_EVIDENCE.upgrade()
                        conn.execute(text("UPDATE freeze_events SET severity='warn', reason='Policy review' WHERE id=1"))
                        FREEZE_EVIDENCE.downgrade()
                    self.assertEqual(
                        conn.execute(text("SELECT notes, severity, reason FROM freeze_events WHERE id=1")).one(),
                        ("existing review", "warn", "Policy review"),
                    )
                finally:
                    transaction.rollback()
        finally:
            engine.dispose()


    def test_closer_and_buyer_claim_migrations_preserve_existing_records(self):
        engine = create_engine(url, pool_pre_ping=True)
        try:
            with engine.connect() as conn:
                transaction = conn.begin()
                try:
                    conn.execute(text("CREATE TABLE deals (id INTEGER PRIMARY KEY)"))
                    conn.execute(text("CREATE TABLE deal_buyer_matches (id INTEGER PRIMARY KEY)"))
                    conn.execute(text("INSERT INTO deals VALUES (7)"))
                    conn.execute(text("INSERT INTO deal_buyer_matches VALUES (9)"))
                    for module in (CLOSER, BUYER_CLAIM):
                        with patch.object(module, "op", Operations(MigrationContext.configure(conn))):
                            module.upgrade()
                    conn.execute(text("""
                        INSERT INTO closer_sessions (id, deal_id, script, last_section, section_notes)
                        VALUES ('session', 7, '{}', 'rapport', '[]')
                    """))
                    conn.execute(text("UPDATE deal_buyer_matches SET claim_expires_at=now() WHERE id=9"))
                    self.assertEqual(conn.execute(text("SELECT deal_id FROM closer_sessions")).scalar_one(), 7)
                    self.assertIsNotNone(conn.execute(text("SELECT claim_expires_at FROM deal_buyer_matches WHERE id=9")).scalar_one())
                finally:
                    transaction.rollback()
        finally:
            engine.dispose()


    def test_loki_receipt_migration_retains_old_reviews_without_trusting_them(self):
        engine = create_engine(url, pool_pre_ping=True)
        try:
            with engine.connect() as conn:
                transaction = conn.begin()
                try:
                    conn.execute(text("CREATE TABLE loki_reviews (id UUID PRIMARY KEY)"))
                    conn.execute(text("INSERT INTO loki_reviews VALUES ('00000000-0000-0000-0000-000000000001')"))
                    with patch.object(LOKI_RECEIPTS, "op", Operations(MigrationContext.configure(conn))):
                        LOKI_RECEIPTS.upgrade()
                    self.assertIsNone(conn.execute(text("SELECT artifact_sha256 FROM loki_reviews")).scalar_one())
                    self.assertEqual(conn.execute(text("SELECT COUNT(*) FROM loki_independent_receipts")).scalar_one(), 0)
                    self.assertEqual(conn.execute(text("SELECT COUNT(*) FROM loki_reconsiderations")).scalar_one(), 0)
                    self.assertTrue(any(row["unique"] for row in inspect(conn).get_indexes("loki_reviews")))
                finally:
                    transaction.rollback()
        finally:
            engine.dispose()


    def test_specialist_schedule_migration_and_exclusive_due_slot(self):
        engine = create_engine(url, pool_pre_ping=True)
        try:
            with engine.begin() as connection:
                with patch.object(SPECIALIST.op, "create_table", side_effect=Operations(
                    MigrationContext.configure(connection)
                ).create_table), patch.object(SPECIALIST.op, "create_index", side_effect=Operations(
                    MigrationContext.configure(connection)
                ).create_index):
                    SPECIALIST.upgrade()
                connection.execute(text("""
                    INSERT INTO prime_specialist_schedules
                        (id, request, cadence_seconds, next_due_at, expires_at, state)
                    VALUES ('00000000-0000-0000-0000-000000000001', '{}', 300,
                            now() - interval '1 minute', now() + interval '1 hour', 'active')
                """))
            claim = text("""
                SELECT id FROM prime_specialist_schedules
                WHERE state = 'active' AND next_due_at <= now() AND expires_at > now()
                ORDER BY next_due_at, id LIMIT 1 FOR UPDATE SKIP LOCKED
            """)
            with engine.begin() as first, engine.connect() as second:
                self.assertIsNotNone(first.execute(claim).scalar_one())
                self.assertIsNone(second.execute(claim).scalar_one_or_none())
                first.execute(text("UPDATE prime_specialist_schedules SET next_due_at = now() + interval '5 minutes'"))
            with engine.connect() as restarted:
                self.assertIsNone(restarted.execute(claim).scalar_one_or_none())
                self.assertIn("ix_prime_specialist_due", {
                    index["name"] for index in inspect(restarted).get_indexes("prime_specialist_schedules")
                })
        finally:
            with engine.begin() as connection:
                connection.execute(text("DROP TABLE IF EXISTS prime_specialist_schedules"))
            engine.dispose()


    def test_product_artifact_migration_retains_binary_version_and_scope(self):
        engine = create_engine(url, pool_pre_ping=True)
        try:
            with engine.connect() as connection:
                transaction = connection.begin()
                try:
                    operations = Operations(MigrationContext.configure(connection))
                    with patch.object(PRODUCT, "op", operations):
                        PRODUCT.upgrade()
                        insert = text("""
                            INSERT INTO product_artifacts (
                                id, legacy_instance_id, business_id, engine_id, jurisdiction, product_id,
                                version, media_type, sha256, data, rights_reference, created_at
                            ) VALUES (
                                :id, 'legacy', 'business', 'engine', :jurisdiction, 'product',
                                1, 'text/plain', :digest, :data, 'internal-rights/proof', now()
                            )
                        """)
                        asset = {"id": "00000000-0000-0000-0000-000000000001",
                                 "jurisdiction": "CA-MB", "digest": "1" * 64, "data": b"actual\x00bytes"}
                        connection.execute(insert, asset)
                        other = {**asset, "id": "00000000-0000-0000-0000-000000000002"}
                        with self.assertRaises(IntegrityError), connection.begin_nested():
                            connection.execute(insert, other)
                        with self.assertRaises(IntegrityError), connection.begin_nested():
                            connection.execute(insert, {**other, "jurisdiction": "CA-ON", "data": b""})
                        connection.execute(insert, {**other, "jurisdiction": "CA-ON"})
                        PRODUCT.downgrade()
                    recovered = connection.execute(text(
                        "SELECT data FROM product_artifacts WHERE jurisdiction='CA-MB'"
                    )).scalar_one()
                    self.assertEqual(bytes(recovered), asset["data"])
                finally:
                    transaction.rollback()
        finally:
            engine.dispose()


if __name__ == "__main__":
    unittest.main()
