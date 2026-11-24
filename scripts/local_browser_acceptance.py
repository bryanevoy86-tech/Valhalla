#!/usr/bin/env python3
"""Run Chromium against a disposable loopback API and emit redacted evidence."""

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
CASE = "services/api/tests/test_product_artifact_workflow.py::test_internal_product_asset_stage_bind_verify_and_revoke"
PREFIX = "BROWSER_ACCEPTANCE "
RESEARCH_CASE = "services/api/tests/test_economic_control.py::test_authenticated_research_participant_browser_and_retention"
RESEARCH_PREFIX = "RESEARCH_BROWSER "


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    if any((directory / ".env").exists() for directory in (ROOT, *ROOT.parents, ROOT / "services" / "api")):
        parser.error("Use an isolated checkout without dotenv files")

    env = {key: os.environ[key] for key in ("PATH", "SYSTEMROOT", "WINDIR", "TEMP", "TMP", "TMPDIR",
           "HOME", "NODE_PATH", "PLAYWRIGHT_BROWSERS_PATH", "VALHALLA_BROWSER_EXECUTABLE") if key in os.environ}
    env.update(DATABASE_URL="sqlite://", VALHALLA_JWT_SECRET="browser-acceptance-fixture-jwt",
               VALHALLA_OWNER_USERNAME="browser-fixture", VALHALLA_OWNER_PASSWORD="synthetic-only",
               PYTEST_DISABLE_PLUGIN_AUTOLOAD="1", ENV="dev", APP_ENV="dev", RESET_OWNER_PASSWORD="false",
               VALHALLA_EMERGENCY_STOP="true", PYTHON_DOTENV_DISABLED="1", VALHALLA_BROWSER_ACCEPTANCE="1")
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-o", "addopts=", "-qs", "--disable-warnings", "--tb=short", CASE,
         "services/api/tests/test_loki_independent_receipt.py", RESEARCH_CASE],
        cwd=ROOT, env=env, capture_output=True, text=True, timeout=250,
    )
    sys.stdout.write(result.stdout)
    sys.stderr.write(result.stderr)
    checkpoints = [json.loads(line[len(PREFIX):]) for line in result.stdout.splitlines() if line.startswith(PREFIX)]
    research = [json.loads(line[len(RESEARCH_PREFIX):]) for line in result.stdout.splitlines() if line.startswith(RESEARCH_PREFIX)]
    passed = (result.returncode == 0 and [item["phase"] for item in checkpoints] == ["stopped", "recovered"]
              and research == [{"voluntary_consent": True, "branched_question": True, "withdrawn": True,
                                "prime_key_exposed": False}])
    report = {
        "revision": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "local_browser_acceptance": "PASSED" if passed else "FAILED",
        "weweb_preview_acceptance": "OPEN",
        "commercial_activation_authorized": False,
        "checkpoints": checkpoints,
        "participant_research": research,
    }
    args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
