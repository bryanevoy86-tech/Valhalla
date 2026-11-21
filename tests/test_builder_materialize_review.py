"""Dependency-free Builder materialization acceptance tests."""
from __future__ import annotations
import copy
import json
from pathlib import Path
import runpy
import subprocess
import tempfile
import unittest

MOD = runpy.run_path(str(Path(__file__).resolve().parents[1] / "scripts/builder_materialize_review.py"))
materialize, sha, canonical = (MOD[name] for name in ("materialize", "sha", "canonical"))


class BuilderMaterializeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.base = root / "base"
        self.output = root / "output"
        self.output.mkdir()
        self.path = "services/api/app/routers/example.py"
        self.source = self.base / self.path
        self.source.parent.mkdir(parents=True)
        self.source.write_bytes(b"VALUE = 1\n")
        self.row = {"path": self.path, "mode": "replace",
                    "base_sha256": sha(self.source.read_bytes()),
                    "content": "VALUE = 2\n", "content_sha256": sha(b"VALUE = 2\n")}

    def review(self, rows=None):
        bundle = {"version": 2, "task_id": 5, "files": [self.row] if rows is None else rows}
        return {"bundle": bundle, "sha256": sha(canonical(bundle)), "status": "review_ready",
                "source_modified": False, "tests_verified": False, "deployed": False}

    def test_materializes_exact_bytes_without_writing_base_or_executing_code(self):
        dangerous_if_executed = "raise RuntimeError('must not execute')\n"
        row = dict(self.row, content=dangerous_if_executed,
                   content_sha256=sha(dangerous_if_executed.encode()))
        review = self.review([row])
        out = materialize(review, self.base, self.output)
        self.assertEqual((out / "files" / self.path).read_text(), dangerous_if_executed)
        self.assertEqual(self.source.read_bytes(), b"VALUE = 1\n")
        receipt = json.loads((out / "receipt.json").read_text())
        self.assertEqual(receipt["bundle_sha256"], review["sha256"])
        self.assertEqual(receipt["files"][0]["validation"], "python_syntax_only")
        for flag in ("source_modified", "tests_verified", "code_executed", "committed", "deployed"):
            self.assertFalse(receipt[flag])
        other = materialize(review, self.base, self.output)
        self.assertNotEqual(other, out)

    def test_handoff_binds_exact_git_base_and_passing_receipt(self):
        def git(*args):
            return subprocess.check_output(["git", "-C", str(self.base), *args], text=True, stderr=subprocess.DEVNULL).strip()

        git("init", "-q")
        git("add", ".")
        git("-c", "user.name=Builder Fixture", "-c", "user.email=fixture@example.invalid", "commit", "-qm", "base")
        base = git("rev-parse", "HEAD")
        review = self.review()
        receipt = {"base_commit": base, "bundle_sha256": review["sha256"], "status": "suite_exited_zero",
                   "suite": "services/api/tests", "exit_code": 0, "source_modified": False,
                   "committed": False, "deployed": False, "release_authorized": False}
        packet = {"base_commit": base, "bundle_sha256": review["sha256"], "review": review,
                  "runner_receipt": receipt, "test_receipt_sha256": sha(canonical(receipt)),
                  "submission_state": "PREPARED_FOR_OWNER_REVIEW", "github_write_authorized": False,
                  "release_authorized": False}
        packet["handoff_sha256"] = sha(canonical(packet))
        with self.assertRaises(ValueError):
            MOD["materialize_handoff"]({**packet, "test_receipt_sha256": "0" * 64}, self.base, self.output)
        output = MOD["materialize_handoff"](packet, self.base, self.output)
        self.assertEqual((output / "files" / self.path).read_bytes(), b"VALUE = 2\n")
        git("-c", "user.name=Builder Fixture", "-c", "user.email=fixture@example.invalid", "commit",
            "--allow-empty", "-qm", "moved")
        with self.assertRaises(ValueError):
            MOD["materialize_handoff"](packet, self.base, self.output)
        self.assertEqual(self.source.read_bytes(), b"VALUE = 1\n")
        self.assertEqual(list(self.output.iterdir()), [output])

    def test_stale_base_rejects_entire_batch(self):
        self.source.write_bytes(b"VALUE = 3\n")
        with self.assertRaises(ValueError):
            materialize(self.review(), self.base, self.output)
        self.assertEqual(list(self.output.iterdir()), [])

    def test_malformed_or_tampered_review_rejected(self):
        review = copy.deepcopy(self.review())
        review["bundle"]["files"][0]["content"] = "VALUE = 999\n"
        with self.assertRaises(ValueError):
            materialize(review, self.base, self.output)
        review = dict(self.review(), tests_verified=True)
        with self.assertRaises(ValueError):
            materialize(review, self.base, self.output)
        self.assertEqual(list(self.output.iterdir()), [])

    def test_duplicate_and_escape_rejected(self):
        for rows in ([self.row, self.row],
                     [dict(self.row, path="../outside.py")]):
            with self.subTest(rows=rows), self.assertRaises(ValueError):
                materialize(self.review(rows), self.base, self.output)
        self.assertEqual(list(self.output.iterdir()), [])

    def test_invalid_code_rejects_batch_before_any_output(self):
        invalid = "def broken(:\n"
        target = "services/api/app/routers/new.py"
        row = {"path": target, "mode": "add", "content": invalid,
               "base_sha256": None, "content_sha256": sha(invalid.encode())}
        with self.assertRaises(SyntaxError):
            materialize(self.review([self.row, row]), self.base, self.output)
        self.assertEqual(list(self.output.iterdir()), [])
        self.assertFalse((self.base / target).exists())

    def test_output_inside_base_rejected(self):
        with self.assertRaises(ValueError):
            materialize(self.review(), self.base, self.source.parent)

    def test_new_file_materialized_without_creating_it_in_base(self):
        path = "services/api/app/routers/fresh.py"
        content = "NEW = True\n"
        row = {"path": path, "mode": "add", "content": content,
               "base_sha256": None, "content_sha256": sha(content.encode())}
        out = materialize(self.review([row]), self.base, self.output)
        self.assertEqual((out / "files" / path).read_text(), content)
        self.assertFalse((self.base / path).exists())


if __name__ == "__main__":
    unittest.main()
