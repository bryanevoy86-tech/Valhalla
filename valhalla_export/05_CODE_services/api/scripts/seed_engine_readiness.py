"""
Seed engine readiness with safe defaults.

Run after migration: 
  python -m services.api.scripts.seed_engine_readiness
"""

from sqlalchemy.orm import Session
from app.core.db import SessionLocal
from app.models.engine_readiness import EngineReadiness


def seed_engines():
    db = SessionLocal()
    
    try:
        # Check if already seeded
        count = db.query(EngineReadiness).count()
        if count > 0:
            print(f"Engines already seeded ({count} rows). Skipping.")
            return
        
        # Initialize with safe defaults
        engines = [
            EngineReadiness(engine_name="wholesaling", state="SANDBOX"),
            EngineReadiness(engine_name="arbitrage", state="DISABLED"),
            EngineReadiness(engine_name="trading_advisory", state="DISABLED"),
        ]
        
        db.add_all(engines)
        db.commit()
        
        print("✅ Engine readiness seeded:")
        for engine in engines:
            print(f"   - {engine.engine_name}: {engine.state}")
    
    except Exception as e:
        db.rollback()
        print(f"❌ Seeding failed: {e}")
    
    finally:
        db.close()


if __name__ == "__main__":
    seed_engines()
