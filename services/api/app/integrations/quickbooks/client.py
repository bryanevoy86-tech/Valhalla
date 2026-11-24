"""QuickBooks integration client."""
import re

from fastapi import HTTPException

from app.integrations.commissioning import approved_reader, commissioning_receipt, read_json
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

    raise HTTPException(503, "QuickBooks journal submission has not been commissioned")


def get_account(account_id):
    """Inspect the exact QuickBooks test account recorded by the owner."""
    return read_account_fixture(account_id=account_id)


def read_account_fixture(*, account_id=None, transport=None):
    with approved_reader("QUICKBOOKS", "https://sandbox-quickbooks.api.intuit.com", "REALM_ID", "ACCOUNT_ID",
                         transport=transport) as (client, config):
        realm, reference = config
        if not re.fullmatch(r"[0-9]{1,30}", realm) or not re.fullmatch(r"[0-9]{1,30}", reference):
            raise HTTPException(503, "Exact QuickBooks test company and account configuration required")
        if account_id is not None and account_id != reference:
            raise HTTPException(409, "Account differs from the approved commissioning scope")
        data = read_json(client, f"/v3/company/{realm}/account/{reference}").get("Account")
        group = data.get("Classification") if isinstance(data, dict) else None
        if not isinstance(data, dict) or data.get("Id") != reference or data.get("Active") is not True or group not in {
            "Asset", "Liability", "Equity", "Revenue", "Expense",
        }:
            raise HTTPException(409, "QuickBooks account evidence did not match the configured resource")
    return commissioning_receipt("QUICKBOOKS", f"{realm}/{reference}", classification=group, bank_balance_verified=False)
