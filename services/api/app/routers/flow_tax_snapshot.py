"""Private planning calculations using the canonical recorded cost inputs."""

from decimal import Decimal

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.dependencies import require_prime_control_key
from app.routers.flow_profit_allocation import compute_profit_metrics, recorded_cost_inputs
from app.schemas.profit_allocation import ProfitAllocationPolicy
from app.schemas.tax_snapshot import TaxSnapshotInput, TaxSnapshotNumbers, TaxSnapshotPolicy, TaxSnapshotResponse
from app.services.freeze_events import log_freeze_event

router = APIRouter(
    prefix="/flow", tags=["Flow", "TaxSnapshot"],
    dependencies=[Depends(require_prime_control_key)],
)


@router.post("/tax_snapshot_for_deal", response_model=TaxSnapshotResponse)
def tax_snapshot_for_deal(payload: TaxSnapshotInput, db: Session = Depends(get_db)) -> TaxSnapshotResponse:
    purchase_price, repairs = recorded_cost_inputs(db, payload.backend_deal_id)
    metrics = compute_profit_metrics(
        purchase_price, repairs, payload.sale_price, payload.sale_closing_costs,
        payload.extra_expenses, payload.tax_rate,
    )
    minimum = ProfitAllocationPolicy().min_tax_rate
    breach = metrics.gross_profit > 0 and payload.tax_rate < minimum
    note = "Scenario tax rate falls below the configured planning threshold." if breach else None
    if breach:
        log_freeze_event(
            db, source="tax_snapshot", event_type="profit_policy_violation",
            severity="critical", reason=note,
            payload={
                "backend_deal_id": payload.backend_deal_id,
                "tax_rate": str(payload.tax_rate),
                "minimum": str(minimum),
            },
        )
    return TaxSnapshotResponse(
        backend_deal_id=payload.backend_deal_id,
        numbers=TaxSnapshotNumbers(
            purchase_price=metrics.purchase_price,
            repairs=metrics.repairs,
            cost_basis=metrics.total_cost_basis,
            sale_price=metrics.sale_price,
            sale_closing_costs=metrics.sale_closing_costs,
            extra_expenses=metrics.extra_expenses,
            gross_profit=metrics.gross_profit,
            taxable_profit=max(metrics.gross_profit, Decimal("0")),
            tax_rate_applied=payload.tax_rate,
            tax_amount=metrics.taxes,
            net_after_tax=metrics.net_profit_after_tax,
        ),
        policy=TaxSnapshotPolicy(min_tax_rate=minimum, breach_min_tax_rate=breach, notes=note),
        summary="Planning estimate using the entered sale, costs and tax rate.",
        debug={"profit_allocation_freeze_created": str(breach)},
    )
