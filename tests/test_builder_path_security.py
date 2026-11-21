"""Builder file boundary regression tests; no project dependencies required."""
from __future__ import annotations

from pathlib import Path
import runpy
import tempfile
import unittest

POLICY = Path(__file__).resolve().parents[1] / "services/api/app/core/builder_path_policy.py"
MOD = runpy.run_path(str(POLICY))
resolve = MOD["resolve_builder_path"]
Rejected = MOD["BuilderPathRejected"]
ALLOW = ["services/api/app/routers", "services/api/app/models"]


class BuilderPathSecurityTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.root = Path(self.folder.name) / "repo"
        (self.root / "services/api/app/routers").mkdir(parents=True)
        (self.root / "services/api/app/models").mkdir(parents=True)

    def tearDown(self):
        self.folder.cleanup()

    def test_legitimate_router_path_resolves_under_repo(self):
        target = resolve("services/api/app/routers/safe.py", ALLOW, self.root)
        self.assertEqual(target, self.root / "services/api/app/routers/safe.py")

    def test_legitimate_windows_style_separator_normalizes_safely(self):
        result = resolve(r"services\api\app\models\widget.py", ALLOW, self.root)
        self.assertEqual(result, self.root / "services/api/app/models/widget.py")

    def test_traversal_and_absolute_paths_denied(self):
        for path in [
            "services/api/app/routers/../../../../../../etc/passwd",
            "services/api/app/routers/../models/unsafe.py",
            "../services/api/app/routers/x.py",
            "/etc/passwd",
            r"C:\Windows\system.ini",
            r"\\server\share\file.py",
            "services/api/app/routers/./x.py",
            "services/api/app/routers//x.py",
            "services/api/app/routers/\x00bad.py",
            "services/api/app/routers",
            "services/api/app/routes/x.py",
            "services/api/app/models-extra/x.py",
        ]:
            with self.subTest(path=path), self.assertRaises(Rejected):
                resolve(path, ALLOW, self.root)

    def test_symlink_escape_denied(self):
        outside = Path(self.folder.name) / "outside"
        outside.mkdir()
        link = self.root / "services/api/app/routers/unsafe"
        link.symlink_to(outside, target_is_directory=True)
        with self.assertRaises(Rejected):
            resolve("services/api/app/routers/unsafe/escape.py", ALLOW, self.root)

    def test_symlink_allowlist_escapes_repo_denied(self):
        outside = Path(self.folder.name) / "outside"
        outside.mkdir(exist_ok=True)
        symlink = self.root / "untrusted"
        symlink.symlink_to(outside, target_is_directory=True)
        with self.assertRaises(Rejected):
            resolve("untrusted/x.py", ["untrusted"], self.root)

    def test_no_relative_assumptions_about_process_working_dir(self):
        result = resolve("services/api/app/routers/pilot.py", ALLOW, self.root)
        self.assertEqual(result, self.root / "services/api/app/routers/pilot.py")

    def test_repo_integrity_gate_rejects_blank_malformed_inputs(self):
        for raw in ["", " ", " services/api/app/routers/x.py ", "\n", "\t"]:
            with self.subTest(raw=raw), self.assertRaises(Rejected):
                resolve(raw, ALLOW, self.root)


if __name__ == "__main__":
    unittest.main()
