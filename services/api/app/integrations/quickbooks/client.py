"""QuickBooks integration client."""
from app.core.engines.actions import MONEY_MOVE
from app.core.engines.guard_runtime import enforce_engine
from app.core.runtime_flags import is_live


def post_journal_entry(entry):
    """Post a journal entry to QuickBooks."""
    enforce_engine(
        "wholesaling",
        MONEY_MOVE,
        {
            "provider": "quickbooks",
            "target_type": "journal_entry",
            "entry_type": str((entry or {}).get("type") or "unknown"),
        },
    )
    if not is_live():
        return {"status": "sandbox", "entry_id": "entry_sandbox"}

    return {
        "status": "posted",
        "entry_id": f"qbo_{entry.get('account', 'unknown')[:4]}"
    }


def get_account(account_id):
    """Get an account from QuickBooks."""
    return {
        "id": account_id,
        "name": "Account",
        "balance": 0
    }
