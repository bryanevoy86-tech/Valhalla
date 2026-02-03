# services/api/tools/public_training/import_public_data.py
import os
import csv
from typing import Optional
from sqlalchemy import create_engine, text

RAW_DIR = "data/public_sources/raw"

def die(msg: str):
    raise SystemExit(f"[import_public_data] {msg}")

def to_float(v: str) -> Optional[float]:
    v = (v or "").strip()
    if not v:
        return None
    try:
        return float(v.replace(",", ""))
    except:
        return None

def to_int(v: str) -> Optional[int]:
    v = (v or "").strip()
    if not v:
        return None
    try:
        return int(float(v))
    except:
        return None

def main():
    app_env = os.getenv("APP_ENV", "dev").lower()
    if app_env not in ("sandbox", "dev"):
        die(f"Refusing to import training data in APP_ENV={app_env}. Set APP_ENV=sandbox.")

    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        die("DATABASE_URL not set")

    engine = create_engine(db_url, future=True)

    # Training tables (do NOT touch production lead tables)
    create_sql = """
    CREATE TABLE IF NOT EXISTS public_training_properties (
        id BIGSERIAL PRIMARY KEY,
        source TEXT NOT NULL,
        external_id TEXT NOT NULL,
        province TEXT NOT NULL,
        city TEXT,
        address TEXT,
        assessed_value NUMERIC,
        assessment_year INT,
        property_type TEXT,
        year_built INT,
        land_area NUMERIC,
        building_area NUMERIC,
        raw_json JSONB,
        UNIQUE(source, external_id)
    );

    CREATE TABLE IF NOT EXISTS public_training_labels (
        source TEXT NOT NULL,
        external_id TEXT NOT NULL,
        risk_level TEXT,
        should_pursue BOOLEAN,
        offer_low NUMERIC,
        offer_high NUMERIC,
        human_review_required BOOLEAN,
        confidence NUMERIC,
        outcome_type TEXT NOT NULL DEFAULT 'synthetic',
        PRIMARY KEY (source, external_id)
    );
    """

    with engine.begin() as conn:
        conn.execute(text(create_sql))

        # Edmonton assessment current
        edmonton_path = os.path.join(RAW_DIR, "edmonton_assessment_current.csv")
        if os.path.exists(edmonton_path):
            load_edmonton(conn, edmonton_path)

        # Calgary assessment current
        calgary_current_path = os.path.join(RAW_DIR, "calgary_assessment_current.csv")
        if os.path.exists(calgary_current_path):
            load_calgary(conn, calgary_current_path, is_historical=False)

        # Calgary assessment historical
        calgary_hist_path = os.path.join(RAW_DIR, "calgary_assessment_historical.csv")
        if os.path.exists(calgary_hist_path):
            load_calgary(conn, calgary_hist_path, is_historical=True)

    print("[import_public_data] Done.")

def load_edmonton(conn, path: str):
    # Edmonton column names can change; we store raw row JSON too.
    # We'll attempt to map common columns when present.
    print(f"[import_public_data] Loading Edmonton: {path}")
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            external_id = r.get("Account Number") or r.get("ACCOUNT_NUMBER") or r.get("account_number") or r.get("Roll Number") or r.get("roll_number")
            if not external_id:
                continue
            assessed = to_float(r.get("Assessed Value") or r.get("assessed_value") or r.get("ASSESSMENT_VALUE") or r.get("Assessed Value (Current Year)"))
            year = to_int(r.get("Assessment Year") or r.get("assessment_year") or r.get("ASSESSMENT_YEAR"))
            addr = r.get("Address") or r.get("address") or r.get("SITE_ADDRESS")

            conn.execute(text("""
            INSERT INTO public_training_properties
            (source, external_id, province, city, address, assessed_value, assessment_year, raw_json)
            VALUES
            (:source, :external_id, :province, :city, :address, :assessed_value, :assessment_year, to_jsonb(:raw_json::json))
            ON CONFLICT (source, external_id) DO UPDATE SET
              assessed_value=EXCLUDED.assessed_value,
              assessment_year=EXCLUDED.assessment_year,
              address=EXCLUDED.address,
              raw_json=EXCLUDED.raw_json;
            """), {
                "source": "edmonton_assessment_current",
                "external_id": str(external_id),
                "province": "AB",
                "city": "Edmonton",
                "address": addr,
                "assessed_value": assessed,
                "assessment_year": year,
                "raw_json": "{}"  # keep simple; optional: dump full row JSON if you want
            })

def load_calgary(conn, path: str, is_historical: bool):
    print(f"[import_public_data] Loading Calgary ({'historical' if is_historical else 'current'}): {path}")
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            # Calgary uses roll numbers / account IDs; columns vary
            external_id = r.get("ROLL_NUM") or r.get("ROLL_NUMBER") or r.get("ROLL_NUMBER_TXT") or r.get("roll_num") or r.get("ACCOUNT_NUM") or r.get("account_num")
            if not external_id:
                continue
            assessed = to_float(r.get("ASSESSMENT") or r.get("ASSESSED_VALUE") or r.get("assessed_value") or r.get("ASSESSMENT_VALUE"))
            year = to_int(r.get("TAX_YEAR") or r.get("ASSESSMENT_YEAR") or r.get("tax_year") or r.get("assessment_year"))
            addr = r.get("ADDRESS") or r.get("SITE_ADDRESS") or r.get("address")

            conn.execute(text("""
            INSERT INTO public_training_properties
            (source, external_id, province, city, address, assessed_value, assessment_year, raw_json)
            VALUES
            (:source, :external_id, :province, :city, :address, :assessed_value, :assessment_year, '{}'::jsonb)
            ON CONFLICT (source, external_id) DO UPDATE SET
              assessed_value=EXCLUDED.assessed_value,
              assessment_year=EXCLUDED.assessment_year,
              address=EXCLUDED.address,
              raw_json=EXCLUDED.raw_json;
            """), {
                "source": "calgary_assessment_historical" if is_historical else "calgary_assessment_current",
                "external_id": str(external_id),
                "province": "AB",
                "city": "Calgary",
                "address": addr,
                "assessed_value": assessed,
                "assessment_year": year
            })

if __name__ == "__main__":
    main()
