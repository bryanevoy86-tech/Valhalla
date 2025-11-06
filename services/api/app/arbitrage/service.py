from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import List, Optional, Tuple
from app.arbitrage.models import FXRule, FXOrder, FXMetric
from app.arbitrage.schemas import FXRuleCreate, FXOrderCreate
from app.finops.schemas import VaultBalanceUpsert
from app.finops.service import upsert_vault, list_vaults


SAFE_VAULT = "MAIN"  # sync book equity to MAIN vault


def create_rule(db: Session, payload: FXRuleCreate) -> FXRule:
    rule = FXRule(**payload.dict())
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


def list_rules(db: Session) -> List[FXRule]:
    return db.query(FXRule).order_by(FXRule.id.desc()).all()


def place_order(db: Session, payload: FXOrderCreate) -> FXOrder:
    order = FXOrder(**payload.dict(), status="open")
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


def list_orders(db: Session, status: Optional[str] = None) -> List[FXOrder]:
    q = db.query(FXOrder)
    if status:
        q = q.filter(FXOrder.status == status)
    return q.order_by(FXOrder.id.desc()).all()


def close_order(db: Session, order_id: int, exit_px: float) -> Optional[FXOrder]:
    o = db.get(FXOrder, order_id)
    if not o:
        return None
    o.exit_px = exit_px
    o.status = "closed"
    o.closed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(o)
    return o


def _compute_book_equity(db: Session) -> Tuple[float, float]:
    """Return (equity, realized_pnl). Unrealized omitted for simplicity."""
    closed = db.query(FXOrder).filter(FXOrder.status == "closed").all()
    realized = 0.0
    for o in closed:
        pnl_per_unit = (
            (o.exit_px - o.entry_px) if o.side == "buy" else (o.entry_px - o.exit_px)  # type: ignore[operator]
        )
        realized += pnl_per_unit * o.size
    # Assume base equity is last vault MAIN balance (if any)
    vaults = list_vaults(db)
    base = 0.0
    for v in vaults:
        if v.vault_code == SAFE_VAULT:
            base = v.balance
            break
    equity = base + realized
    return equity, realized


def _get_last_metric(db: Session) -> Optional[FXMetric]:
    return db.query(FXMetric).order_by(FXMetric.id.desc()).first()


def evaluate_and_record_metrics(db: Session) -> FXMetric:
    equity, _ = _compute_book_equity(db)
    last = _get_last_metric(db)
    peak = max(equity, last.peak_equity if last else equity)
    dd = 0.0 if peak <= 0 else max(0.0, (peak - equity) / peak * 100.0)
    metric = FXMetric(equity=equity, peak_equity=peak, drawdown_pct=dd, note="auto")
    db.add(metric)
    db.commit()
    db.refresh(metric)

    # Sync vault with current equity (book value) — source "fx_engine"
    upsert_vault(
        db,
        payload=VaultBalanceUpsert(
            vault_code=SAFE_VAULT,
            currency="CAD",
            balance=equity,
            last_source="fx_engine",
        ),
    )

    # Enforce freeze if rules require it
    enforce_freeze_rules(db, metric)
    return metric


def _rules_map(db: Session) -> dict:
    rules = list_rules(db)
    active = {r.param: r.value for r in rules if r.active}
    return active


def enforce_freeze_rules(db: Session, metric: FXMetric):
    rules = _rules_map(db)
    max_dd = float(rules.get("max_drawdown_pct", 2.0))
    if metric.drawdown_pct >= max_dd:
        # Practical "freeze": mark a vault note by reducing exposure => here we just add a cautionary note.
        metric.note = f"freeze_triggered_dd_{metric.drawdown_pct:.2f}%"
        db.commit()
        # In a real engine, you would: cancel open orders, reduce positions, halt new orders, alert, etc.


def bootstrap_safe_rules(db: Session):
    """Idempotent safe defaults."""
    defaults = [
        FXRuleCreate(
            name="SafeMode Max DD 2%", param="max_drawdown_pct", value=2.0, active=True
        ),
    ]
    for d in defaults:
        exists = db.query(FXRule).filter(FXRule.param == d.param).first()
        if not exists:
            create_rule(db, d)
