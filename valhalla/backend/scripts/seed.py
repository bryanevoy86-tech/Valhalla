import datetime
import random

from backend.db.models import Deal, Legacy, Notification, Org, OrgMember, User
from backend.db.session import SessionLocal
from sqlalchemy.orm import Session


def main():
    db: Session = SessionLocal()

    # org
    org = db.query(Org).filter(Org.slug == "valhalla").first()
    if not org:
        org = Org(slug="valhalla", name="Valhalla Legacy Inc")
        db.add(org)
        db.commit()
        db.refresh(org)

    # users
    owner = db.query(User).filter(User.email == "owner@example.com").first()
    if not owner:
        owner = User(email="owner@example.com", role="admin", plan_key="pro_monthly")
        db.add(owner)
        db.commit()
        db.refresh(owner)

    # membership
    if (
        not db.query(OrgMember)
        .filter(OrgMember.org_id == org.id, OrgMember.user_id == owner.id)
        .first()
    ):
        db.add(OrgMember(org_id=org.id, user_id=owner.id, role="owner"))
        db.commit()

    # legacies
    for i in range(1, 4):
        slug = f"legacy-{i}"
        row = db.query(Legacy).filter(Legacy.slug == slug).first()
        if not row:
            row = Legacy(slug=slug, name=f"Legacy {i}", org_id=org.id)
            db.add(row)
    db.commit()

    # deals (random)
    statuses = ["draft", "pending", "active", "closed", "lost"]
    cities = ["Austin", "Toronto", "Nashville", "Phoenix", "Tampa"]
    states = ["TX", "ON", "TN", "AZ", "FL"]
    for i in range(30):
        d = Deal(
            org_id=org.id,
            legacy_id=None,
            status=random.choice(statuses),
            city=random.choice(cities),
            state=random.choice(states),
            price=random.randint(50_000, 500_000),
            created_at=datetime.datetime.utcnow() - datetime.timedelta(days=random.randint(0, 90)),
        )
        db.add(d)
    db.commit()

    # notifications
    for i in range(3):
        n = Notification(
            org_id=org.id,
            user_id=owner.id,
            channel="in-app",
            topic="deal",
            title=f"Deal event #{i+1}",
            body="Sample notification",
            unread=True,
        )
        db.add(n)
    db.commit()

    print("Seeded: org, user, memberships, legacies, deals, notifications.")


if __name__ == "__main__":
    main()
