# services/api/tools/public_training/replay_wholesaling.py
import os
import sys
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from sqlalchemy import create_engine, text

# Ensure app module is importable (services/api is the root for "app.*" imports)
_api_root = Path(__file__).parent.parent.parent.parent / "services" / "api"
if str(_api_root) not in sys.path:
    sys.path.insert(0, str(_api_root))

def die(msg: str):
    raise SystemExit(f"[replay_wholesaling] {msg}")

@dataclass
class ReplayResult:
    external_id: str
    predicted_should_pursue: bool
    predicted_offer_low: Optional[float]
    predicted_offer_high: Optional[float]
    predicted_review: bool

    label_should_pursue: Optional[bool]
    label_offer_low: Optional[float]
    label_offer_high: Optional[float]
    label_review: Optional[bool]
    label_risk: Optional[str]

# --------------- ADAPTER WIRED TO REAL LOGIC ---------------
from typing import Dict, Any, Optional


def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def _get_calculate_deal_metrics():
    """Lazy load the real function with path handling."""
    try:
        from app.deal_analyzer.service import calculate_deal_metrics
        return calculate_deal_metrics
    except ModuleNotFoundError:
        # services/api must be in sys.path for "from app..." to work
        import os
        
        # Current working directory is typically the repo root
        cwd = Path(os.getcwd())
        
        # Check if cwd is already the repo root (contains services/api)
        services_api = cwd / "services" / "api"
        if services_api.exists():
            if str(services_api) not in sys.path:
                sys.path.insert(0, str(services_api))
        else:
            # Fallback: try relative to this file (3 levels up)
            file_path = Path(__file__).resolve().parent.parent.parent
            if file_path.exists() and "api" in str(file_path) and str(file_path) not in sys.path:
                sys.path.insert(0, str(file_path))
        
        from app.deal_analyzer.service import calculate_deal_metrics
        return calculate_deal_metrics


def _derive_inputs_from_training_lead(lead: Dict[str, Any]) -> Dict[str, float]:
    """
    We do not have true asking price, sold price, or real rehab in public assessment data.
    So for SANDBOX replay we derive conservative proxy inputs from assessed_value.

    assessed_value -> valuation anchor (high confidence)
    purchase_price -> conservative target acquisition proxy
    rehab_cost     -> conservative rehab band proxy
    arv            -> conservative after-repair value proxy
    """
    assessed = lead.get("assessed_value")
    if assessed is None:
        raise ValueError("lead.assessed_value is required for replay adapter")

    assessed = float(assessed)

    # Conservative proxy assumptions (tune later)
    # Purchase price proxy: target below assessed to avoid optimism
    purchase_price = assessed * 0.70

    # Rehab proxy: modest % of assessed with clamps to avoid crazy numbers
    rehab_cost = _clamp(assessed * 0.12, 8000.0, 90000.0)

    # ARV proxy: mild uplift over assessed (still conservative)
    arv = assessed * 1.10

    return {
        "assessed_value": assessed,
        "purchase_price": purchase_price,
        "rehab_cost": rehab_cost,
        "arv": arv,
    }


