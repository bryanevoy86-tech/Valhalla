# services/api/tools/public_training/generate_synthetic_outcomes.py
import os
from sqlalchemy import create_engine, text

def die(msg: str):
    raise SystemExit(f"[generate_synthetic_outcomes] {msg}")

def main():
    app_env = os.getenv("APP_ENV", "dev").lower()
    if app_env not in ("sandbox", "dev"):
        die(f"Refusing to label training data in APP_ENV={app_env}. Set APP_ENV=sandbox.")

    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        die("DATABASE_URL not set")

    engine = create_engine(db_url, future=True)

    # Conservative global constants (tune later)
    # Goal: reject most deals, flag uncertainty, cap offers.
    MAX_OFFER_TO_ASSESSMENT = 0.78   # cap offer band at 78% of assessed value (conservative)
    MIN_OFFER_TO_ASSESSMENT = 0.60   # low end
    HIGH_RISK_ASSESSMENT_CEILING = 120000  # example: low value bands may be volatile; adjust per city later

    with engine.begin() as conn:
        rows = conn.execute(text("""
            SELECT source, external_id, assessed_value, city, province
            FROM public_training_properties
            WHERE assessed_value IS NOT NULL
            LIMIT 200000
        """)).fetchall()

        upserts = 0
        for source, external_id, assessed_value, city, province in rows:
            av = float(assessed_value)

            # Risk logic (simple & conservative)
            risk = "medium"
            review = True
            should_pursue = False
            confidence = 0.35

            if av < HIGH_RISK_ASSESSMENT_CEILING:
                risk = "high"
                review = True
                should_pursue = False
                confidence = 0.25
            else:
                # Still conservative: most records require review; only pursue if valuation stable enough
                risk = "medium"
                review = True
                should_pursue = False
                confidence = 0.40

                # Allow a small subset to be "pursue" to test pipeline behavior
                # You will tighten this later based on replay metrics.
                if av >= 250000:
                    risk = "low"
                    review = True  # keep review on even for low risk early
                    should_pursue = True
                    confidence = 0.55

            offer_low = av * MIN_OFFER_TO_ASSESSMENT
            offer_high = av * MAX_OFFER_TO_ASSESSMENT

            conn.execute(text("""
                INSERT INTO public_training_labels
                (source, external_id, risk_level, should_pursue, offer_low, offer_high, human_review_required, confidence, outcome_type)
                VALUES
                (:source, :external_id, :risk_level, :should_pursue, :offer_low, :offer_high, :review, :confidence, 'synthetic')
                ON CONFLICT (source, external_id) DO UPDATE SET
                  risk_level=EXCLUDED.risk_level,
                  should_pursue=EXCLUDED.should_pursue,
                  offer_low=EXCLUDED.offer_low,
                  offer_high=EXCLUDED.offer_high,
                  human_review_required=EXCLUDED.human_review_required,
                  confidence=EXCLUDED.confidence,
                  outcome_type='synthetic';
            """), {
                "source": source,
                "external_id": external_id,
                "risk_level": risk,
                "should_pursue": should_pursue,
                "offer_low": offer_low,
                "offer_high": offer_high,
                "review": review,
                "confidence": confidence
            })
            upserts += 1

    print(f"[generate_synthetic_outcomes] Labeled {upserts} records (synthetic).")

if __name__ == "__main__":
    main()
