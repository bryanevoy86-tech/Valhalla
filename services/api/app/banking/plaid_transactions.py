"""Bounded, read-only Plaid adapter for independently posted CAD credits."""
from contextlib import contextmanager
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
import hashlib
import os

import httpx
from fastapi import HTTPException


def _posted_movement(client, *, token, account_id, trace, arrival, amount_minor, today, debit):
    start, end = arrival - timedelta(days=1), min(today, arrival + timedelta(days=7))
    if end < start:
        raise HTTPException(409, "Payout is outside the bank posting window")
    try:
        response = client.post("/transactions/get", json={
            "access_token": token, "start_date": start.isoformat(), "end_date": end.isoformat(),
            "options": {"account_ids": [account_id], "count": 500, "offset": 0},
        })
        response.raise_for_status()
        body = response.json(parse_float=Decimal)
    except (ValueError, httpx.HTTPError):
        raise HTTPException(503, "Independent bank readback unavailable") from None
    items = body.get("transactions") if isinstance(body, dict) else None
    if (not isinstance(items, list) or len(items) > 500 or type(body.get("total_transactions")) is not int
            or body["total_transactions"] != len(items) or any(not isinstance(item, dict) for item in items)):
        raise HTTPException(409, "Bank readback window is incomplete")
    candidates = []
    for item in items:
        meta = item.get("payment_meta")
        if (item.get("account_id") == account_id and isinstance(meta, dict) and meta.get("reference_number") == trace):
            candidates.append(item)
    if len(candidates) != 1:
        raise HTTPException(409, "A single bank entry with the exact payout trace is required")
    item = candidates[0]
    identity = item.get("transaction_id")
    try:
        posted_on = date.fromisoformat(item.get("date"))
        amount = item.get("amount")
        minor = (1 if debit else -1) * Decimal(amount) * 100 if type(amount) in (int, Decimal) else None
    except (ValueError, TypeError, InvalidOperation):
        raise HTTPException(409, "Malformed bank posting evidence") from None
    if (not isinstance(identity, str) or not 1 <= len(identity) <= 160 or item.get("pending") is not False
            or item.get("iso_currency_code") != "CAD" or not start <= posted_on <= end
            or minor is None or not minor.is_finite() or minor != amount_minor):
        raise HTTPException(409, "The bank posting is pending or differs from the payout")
    return {"transaction_sha256": hashlib.sha256(identity.encode()).hexdigest(),
            "posted_on": posted_on.isoformat(), "amount_minor": amount_minor, "currency": "CAD"}


def posted_credit(client, *, token, account_id, trace, arrival, amount_minor, today):
    return _posted_movement(client, token=token, account_id=account_id, trace=trace, arrival=arrival,
                            amount_minor=amount_minor, today=today, debit=False)


@contextmanager
def _configured_bank_reader(*, live, stripe_destination):
    mode = "production" if live else "sandbox"
    scope = os.getenv("VALHALLA_PLAID_STRIPE_DESTINATION")
    account = os.getenv("VALHALLA_PLAID_BANK_ACCOUNT_ID")
    token = os.getenv("VALHALLA_PLAID_READ_ACCESS_TOKEN")
    client_id = os.getenv("PLAID_CLIENT_ID")
    secret = os.getenv("PLAID_SECRET")
    if (os.getenv("VALHALLA_PLAID_SETTLEMENT_MODE") != mode or not all((scope, account, token, client_id, secret))
            or scope != stripe_destination):
        raise HTTPException(503, "Independent bank readback is disabled or not bound to this destination")
    host = "https://production.plaid.com" if live else "https://sandbox.plaid.com"
    with httpx.Client(base_url=host, headers={"PLAID-CLIENT-ID": client_id, "PLAID-SECRET": secret},
                      follow_redirects=False, trust_env=False, timeout=5.0) as client:
        yield client, token, account


def _configured_bank_movement(*, trace, arrival, amount_minor, today, live, stripe_destination, debit):
    with _configured_bank_reader(live=live, stripe_destination=stripe_destination) as (client, token, account):
        return _posted_movement(client, token=token, account_id=account, trace=trace, arrival=arrival,
                                amount_minor=amount_minor, today=today, debit=debit)


def configured_bank_credit(**kwargs):
    return _configured_bank_movement(**kwargs, debit=False)


def configured_bank_debit(**kwargs):
    return _configured_bank_movement(**kwargs, debit=True)


def _balance_minor(value):
    if type(value) not in (int, Decimal):
        raise HTTPException(409, "Independent bank balance is incomplete")
    amount = Decimal(value) * 100
    if not amount.is_finite() or abs(amount) > 999_999_999_999 or amount != amount.to_integral_value():
        raise HTTPException(409, "Independent CAD balance is not an exact minor-unit amount")
    return int(amount)


def account_balance_observation(client, *, token, account_id, live):
    try:
        response = client.post("/accounts/balance/get", json={
            "access_token": token, "options": {"account_ids": [account_id]},
        })
        response.raise_for_status()
        body = response.json(parse_float=Decimal)
    except (ValueError, httpx.HTTPError):
        raise HTTPException(503, "Independent bank balance readback unavailable") from None
    accounts, identity = (body.get("accounts"), body.get("request_id")) if isinstance(body, dict) else (None, None)
    if (not isinstance(accounts, list) or len(accounts) != 1 or not isinstance(accounts[0], dict)
            or not isinstance(identity, str) or not 1 <= len(identity) <= 128):
        raise HTTPException(409, "Exact bank account and request receipt required")
    account = accounts[0]
    balances = account.get("balances")
    if (account.get("account_id") != account_id or account.get("type") != "depository"
            or not isinstance(balances, dict) or balances.get("iso_currency_code") != "CAD"):
        raise HTTPException(409, "Bank balance response is outside the approved CAD depository account")
    return {"bank_available_reported_minor": _balance_minor(balances.get("available")),
            "bank_current_reported_minor": _balance_minor(balances.get("current")),
            "basis": "PLAID_BANK_BALANCE_OBSERVATION" if live else "PLAID_SANDBOX_BALANCE_OBSERVATION",
            "account_reference_sha256": hashlib.sha256(account_id.encode()).hexdigest(),
            "request_reference_sha256": hashlib.sha256(identity.encode()).hexdigest(),
            "read_at": datetime.now(timezone.utc).isoformat(), "actual_accessible_funds_minor": None,
            "funds_movement_authorized": False}


def configured_bank_balance(*, live, stripe_destination):
    if os.getenv("VALHALLA_PLAID_BALANCE_READBACK_ENABLED") != "1":
        raise HTTPException(503, "Independent bank balance readback is disabled")
    with _configured_bank_reader(live=live, stripe_destination=stripe_destination) as (client, token, account):
        return account_balance_observation(client, token=token, account_id=account, live=live)
