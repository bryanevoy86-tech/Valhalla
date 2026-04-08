import json
from datetime import datetime

BASE_URL = "http://localhost:4000"

manifest = {
    "generated_at": datetime.utcnow().isoformat(),
    "base_url": BASE_URL,

    "health": {
        "endpoint": "/health",
        "method": "GET",
        "description": "System health check"
    },

    "auth": {
        "type": "jwt",
        "notes": "Attach Authorization: Bearer <token> when enabled"
    },

    "core_endpoints": {
        "activation": {
            "summary": "/api/v1/activation/routes/summary",
            "routes": "/api/v1/activation/routes"
        },
        "compliance": {
            "mode": "/api/compliance/mode",
            "exit_validate": "/api/compliance/eia/exit/validate",
            "exit_execute": "/api/compliance/eia/exit/execute"
        },
        "legal": {
            "templates": "/api/legal/templates",
            "queue": "/api/legal/queue",
            "approve": "/api/legal/approve/{approval_id}",
            "approve_and_send": "/api/legal/approve-and-send/{approval_id}",
            "stage_trigger": "/api/legal/trigger-from-stage",
            "package_trigger": "/api/legal/trigger-package-from-stage",
            "package_send": "/api/legal/approve-and-send-package",
            "registry_resolve": "/api/legal/registry/resolve"
        },
        "finance": {
            "ledger": "/api/finance/ledger/create",
            "disbursement": "/api/finance/disbursement/plan",
            "intent_queue": "/api/finance/intent/queue",
            "intent_status": "/api/finance/intent/{intent_id}",
            "intent_approve": "/api/finance/intent/{intent_id}/approve",
            "freeze": "/api/finance/freeze",
            "summary": "/api/finance/status/summary",
            "feed": "/api/finance/status/feed",
            "audit": "/api/finance/status/audit"
        }
    },

    "sample_flows": {
        "legal_flow": {
            "step_1": "POST /api/legal/trigger-package-from-stage",
            "step_2": "GET /api/legal/queue/{approval_id}",
            "step_3": "POST /api/legal/approve-and-send-package"
        },
        "finance_flow": {
            "step_1": "POST /api/finance/intent/queue",
            "step_2": "GET /api/finance/intent/{intent_id}",
            "step_3": "POST /api/finance/intent/{intent_id}/approve"
        }
    },

    "notes": [
        "Use base_url + endpoint path",
        "All endpoints return JSON",
        "Approval gates required for legal + finance actions",
        "EIA mode may block certain financial actions",
        "Frontend should read routes dynamically via activation endpoints"
    ]
}

with open("WEWEB_BACKEND_MANIFEST.json", "w") as f:
    json.dump(manifest, f, indent=2)

print("✅ WEWEB_BACKEND_MANIFEST.json generated")
