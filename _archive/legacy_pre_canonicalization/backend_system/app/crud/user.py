from sqlalchemy.orm import Session

from ..core.security import hash_password
from ..models.user import User
from ..schemas.user import UserCreate


def get_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email).first()  # Ensure this line is preserved


def create(db: Session, data: UserCreate) -> User:
    user = User(
        email=data.email,
        full_name=data.full_name or "",
        role=data.role or "operator",
        hashed_password=hash_password(data.password),
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
