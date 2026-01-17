# services/api/app/routers/flow_tax_snapshot.py

from __future__ import annotations

from decimal import Decimal
from typing import Any, Dict

from fastapi import APIRouter, HTTPException, status
from fastapi.testclient import TestClient

from app.main import app as main_app
from app.schemas.tax_snapshot import (
    TaxSnapshotInput,
    TaxSnapshotNumbers,
    TaxSnapshotPolicy,
    TaxSnapshotResponse,
)

router = APIRouter(
    prefix="/flow",
    tags=["Flow", "TaxSnapshot"],
)

_client = TestClient(main_app)


@router.post(
    "/tax_snapshot_for_deal",
    response_model=TaxSnapshotResponse,
    status_code=status.HTTP_200_OK,
    summary="Build a CRA-style tax snapshot for a single deal",
    description=(
        "Wraps the profit_allocation flow and returns a CRA-style numeric breakdown "
        "for one deal: cost basis, gross profit, taxable profit, tax amount, and "
        "net after tax, plus policy flags for minimum tax rate."
    ),
)
def tax_snapshot_for_deal(
    payload: TaxSnapshotInput,
) -> TaxSnapshotResponse:
    # 1. Call profit_allocation in-process
    profit_req: Dict[str, Any] = {
        "profit": {
            "backend_deal_id": payload.backend_deal_id,
            "sale_price": str(payload.sale_price),
            "sale_closing_costs": str(payload.sale_closing_costs),
            "extra_expenses": str(payload.extra_expenses),
            "tax_rate": str(payload.tax_rate),
            # For tax snapshot we don't care about FunFunds/reinvest splits,
            # so use neutral values; profit_allocation will still compute correctly.
            "funfunds_percent": "0.00",
            "reinvest_percent": "0.00",
        },
        "policy": None,
    }

    resp = _client.post("/flow/profit_allocation", json=profit_req)
    if resp.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                f"profit_allocation call failed for deal "
                f"{payload.backend_deal_id}: {resp.status_code} {resp.text}"
            ),
        )

    data = resp.json()
    result = data.get("result") or {}
    metrics = result.get("metrics") or {}
    flags = result.get("flags") or {}
    policy_raw = result.get("policy") or {}

    def _dec(val: Any) -> Decimal:
        try:
            return Decimal(str(val))
        except Exception:
            return Decimal("0")

    numbers = TaxSnapshotNumbers(
        purchase_price=_dec(metrics.get("purchase_price")),
        repairs=_dec(metrics.get("repairs")),
        cost_basis=_dec(metrics.get("total_cost_basis")),
        sale_price=_dec(metrics.get("sale_price")),
        sale_closing_costs=_dec(metrics.get("sale_closing_costs")),
        extra_expenses=_dec(metrics.get("extra_expenses")),
        gross_profit=_dec(metrics.get("gross_profit")),
        taxable_profit=_dec(metrics.get("gross_profit")).max(Decimal("0")),
        tax_rate_applied=_dec(policy_raw.get("min_tax_rate") or payload.tax_rate),
        tax_amount=_dec(metrics.get("taxes")),
        net_after_tax=_dec(metrics.get("net_profit_after_tax")),
    )

    # Policy view
    min_tax_rate = _dec(policy_raw.get("min_tax_rate") or "0.20")
    breach_min_tax_rate = bool(flags.get("breach_min_tax_rate", False))

    policy = TaxSnapshotPolicy(
        min_tax_rate=min_tax_rate,
        breach_min_tax_rate=breach_min_tax_rate,
        notes=flags.get("notes"),
    )

    # Summary line that reads clean for CRA / accountant
    if numbers.gross_profit <= 0:
        summary = (
            f"Deal {payload.backend_deal_id}: no positive gross profit "
            f"(gross={numbers.gross_profit}); no tax expected on this event."
        )
    else:
        summary = (
            f"Deal {payload.backend_deal_id}: cost basis {numbers.cost_basis}, "
            f"sale {numbers.sale_price}, gross profit {numbers.gross_profit}, "
            f"tax amount {numbers.tax_amount} at effective rate "
            f"{payload.tax_rate:.1%}, net after tax {numbers.net_after_tax}."
        )

    debug = {
        "backend_deal_id": str(payload.backend_deal_id),
        "sale_price": str(payload.sale_price),
        "sale_closing_costs": str(payload.sale_closing_costs),
        "extra_expenses": str(payload.extra_expenses),
        "tax_rate_input": str(payload.tax_rate),
        "profit_allocation_freeze_created": str(data.get("freeze_event_created", False)),
    }

    return TaxSnapshotResponse(
        backend_deal_id=payload.backend_deal_id,
        numbers=numbers,
        policy=policy,
        summary=summary,
        debug=debug,
    )
