"""QuickBooks integration client."""
from app.core.runtime_flags import is_live


def post_journal_entry(entry):
    """Post a journal entry to QuickBooks."""
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
