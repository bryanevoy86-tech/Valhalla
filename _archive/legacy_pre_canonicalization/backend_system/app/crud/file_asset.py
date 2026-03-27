from sqlalchemy.orm import Session

from ..models.file_asset import FileAsset


def create(
    db: Session,
    *,
    key: str,
    filename: str,
    content_type: str,
    size: int,
    legacy_id: str,
    user_id: int,
) -> FileAsset:
    obj = FileAsset(
        key=key,
        filename=filename,
        content_type=content_type,
        size=size,
        legacy_id=legacy_id,
        created_by=user_id,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def list_all(db: Session, limit: int = 100, offset: int = 0, legacy_id: str | None = None):
    q = db.query(FileAsset)
    if legacy_id:
        q = q.filter(FileAsset.legacy_id == legacy_id)
    return q.order_by(FileAsset.id.desc()).offset(offset).limit(limit).all()


def get_by_key(db: Session, key: str) -> FileAsset | None:
    return db.query(FileAsset).filter(FileAsset.key == key).first()


def get_by_id(db: Session, file_id: int) -> FileAsset | None:
    return db.query(FileAsset).get(file_id)
