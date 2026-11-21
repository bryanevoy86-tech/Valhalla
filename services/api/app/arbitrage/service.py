from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import List, Optional, Tuple
from app.arbitrage.models import FXRule, FXOrder, FXMetric
from app.arbitrage.schemas import FXRuleCreate, FXOrderCreate
from math import isfinite


PAPER_STARTING_CAPITAL = 100_000.0


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
    o = db.get(FXOrder, order_id, with_for_update=True)
    if o is None:
        return None
    if o.status == "closed" and o.exit_px == exit_px:
        return o
    if o.status != "open":
        raise ValueError("Paper order cannot be closed at a different price or state")
    o.exit_px = exit_px
    o.status = "closed"
    o.closed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(o)
    return o


def _compute_book_equity(db: Session) -> Tuple[float, float]:
    """Recompute virtual equity from paper orders and a fixed virtual baseline."""
    closed = db.query(FXOrder).filter(FXOrder.status == "closed").all()
    realized = 0.0
    for order in closed:
        values = (order.entry_px, order.exit_px, order.size)
        if order.side not in {"buy", "sell"} or any(
            value is None or not isfinite(value) or not 0 < value <= 1_000_000 for value in values
        ):
            continue
        difference = order.exit_px - order.entry_px
        realized += difference * order.size * (1 if order.side == "buy" else -1)
    return PAPER_STARTING_CAPITAL + realized, realized


def _get_last_metric(db: Session) -> Optional[FXMetric]:
    return db.query(FXMetric).filter(FXMetric.note.in_(("paper_only", "paper_freeze_triggered"))).order_by(
        FXMetric.id.desc(),
    ).first()


def evaluate_and_record_metrics(db: Session) -> FXMetric:
    equity, _ = _compute_book_equity(db)
    last = _get_last_metric(db)
    peak = max(equity, last.peak_equity if last else PAPER_STARTING_CAPITAL)
    drawdown = max(0.0, (peak - equity) / peak * 100.0)
    metric = FXMetric(equity=equity, peak_equity=peak, drawdown_pct=drawdown, note="paper_only")
    db.add(metric)
    db.commit()
    db.refresh(metric)

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
        metric.note = "paper_freeze_triggered"
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
