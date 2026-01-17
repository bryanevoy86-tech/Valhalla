# services/api/app/routers/admin_heimdall.py

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict

import requests
from fastapi import APIRouter, HTTPException, status
from app.core.engines.guard_runtime import enforce_engine
from app.core.engines.actions import OUTREACH

router = APIRouter(
    prefix="/admin/heimdall",
    tags=["Admin", "Heimdall"],
)

# Paths are relative to the project root (c:\dev\valhalla)
PROJECT_ROOT = Path(__file__).resolve().parents[4]
AUTO_PR_SCRIPT = PROJECT_ROOT / "scripts" / "ci" / "auto_pr.py"
AUTO_PR_STATUS_FILE = PROJECT_ROOT / "dist" / "docs" / "auto_pr_status.json"


# ---------- Helpers ----------


def _load_autopr_status() -> Dict[str, Any]:
    """
    Load the auto-PR status JSON if it exists.
    """
    if not AUTO_PR_STATUS_FILE.exists():
        raise FileNotFoundError(
            f"Auto-PR status file not found at {AUTO_PR_STATUS_FILE}"
        )

    with AUTO_PR_STATUS_FILE.open("r", encoding="utf-8") as f:
        return json.load(f)


def _run_auto_pr() -> Dict[str, Any]:
    """
    Run the auto PR script synchronously.

    This assumes you have a working Python environment inside the same
    container or host (docker compose api service, or local venv).
    """
    if not AUTO_PR_SCRIPT.exists():
        raise FileNotFoundError(
            f"Auto-PR script not found at {AUTO_PR_SCRIPT}"
        )

    # Use the same Python interpreter running this app
    python_exe = sys.executable or "python"

    try:
        result = subprocess.run(
            [python_exe, str(AUTO_PR_SCRIPT)],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            check=False,
        )
    except Exception as exc:  # pragma: no cover - defensive
        raise RuntimeError(f"Failed to run auto PR script: {exc}") from exc

    return {
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


def _get_discord_status() -> Dict[str, Any]:
    """
    Inspect environment and return a simple view of Discord alert wiring.
    """
    webhook = os.getenv("DISCORD_WEBHOOK_URL") or ""
    configured = bool(webhook.strip())
    return {
        "configured": configured,
        "has_webhook_env": configured,
        "webhook_length": len(webhook) if webhook else 0,
    }


def _send_discord_test_message(message: str) -> Dict[str, Any]:
    webhook = os.getenv("DISCORD_WEBHOOK_URL")
    if not webhook:
        raise RuntimeError(
            "DISCORD_WEBHOOK_URL is not set. Cannot send test alert."
        )

    payload = {"content": message}
    response = requests.post(webhook, json=payload, timeout=10)

    return {
        "status_code": response.status_code,
        "ok": response.ok,
        "response_text": response.text[:500],
    }


# ---------- Routes ----------


@router.get(
    "/api/autopr/status",
    summary="Get auto-PR system status",
    description=(
        "Returns the current auto-PR status, as written by the CI scripts "
        "into dist/docs/auto_pr_status.json."
    ),
)
async def get_autopr_status() -> Dict[str, Any]:
    try:
        status_data = _load_autopr_status()
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(
                f"Auto-PR status file not found at {AUTO_PR_STATUS_FILE}. "
                "Run the auto-PR job at least once."
            ),
        )
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to parse auto-PR status JSON: {exc}",
        )
    return status_data


@router.post(
    "/autopr/run",
    summary="Run auto-PR job now",
    description=(
        "Runs the scripts/ci/auto_pr.py script synchronously and returns "
        "stdout/stderr + exit code."
    ),
)
async def run_autopr_job() -> Dict[str, Any]:
    try:
        result = _run_auto_pr()
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )

    return {
        "message": "Auto-PR job executed",
        "result": result,
    }


@router.get(
    "/api/alerts/status",
    summary="Get alert system status",
    description=(
        "Reports whether Discord webhook is configured for Heimdall alerts."
    ),
)
async def get_alerts_status() -> Dict[str, Any]:
    status_data = _get_discord_status()
    return {
        "alerts": status_data,
    }


@router.post(
    "/api/alerts/test",
    summary="Send test alert to Discord",
    description=(
        "Sends a simple test message to the Discord webhook configured in "
        "DISCORD_WEBHOOK_URL."
    ),
)
async def send_test_alert() -> Dict[str, Any]:
    enforce_engine("wholesaling", OUTREACH)
    try:
        result = _send_discord_test_message(
            "🔔 Heimdall test alert: connectivity OK."
        )
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    except requests.RequestException as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to send test alert: {exc}",
        )

    return {
        "message": "Test alert sent (or attempted).",
        "result": result,
    }
