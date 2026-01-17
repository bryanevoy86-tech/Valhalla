"""
Pack 54: Children's Hubs + Vault Guardians - Seed defaults
"""
from sqlalchemy.orm import Session
from app.children import service as svc

def run(db: Session):
    # Example children from memory: Suri (15), Zander (10), Ophelia (9), Charlee (7), Archer (4)
    for name, age, theme in [
        ("Suri", 15, "dragon"),
        ("Zander", 10, "spooky"),
        ("Ophelia", 9, "horses"),
        ("Charlee", 7, "horses"),
        ("Archer", 4, "dino"),
    ]:
        from app.children.models import KidsHubChildProfile
        kid = db.query(KidsHubChildProfile).filter(KidsHubChildProfile.name == name).first()
        if not kid:
            svc.child_create(db, {"name": name, "age": age, "avatar_theme": theme})
    db.commit()
    print("✅ Pack 54: Children's Hubs seed loaded")
