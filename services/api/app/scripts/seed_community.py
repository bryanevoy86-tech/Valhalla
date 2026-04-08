import sys
from pathlib import Path

from app.core.db import SessionLocal
from app.seeds.community_seed import seed_community


def main():
    db = SessionLocal()
    try:
        seed_community(db)
        db.commit()
        print("✓ Community seed completed successfully.")
    except Exception as e:
        db.rollback()
        print(f"✗ Community seed failed: {e}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
