"""PACK 88: Training Engine - Service"""

from sqlalchemy.orm import Session

from app.models.training import TrainingModule, TrainingProgress
from app.schemas.training import TrainingModuleCreate, TrainingProgressCreate


# Training module operations
def create_training_module(db: Session, module: TrainingModuleCreate) -> TrainingModule:
    db_module = TrainingModule(
        title=module.title,
        difficulty=module.difficulty,
        content_payload=module.content_payload
    )
    db.add(db_module)
    db.commit()
    db.refresh(db_module)
    return db_module


def list_training_modules(db: Session) -> list[TrainingModule]:
    return db.query(TrainingModule).order_by(TrainingModule.id.desc()).all()


def get_training_module(db: Session, module_id: int) -> TrainingModule | None:
    return db.query(TrainingModule).filter(TrainingModule.id == module_id).first()


def update_training_module(db: Session, module_id: int, module: TrainingModuleCreate) -> TrainingModule | None:
    db_module = get_training_module(db, module_id)
    if not db_module:
        return None
    db_module.title = module.title
    db_module.difficulty = module.difficulty
    db_module.content_payload = module.content_payload
    db.commit()
    db.refresh(db_module)
    return db_module


def delete_training_module(db: Session, module_id: int) -> bool:
    db_module = get_training_module(db, module_id)
    if not db_module:
        return False
    db.delete(db_module)
    db.commit()
    return True


# Training progress operations
def create_progress(db: Session, progress: TrainingProgressCreate) -> TrainingProgress:
    db_progress = TrainingProgress(
        user_id=progress.user_id,
        module_id=progress.module_id,
        completion_pct=progress.completion_pct,
        status=progress.status
    )
    db.add(db_progress)
    db.commit()
    db.refresh(db_progress)
    return db_progress


def list_progress(db: Session, user_id: int | None = None) -> list[TrainingProgress]:
    q = db.query(TrainingProgress)
    if user_id:
        q = q.filter(TrainingProgress.user_id == user_id)
    return q.order_by(TrainingProgress.id.desc()).all()


def get_progress(db: Session, progress_id: int) -> TrainingProgress | None:
    return db.query(TrainingProgress).filter(TrainingProgress.id == progress_id).first()


def update_progress(db: Session, progress_id: int, progress: TrainingProgressCreate) -> TrainingProgress | None:
    db_progress = get_progress(db, progress_id)
    if not db_progress:
        return None
    db_progress.user_id = progress.user_id
    db_progress.module_id = progress.module_id
    db_progress.completion_pct = progress.completion_pct
    db_progress.status = progress.status
    db.commit()
    db.refresh(db_progress)
    return db_progress


def delete_progress(db: Session, progress_id: int) -> bool:
    db_progress = get_progress(db, progress_id)
    if not db_progress:
        return False
    db.delete(db_progress)
    db.commit()
    return True
