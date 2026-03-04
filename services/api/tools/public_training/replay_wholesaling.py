# services/api/tools/public_training/replay_wholesaling.py
import os
from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from sqlalchemy import create_engine, text

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

# --------------- ADAPTER YOU WIRE ONCE ---------------
def run_wholesaling_pipeline(lead: Dict[str, Any]) -> Dict[str, Any]:
    """
    TODO: Wire this to your actual wholesaling code.
    Must return a dict like:
      {
        "should_pursue": bool,
        "offer_low": float|None,
        "offer_high": float|None,
        "human_review_required": bool
      }

    Example pseudo-import (replace with your real entrypoint):
      from deals.scoring import score_lead
      from deals.offer import suggest_offer_band
    """
    # Safe fallback (never pursue by default)
    return {
        "should_pursue": False,
        "offer_low": None,
        "offer_high": None,
        "human_review_required": True
    }
# ----------------------------------------------------

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