def run_wholesaling_pipeline(lead: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calls real deal metrics logic and maps result into replay contract:
      {
        "should_pursue": bool,
        "offer_low": float|None,
        "offer_high": float|None,
        "human_review_required": bool
      }

    IMPORTANT:
    - This is still SANDBOX-only (enforced by caller).
    - This does NOT perform outbound actions.
    """
    x = _derive_inputs_from_training_lead(lead)

    # Lazy load the real function (handles import path issues)
    calculate_deal_metrics = _get_calculate_deal_metrics()

    metrics = calculate_deal_metrics(
        purchase_price=x["purchase_price"],
        rehab_cost=x["rehab_cost"],
        arv=x["arv"],
    )

    # metrics.recommendation is one of: "pass", "review", "reject"
    rec = (getattr(metrics, "recommendation", "") or "").strip().lower()
    risk = float(getattr(metrics, "risk_score", 50.0) or 50.0)
    roi = float(getattr(metrics, "roi_percentage", 0.0) or 0.0)
    profit = float(getattr(metrics, "expected_profit", 0.0) or 0.0)

    # --- Two-stage gate ---
    # Stage 1: Analyzer recommendation
    # Stage 2: Valhalla safety policy (secondary gate)
    PASS_RISK_MAX = 20.0
    PASS_ROI_MIN = 18.0
    PASS_PROFIT_MIN = 15000.0

    passes_secondary_gate = (
        (risk <= PASS_RISK_MAX) and
        (roi >= PASS_ROI_MIN) and
        (profit >= PASS_PROFIT_MIN)
    )

    # Only pursue if analyzer says "pass" AND passes secondary safety gate
    should_pursue = (rec == "pass") and passes_secondary_gate

    # Review stays on by default unless it's a very clean pass (both gates pass)
    human_review_required = not should_pursue


    # Offer band uses assessed anchor (aligns with synthetic labels + gates)
    offer_low = x["assessed_value"] * 0.60
    offer_high = x["assessed_value"] * 0.78

    return {
        "should_pursue": bool(should_pursue),
        "offer_low": float(offer_low),
        "offer_high": float(offer_high),
        "human_review_required": bool(human_review_required),
    }
# ----------------------------------------------------------

def main():
    app_env = os.getenv("APP_ENV", "dev").lower()
    if app_env not in ("sandbox", "dev"):
        die(f"Refusing to replay in APP_ENV={app_env}. Set APP_ENV=sandbox.")

    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        die("DATABASE_URL not set")

    engine = create_engine(db_url, future=True)

    sample_limit = int(os.getenv("REPLAY_LIMIT", "1000"))

    results: List[ReplayResult] = []

    with engine.begin() as conn:
        rows = conn.execute(text("""
          SELECT p.source, p.external_id, p.province, p.city, p.address, p.assessed_value,
                 l.should_pursue, l.offer_low, l.offer_high, l.human_review_required, l.risk_level
          FROM public_training_properties p
          LEFT JOIN public_training_labels l
            ON l.source = p.source AND l.external_id = p.external_id
          WHERE p.assessed_value IS NOT NULL
          LIMIT :limit
        """), {"limit": sample_limit}).fetchall()

        for (source, external_id, province, city, address, assessed_value,
             lbl_should, lbl_low, lbl_high, lbl_review, lbl_risk) in rows:

            lead = {
                "source": source,
                "external_id": external_id,
                "province": province,
                "city": city,
                "address": address,
                "assessed_value": float(assessed_value) if assessed_value is not None else None,
            }

            pred = run_wholesaling_pipeline(lead)

            results.append(ReplayResult(
                external_id=str(external_id),
                predicted_should_pursue=bool(pred.get("should_pursue", False)),
                predicted_offer_low=pred.get("offer_low"),
                predicted_offer_high=pred.get("offer_high"),
                predicted_review=bool(pred.get("human_review_required", True)),
                label_should_pursue=bool(lbl_should) if lbl_should is not None else None,
                label_offer_low=float(lbl_low) if lbl_low is not None else None,
                label_offer_high=float(lbl_high) if lbl_high is not None else None,
                label_review=bool(lbl_review) if lbl_review is not None else None,
                label_risk=lbl_risk
            ))

    # Metrics
    n = len(results)
    if n == 0:
        die("No records replayed.")

    tp = fp = tn = fn = 0
    review_rate = 0
    pursue_rate = 0

    for r in results:
        if r.predicted_review:
            review_rate += 1
        if r.predicted_should_pursue:
            pursue_rate += 1

        # Only score classification if labels exist
        if r.label_should_pursue is None:
            continue

        if r.predicted_should_pursue and r.label_should_pursue:
            tp += 1
        elif r.predicted_should_pursue and not r.label_should_pursue:
            fp += 1
        elif not r.predicted_should_pursue and not r.label_should_pursue:
            tn += 1
        elif not r.predicted_should_pursue and r.label_should_pursue:
            fn += 1

    denom = (tp + fp + tn + fn) or 1
    accuracy = (tp + tn) / denom
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0

    print("\n=== SANDBOX REPLAY REPORT (WHOLESALING) ===")
    print(f"Records replayed: {n}")
    print(f"Pursue rate: {pursue_rate/n:.2%}")
    print(f"Review rate: {review_rate/n:.2%}")
    print(f"Accuracy (where labeled): {accuracy:.2%}")
    print(f"Precision: {precision:.2%}")
    print(f"Recall: {recall:.2%}")
    print(f"TP/FP/TN/FN: {tp}/{fp}/{tn}/{fn}")
    print("==========================================\n")
    print("Next tuning levers:")
    print("- If pursue rate is too high: tighten thresholds / default review")
    print("- If FP is high: increase rejection, add risk gates, cap offers")
    print("- If FN is high: allow more borderline cases to 'review' not 'skip'")

if __name__ == "__main__":
    main()
