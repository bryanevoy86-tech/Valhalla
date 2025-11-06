from sqlalchemy.orm import Session
from datetime import datetime
from .models import Closer
from .schemas import CloserCreate


def create_closer(db: Session, closer: CloserCreate) -> Closer:
    db_closer = Closer(
        name=closer.name,
        success_rate=closer.success_rate,
        last_interaction=closer.last_interaction or datetime.utcnow(),
        current_target=closer.current_target,
    )
    db.add(db_closer)
    db.commit()
    db.refresh(db_closer)
    return db_closer


def get_closers(db: Session) -> list[Closer]:
    return db.query(Closer).all()
