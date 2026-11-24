"""Execute known Builder artifacts through the real container runner in CI."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from builder_materialize_review import canonical, sha
from builder_test_review import test_review as run_review
from builder_assignment_worker import tick


class BuilderOfflineRunnerTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.repo = Path(temp.name)
        self.path = "services/api/app/routers/example.py"
        self.base = self.repo / self.path
        self.base.parent.mkdir(parents=True)
        self.base.write_text("VALUE = 1\n")
        suite = self.repo / "services/api/tests"
        suite.mkdir(parents=True)
        (suite / "test_example.py").write_text("""
from pathlib import Path
import os

from app.routers.example import VALUE


def test_candidate_and_isolation():
    assert VALUE == 2
    assert os.getuid() == 65534
    assert set(os.listdir('/sys/class/net')) == {'lo'}
    assert 'BUILDER_HOST_ONLY_SENTINEL' not in os.environ
    assert not Path('/snapshot/services/api/.env').exists()
    assert not Path('/snapshot/.git').exists()
    assert not os.access('/snapshot', os.W_OK)
""")
        (self.repo / "pytest.ini").write_text("[pytest]\npythonpath = services/api\n")
        (self.repo / "services/api/.env").write_text("BUILDER_HOST_ONLY_SENTINEL=ci-fixture\n")
        self.git("init", "-q")
        self.git("add", ".")
        self.git("-c", "user.name=CI", "-c", "user.email=ci@example.invalid", "commit", "-qm", "isolated test")
        self.commit = self.git("rev-parse", "HEAD").strip()
        (self.repo / self.path).write_text("VALUE = 99\n")

    def git(self, *args):
        return subprocess.check_output(["git", "-C", str(self.repo), *args], text=True)

    def review(self, value=2):
        content = f"VALUE = {value}\n"
        bundle = {"task_id": 17, "version": 2, "files": [{
            "path": self.path, "mode": "replace", "content": content,
            "base_sha256": sha(b"VALUE = 1\n"), "content_sha256": sha(content.encode()),
        }]}
        return {"bundle": bundle, "sha256": sha(canonical(bundle)), "status": "review_ready",
                "source_modified": False, "tests_verified": False, "deployed": False}

    def test_unpinned_image_and_stale_review_fail_before_docker(self):
        with self.assertRaisesRegex(ValueError, "pinned"):
            run_review(self.review(), self.repo, self.commit, "python:latest", 30)
        stale = self.review()
        stale["bundle"]["files"][0]["base_sha256"] = sha(b"changed before review")
        stale["sha256"] = sha(canonical(stale["bundle"]))
        with self.assertRaisesRegex(ValueError, "base checksum"):
            run_review(stale, self.repo, self.commit, "sha256:" + "0" * 64, 30)
        self.assertEqual(self.base.read_text(), "VALUE = 99\n")

    @unittest.skipUnless(os.environ.get("BUILDER_OFFLINE_TEST_IMAGE"), "Requires a preloaded offline Builder test image")
    def test_real_offline_test_pass_and_failure(self):
        image = os.environ["BUILDER_OFFLINE_TEST_IMAGE"]
        original = os.environ.get("BUILDER_HOST_ONLY_SENTINEL")
        os.environ["BUILDER_HOST_ONLY_SENTINEL"] = "host-only"
        try:
            review = self.review()
            assignment = {
                "assignment_id": "00000000-0000-0000-0000-000000000001", "lease_id": "fixture-lease",
                "status": "leased", "image_id": image, "base_commit": self.commit, "review": review,
            }
            receipts = []

            class WorkerResponse:
                def __init__(self, data):
                    self.data = data

                def raise_for_status(self):
                    pass

                def json(self):
                    return self.data

            class WorkerTransport:
                def post(self, path, **kwargs):
                    if path.endswith("/claim"):
                        return WorkerResponse(assignment)
                    receipts.append(kwargs["json"])
                    return WorkerResponse({"status": "review_ready"})

            outcome = tick(WorkerTransport(), self.repo, image)
            self.assertEqual(outcome["status"], "review_ready")
            self.assertEqual(len(receipts), 1)
            result = receipts[0]
            self.assertEqual(result["status"], "suite_exited_zero", json.dumps(result))
            self.assertEqual(result["lease_id"], assignment["lease_id"])
            self.assertEqual(result["bundle_sha256"], review["sha256"])
            self.assertFalse(result["release_authorized"])
            failed = run_review(self.review(value=3), self.repo, self.commit, image, 45)
            self.assertEqual(failed["status"], "suite_exited_nonzero", json.dumps(failed))
            self.assertEqual(failed["exit_code"], 1)
            self.assertEqual(self.base.read_text(), "VALUE = 99\n")
        finally:
            if original is None:
                del os.environ["BUILDER_HOST_ONLY_SENTINEL"]
            else:
                os.environ["BUILDER_HOST_ONLY_SENTINEL"] = original


if __name__ == "__main__":
    unittest.main()
