"""Dependency-free regression tests: false completion must never be reported.

These tests validate the touched fail-closed paths, not full production wiring.
"""
from __future__ import annotations

import ast
import os
from pathlib import Path
import runpy
import sys
import types
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


class FakeQuery:
    def __init__(self, rows):
        self.rows = rows

    def filter(self, *args):
        return self

    def order_by(self, *args):
        return self

    def limit(self, *args):
        return self

    def all(self):
        return self.rows


class FakeDb:
    def __init__(self, rows):
        self.rows = rows
        self.commits = 0
        self.rollbacks = 0
        self.closed = False

    def query(self, *args):
        return FakeQuery(self.rows)

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1

    def close(self):
        self.closed = True


class FakeField:
    def __eq__(self, other):
        return True

    def asc(self):
        return self


class FakeOutbox:
    status = FakeField()
    id = FakeField()


class FailClosedSmokeTests(unittest.TestCase):
    def test_daily_ops_cannot_claim_placeholder_success(self):
        module = runpy.run_path(str(ROOT / "services/api/app/cron/daily_ops.py"))
        result = module["run_daily_ops"]()
        self.assertEqual(result["status"], "blocked")
        self.assertFalse(result["verified"])
        self.assertEqual(set(result["checks"]), {"contracts", "payments", "alerts"})
        self.assertTrue(all(not item["verified"] for item in result["checks"].values()))

    def test_job_runner_requires_completion_evidence(self):
        registry = types.ModuleType("app.cron.registry")
        registry.CRON_JOBS = {
            "pretend": {"handler": lambda: {"status": "complete"}, "schedule": "* * * * *", "description": "pretend"},
            "real": {"handler": lambda: {"status": "complete", "verified": True}, "schedule": "* * * * *", "description": "real"},
            "blocked": {"handler": lambda: {"status": "blocked", "verified": False}, "schedule": "* * * * *", "description": "blocked"},
        }
        registry.get_job = lambda name: registry.CRON_JOBS.get(name)
        app = types.ModuleType("app")
        app.__path__ = []
        cron = types.ModuleType("app.cron")
        cron.__path__ = []
        with patch.dict(sys.modules, {"app": app, "app.cron": cron, "app.cron.registry": registry}):
            run_job = runpy.run_path(str(ROOT / "services/api/app/jobs/runner.py"))["run_job"]
        self.assertEqual(run_job("pretend")["status"], "unverified")
        self.assertEqual(run_job("real")["status"], "success")
        self.assertEqual(run_job("blocked")["status"], "blocked")
        self.assertEqual(run_job("missing")["status"], "error")

    def test_reference_outbox_keeps_unsent_messages_queued(self):
        sa = types.ModuleType("sqlalchemy")
        sa.__path__ = []
        sa_orm = types.ModuleType("sqlalchemy.orm")
        sa_orm.Session = object
        app = types.ModuleType("app")
        app.__path__ = []
        core = types.ModuleType("app.core")
        core.__path__ = []
        engines = types.ModuleType("app.core.engines")
        engines.__path__ = []
        guard = types.ModuleType("app.core.engines.dispatch_guard")
        guard.guard_outreach = lambda engine: None
        models = types.ModuleType("app.models")
        models.__path__ = []
        notify = types.ModuleType("app.models.notify")
        notify.Outbox = FakeOutbox
        modules = {
            "sqlalchemy": sa, "sqlalchemy.orm": sa_orm, "app": app,
            "app.core": core, "app.core.engines": engines,
            "app.core.engines.dispatch_guard": guard,
            "app.models": models, "app.models.notify": notify,
        }
        with patch.dict(sys.modules, modules):
            dispatcher = runpy.run_path(
                str(ROOT / "services/api/app/workers/outbox_dispatcher.py")
            )["dispatch_outbox_once"]
        pending = types.SimpleNamespace(status="queued")
        db = FakeDb([pending])
        result = dispatcher(db=db)
        self.assertFalse(result["ok"])
        self.assertEqual(result["error"], "OUTBOX_TRANSPORT_NOT_CONFIGURED")
        self.assertEqual(result["sent"], 0)
        self.assertEqual(pending.status, "queued")
        self.assertEqual(db.commits, 0)

    def test_scheduler_does_not_complete_unexecuted_clone(self):
        path = ROOT / "services/api/app/scheduler/runner.py"
        source = path.read_text(encoding="utf-8")
        ast.parse(source)
        self.assertNotIn("placeholder deploy complete", source)
        self.assertNotIn("mark_clone_status(", source)
        self.assertIn("remain queued", source)

    def test_readiness_does_not_claim_unverified_authority(self):
        module = runpy.run_path(str(ROOT / "services/api/app/heimdall/readiness.py"))
        checks = module["readiness_checks"]()
        self.assertFalse(checks["heimdall_authority_ready"])
        self.assertFalse(checks["bank_account_connected"])
        self.assertFalse(checks["floor_controls_set"])
        self.assertFalse(module["is_ready_to_go_live"]())
        report = module["get_readiness_report"]()
        self.assertFalse(report["ready"])
        self.assertIn("heimdall_authority_ready", report["unverified"])


if __name__ == "__main__":
    unittest.main()
