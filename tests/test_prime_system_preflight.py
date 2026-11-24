"""System-wide acceptance inventory must remain explicit and non-deceptive."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import runpy
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
MODULE = runpy.run_path(str(ROOT / "scripts/prime_system_preflight.py"))
inspect_matrix = MODULE["inspect_matrix"]
SOURCE_MATRIX = ROOT / "ops/prime_system_integration_matrix.json"


class PrimeSystemPreflightTests(unittest.TestCase):
    def setUp(self):
        self.doc = json.loads(SOURCE_MATRIX.read_text(encoding="utf-8"))

    def test_current_manifest_has_all_source_anchors_and_no_false_production_claims(self):
        report = inspect_matrix(ROOT)
        self.assertTrue(report["ok"], report["issues"])
        self.assertEqual(report["capability_count"], 50)
        self.assertEqual(report["task_count"], 53)
        self.assertEqual(len(report["capability_gap_classification"]), 50)
        self.assertEqual(len(report["remaining_work_counts"]), 7)
        self.assertGreaterEqual(report["remaining_work_counts"]["internal_coding"], report["p0_internal_coding_count"])
        self.assertEqual(report["production_verified_count"], 0)
        self.assertIn("cannot prove", report["warning"])

    def _altered_report(self, alter, alter_handoff=lambda handoff: handoff):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "ops").mkdir()
            handoff = root / MODULE["HANDOFF_PATH"]
            handoff.parent.mkdir()
            handoff.write_text(alter_handoff((ROOT / MODULE["HANDOFF_PATH"]).read_text(encoding="utf-8")),
                               encoding="utf-8")
            doc = copy.deepcopy(self.doc)
            alter(doc)
            (root / "ops/prime_system_integration_matrix.json").write_text(json.dumps(doc), encoding="utf-8")
            return inspect_matrix(root)

    def test_manifest_cannot_claim_live_without_receipt_and_commit(self):
        def alter(doc):
            row = doc["capabilities"][0]
            row["production_verified"] = True
            row["evidence_level"] = "SQLITE_INTEGRATION_TESTED"
        report = self._altered_report(alter)
        self.assertFalse(report["ok"])
        self.assertTrue(any("unsupported live claim" in x for x in report["issues"]))
        self.assertTrue(any("live_receipt" in x for x in report["issues"]))

    def test_unknown_dependencies_are_rejected(self):
        def alter(doc):
            doc["capabilities"][0]["depends_on"].append("imaginary_engine_not_built")
        report = self._altered_report(alter)
        self.assertTrue(any("unknown dependency" in x for x in report["issues"]))

    def test_provider_commissioning_and_qualified_review_cannot_be_collapsed(self):
        def alter(doc):
            work = doc["capabilities"][0]["continuation"]["remaining"]
            del work["qualified_professional_review"]
            work["owner_or_professional_action"] = "Combined older class"
        report = self._altered_report(alter)
        self.assertTrue(any("seven separate remaining-work classes" in issue for issue in report["issues"]))

    def test_open_p0_requires_separate_core_and_business_launch_gates(self):
        def alter(doc):
            runtime = next(row for row in doc["capabilities"] if row["id"] == "runtime_governance")
            del runtime["continuation"]["january_2027_launch_gates"]["first_recurring_cad"]

        report = self._altered_report(alter)
        self.assertTrue(any("runtime_governance: every January launch gate" in issue for issue in report["issues"]))

    def test_tasks_must_match_the_original_acceptance_mapping(self):
        report = self._altered_report(
            lambda doc: None,
            lambda handoff: handoff.replace("| 50 | `loki_independent_challenger` |",
                                            "| 50 | `api_wiring` |"),
        )
        self.assertEqual(report["task_count"], 53)
        self.assertIn("December handoff must map all 53 tasks in order to the acceptance inventory",
                      report["issues"])

    def test_missing_sources_are_not_treated_as_complete(self):
        report = self._altered_report(lambda doc: None)
        self.assertFalse(report["ok"])
        self.assertTrue(any("missing source" in x for x in report["issues"]))


if __name__ == "__main__":
    unittest.main()
