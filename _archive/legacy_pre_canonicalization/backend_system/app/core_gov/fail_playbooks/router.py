from __future__ import annotations
from fastapi import APIRouter

router = APIRouter(prefix="/core/fail_playbooks", tags=["core-fail-playbooks"])

@router.get("/payment_failed")
def payment_failed():
    return {
        "steps": [
            "1) Confirm whether the bank declined (NSF) or vendor rejected (account mismatch).",
            "2) Move funds into the bills account immediately (or transfer from buffer).",
            "3) If vendor: confirm PAD details and retry; if NSF: ask vendor for retry date.",
            "4) Log a pay_confirm entry once resolved (even if late).",
            "5) Mark autopay_verified=false until next successful cycle.",
            "6) If recurring risk: enable Shield Lite to pause non-essential spending.",
        ],
        "templates": {
            "vendor_call": "Hi, this is regarding a failed payment draft for <PAYEE>. Can you confirm the reason code and the next retry date?",
            "bank_call": "Hi, I need to confirm why a pre-authorized debit was declined and whether there are holds/limits on my account.",
        }
    }
