"""
Generate synthetic training data for SANDBOX replay testing.
Creates realistic property assessments and synthetic labels.
"""
import os
import sys
from pathlib import Path
from sqlalchemy import create_engine, text

def die(msg: str):
    print(f"[ERROR] {msg}")
    sys.exit(1)

def main():
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        die("DATABASE_URL not set")

    print("[*] Connecting to database...")
    engine = create_engine(db_url, future=True)
    
    # Generate synthetic properties
    print("[*] Generating synthetic properties...")
    properties = []
    for i in range(2000):
        # Vary assessed values across realistic ranges
        region = i % 3  # Calgary=0, Edmonton=1, Other=2
        if region == 0:
            assessed_value = 150000 + (i % 500) * 100  # Calgary: 150k-200k range
        elif region == 1:
            assessed_value = 120000 + (i % 400) * 100  # Edmonton: 120k-160k range
        else:
            assessed_value = 180000 + (i % 600) * 100  # Other: 180k-240k range
        
        properties.append({
            "source": f"synthetic_{region}",
            "external_id": f"SYNTH_{i:04d}",
            "province": ["AB", "AB", "MB"][region],
            "city": ["Calgary", "Edmonton", "Winnipeg"][region],
            "address": f"{100+i} Main St",
            "assessed_value": assessed_value,
            "assessment_year": 2024,
            "property_type": "residential",
            "year_built": 1950 + (i % 70),
            "land_area": 5000 + (i % 10000),
            "building_area": 1500 + (i % 3000),
        })
    
    print(f"[*] Generated {len(properties)} synthetic properties")
    
    # Insert into DB
    print("[*] Inserting into public_training_properties...")
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM public_training_properties"))
        for prop in properties:
            conn.execute(text("""
                INSERT INTO public_training_properties 
                (source, external_id, province, city, address, assessed_value, 
                 assessment_year, property_type, year_built, land_area, building_area)
                VALUES (:source, :external_id, :province, :city, :address, :assessed_value,
                        :assessment_year, :property_type, :year_built, :land_area, :building_area)
            """), prop)
        
        # Create synthetic labels (conservative defaults)
        conn.execute(text("DELETE FROM public_training_labels"))
        for prop in properties:
            # Synthetic label: most things require review, few are pursued
            assessed = prop["assessed_value"]
            should_pursue = assessed > 200000  # Only pursue high-value
            
            conn.execute(text("""
                INSERT INTO public_training_labels
                (source, external_id, should_pursue, offer_low, offer_high, 
                 human_review_required, risk_level)
                VALUES (:source, :external_id, :should_pursue, :offer_low, :offer_high,
                        :review, :risk)
            """), {
                "source": prop["source"],
                "external_id": prop["external_id"],
                "should_pursue": should_pursue,
                "offer_low": assessed * 0.60,
                "offer_high": assessed * 0.78,
                "review": True,
                "risk": "medium",
            })
    
    print(f"[✓] Inserted {len(properties)} training records")

if __name__ == "__main__":
    main()
