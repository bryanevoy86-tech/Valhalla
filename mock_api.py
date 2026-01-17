"""
Minimal mock API for testing stage_check.ps1 script.
This demonstrates that the stage check script works correctly.
"""

from fastapi import FastAPI
from datetime import datetime

app = FastAPI(title="Valhalla Mock API", version="1.0.0", docs_url="/docs")


@app.get("/api/governance/runbook/status")
def runbook_status():
    """
    Mock runbook endpoint that returns a realistic response.
    """
    return {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "blockers": [
            {
                "id": "env_sanity",
                "ok": False,
                "severity": "BLOCKER",
                "message": "ENV and DATABASE_URL must be set correctly",
                "detail": {
                    "ENV": None,
                    "GO_LIVE_ENFORCE": None,
                    "DATABASE_URL_set": False
                }
            },
            {
                "id": "risk_policies_present",
                "ok": False,
                "severity": "BLOCKER",
                "message": "Risk policies must exist (floors / caps / approvals)",
                "detail": {"count": 0}
            }
        ],
        "warnings": [],
        "info": [
            {
                "id": "system_online",
                "ok": True,
                "severity": "INFO",
                "message": "Mock API is running",
                "detail": None
            }
        ],
        "ok_to_enable_go_live": False,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
