"""Exercise the documented Docker Command without contacting hosted resources."""
import os
from pathlib import Path
import re
import shlex
import subprocess
import tempfile
import unittest


SHEET = Path(__file__).resolve().parents[1] / "docs/VALHALLA_COMMERCIAL_COMMISSIONING_SHEET.md"
EXPECTED_SHA = "5140c01ec5516ad72a48a4860b4cdb9b3d399412"
FIXTURE_ORIGIN = "https://isolated-stage.example.invalid"

FAKE_PYTHON = """#!/bin/sh
case "$*" in
    'scripts/staging_preflight.py api')
        echo preflight >> "$TRACE"
        exit "${PREFLIGHT_CODE:-0}"
        ;;
    'scripts/render_migrate.py')
        echo migrate >> "$TRACE"
        exit "${MIGRATION_CODE:-0}"
        ;;
    '-m alembic -c '*'/alembic.ini current')
        echo current >> "$TRACE"
        echo "${MIGRATION_HEAD:-20261123_mimir_registry (head)}"
        exit "${ALEMBIC_CODE:-0}"
        ;;
    'start.py')
        echo api >> "$TRACE"
        exit "${APP_CODE:-0}"
        ;;
esac
exit 99
"""


class StagingDockerCommandTests(unittest.TestCase):
    def setUp(self):
        blocks = re.findall(r"^```bash\n(/bin/bash [^\n]+)\n```$", SHEET.read_text(), re.MULTILINE)
        self.assertEqual(len(blocks), 1)
        self.command = blocks[0]
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        root = Path(self.temp_dir.name)
        (root / "services/api").mkdir(parents=True)
        stub = root / "python"
        stub.write_text(FAKE_PYTHON)
        stub.chmod(0o700)
        self.trace = root / "trace"
        self.command = re.sub(r"(?<![\w/])/app(?=[ /])", shlex.quote(str(root)), self.command)
        self.env = {
            "PATH": f"{root}:/usr/bin:/bin",
            "TRACE": str(self.trace),
            "RENDER_GIT_COMMIT": EXPECTED_SHA,
            "RENDER_EXTERNAL_URL": FIXTURE_ORIGIN,
            "VALHALLA_STAGING_API_ORIGIN": FIXTURE_ORIGIN,
        }

    def run_command(self, expected_exit, expected_trace, *, shell=False, **changes):
        self.trace.unlink(missing_ok=True)
        env = {**self.env, **changes}
        args = ["/bin/sh", "-c", self.command] if shell else shlex.split(self.command)
        result = subprocess.run(args, env=env, capture_output=True, text=True, timeout=5)
        self.assertEqual(result.returncode, expected_exit, result.stderr)
        observed = self.trace.read_text().splitlines() if self.trace.exists() else []
        self.assertEqual(observed, expected_trace)

    def test_shell_and_argv_parsers_run_one_command_body(self):
        self.assertEqual(shlex.split(self.command)[:5], ["/bin/bash", "-e", "-o", "pipefail", "-c"])
        self.assertEqual(len(shlex.split(self.command)), 6)
        for shell in (False, True):
            with self.subTest(shell=shell):
                self.run_command(0, ["preflight", "migrate", "current", "api"], shell=shell)

    def test_missing_or_changed_commit_and_origins_execute_nothing(self):
        cases = (
            (1, {"RENDER_GIT_COMMIT": ""}),
            (1, {"RENDER_GIT_COMMIT": "0" * 40}),
            (1, {"RENDER_EXTERNAL_URL": "https://wrong.example.invalid"}),
            (1, {"RENDER_EXTERNAL_URL": ""}),
            (1, {"VALHALLA_STAGING_API_ORIGIN": ""}),
        )
        for expected, changes in cases:
            with self.subTest(changes=changes):
                self.run_command(expected, [], **changes)

    def test_preflight_or_migration_failure_stops_before_api(self):
        self.run_command(2, ["preflight"], PREFLIGHT_CODE="2")
        self.run_command(7, ["preflight", "migrate"], MIGRATION_CODE="7")

    def test_alembic_failure_propagates_even_if_output_matches_head(self):
        self.run_command(17, ["preflight", "migrate", "current"], ALEMBIC_CODE="17")

    def test_wrong_head_holds_and_api_exit_is_preserved(self):
        self.run_command(1, ["preflight", "migrate", "current"], MIGRATION_HEAD="wrong (head)")
        self.run_command(53, ["preflight", "migrate", "current", "api"], APP_CODE="53")

    def test_literal_quoted_body_can_reproduce_observed_127(self):
        legacy_body = '   test "${RENDER_GIT_COMMIT:-}" = "fixture"   cd /app '
        result = subprocess.run(
            ["/bin/bash", "-c", shlex.quote(legacy_body)],
            env=self.env,
            capture_output=True,
            text=True,
            timeout=5,
        )
        self.assertEqual(result.returncode, 127)
        self.assertIn("No such file or directory", result.stderr)
        self.assertFalse(self.trace.exists())


if __name__ == "__main__":
    unittest.main()
