#!/usr/bin/env python3
"""Run the January core acceptance rehearsal without using live services."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
from time import monotonic
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
API_TESTS = "services/api/tests/"
FRONTEND_TESTS = [
    "tests/test-weweb-owner-conversations.test.mjs",
    "tests/test-weweb-owner-review-portal.test.mjs",
    "tests/test-weweb-owner-pantheon.test.mjs",
    "tests/test-weweb-owner-operating-scope.test.mjs",
    "tests/test-weweb-owner-attention.test.mjs",
    "tests/test-weweb-subscriber-paid-product.test.mjs",
]


def run_gate(name, command, environment):
    started = monotonic()
    print(f"\n[January] {name}", flush=True)
    try:
        result = subprocess.run(command, cwd=ROOT, env=environment, check=False, timeout=240)
    except (OSError, subprocess.TimeoutExpired) as error:
        return {"gate": name, "status": "FAILED", "reason": type(error).__name__}
    return {"gate": name, "status": "PASSED" if result.returncode == 0 else "FAILED",
            "exit_code": result.returncode, "seconds": round(monotonic() - started, 2)}


def protected_postgres_url():
    raw = os.environ.get("FACTORY_TEST_POSTGRES_URL", "")
    url = urlsplit(raw)
    if (url.scheme not in {"postgresql", "postgresql+psycopg2"} or url.hostname != "127.0.0.1"
            or url.port != 5432 or url.path != "/valhalla_factory_ci" or url.query or url.fragment):
        raise ValueError("Supply an isolated loopback PostgreSQL database named valhalla_factory_ci")
    return raw


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--postgres", action="store_true", help="require disposable localhost PostgreSQL gates")
    parser.add_argument("--report", type=Path, help="write machine-readable results")
    args = parser.parse_args()
    if any((directory / ".env").exists() for directory in (ROOT, *ROOT.parents, ROOT / "services" / "api")):
        parser.error("Use an isolated checkout without a .env file in the repository, API directory, or their parents")
    try:
        postgres = protected_postgres_url() if args.postgres else None
    except ValueError as error:
        parser.error(str(error))

    # Build from OS essentials so an owner shell cannot supply live credentials or provider flags.
    env = {key: os.environ[key] for key in ("PATH", "SYSTEMROOT", "WINDIR", "TEMP", "TMP", "TMPDIR")
           if key in os.environ}
    env.update(DATABASE_URL="sqlite://", VALHALLA_JWT_SECRET="january-isolated-rehearsal",
               VALHALLA_OWNER_USERNAME="january-rehearsal", VALHALLA_OWNER_PASSWORD="synthetic-only",
               PYTEST_DISABLE_PLUGIN_AUTOLOAD="1", ENV="dev", APP_ENV="dev",
               RESET_OWNER_PASSWORD="false", VALHALLA_EMERGENCY_STOP="true", PYTHON_DOTENV_DISABLED="1")

    gates = [
        ("acceptance_matrix", [PYTHON, "scripts/prime_system_preflight.py", "--json"]),
        ("canonical_api_routes", [PYTHON, "scripts/prime_runtime_route_probe.py", "--import-app"]),
        ("connected_owner_specialists_loki_factory_mimir_and_cad", [
            PYTHON, "-m", "pytest", "-q", "--tb=short",
            API_TESTS + "test_product_artifact_workflow.py",
            API_TESTS + "test_loki_independent_receipt.py",
        ]),
        ("cad_processor_buyer_delivery_corrections_and_cash", [
            PYTHON, "-m", "pytest", "-q", "--tb=short", API_TESTS + "test_stripe_finance.py",
        ]),
        ("builder_and_browser_boundary", [
            PYTHON, "-m", "pytest", "-q", "--tb=short", API_TESTS + "test_builder_assignments.py",
            API_TESTS + "test_weweb_logout_canonical_mount.py",
        ]),
        ("weweb_transport_contracts", ["node", "--test", *FRONTEND_TESTS]),
    ]
    results = [run_gate(name, command, env) for name, command in gates]
    postgres_gates = (
        ("postgres_restart_concurrency", "test_factory_postgres.py"),
        ("postgres_migration_chain", "test_postgres_migration_chain.py"),
        ("postgres_cold_release_and_snapshot_restore", "test_january_release_restore.py"),
    )
    if postgres:
        # The PostgreSQL fixtures execute strictly internal work to prove acquisition and retry.
        pg_env = {**env, "FACTORY_TEST_POSTGRES_URL": postgres, "DATABASE_URL": postgres,
                  "VALHALLA_EMERGENCY_STOP": "false"}
        for gate, test in postgres_gates:
            results.append(run_gate(gate, [PYTHON, "-m", "unittest", "discover", "-s", "tests",
                                          "-p", test, "-v"], pg_env))
    else:
        for gate, _ in postgres_gates:
            results.append({"gate": gate, "status": "BLOCKED", "reason": "Run with --postgres on a disposable database"})

    passed = all(gate["status"] == "PASSED" for gate in results)
    failed = any(gate["status"] == "FAILED" for gate in results)
    report = {
        "revision": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "tracked_worktree_clean": not subprocess.check_output(
            ["git", "status", "--porcelain", "--untracked-files=no"], cwd=ROOT, text=True,
        ).strip(),
        "mode": "ISOLATED_REHEARSAL",
        "internal_status": "FAILED" if failed else ("PASSED" if passed else "PARTIAL"),
        "gates": results,
        "authorized_staging_status": "BLOCKED",
        "staging_evidence_required": [
            "Approved HTTPS API and WeWeb preview origins and real signed-in browser acceptance",
            "Authorized scope, independent staging identities and elapsed run/restart evidence",
            "Approved CAD offer and commissioned provider-native test events and readback",
            "Independent bank and qualified accounting review for proceeds reliance",
        ],
        "external_authority_granted": False,
    }
    output = json.dumps(report, indent=2) + "\n"
    print(output, end="")
    if args.report:
        args.report.write_text(output, encoding="utf-8")
    return int(failed)


if __name__ == "__main__":
    raise SystemExit(main())
