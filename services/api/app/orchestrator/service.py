from sqlalchemy.orm import Session
from typing import List, Optional
from app.orchestrator.models import LegacyInstance, ClonePlan, MirrorLink
from app.orchestrator.schemas import LegacyInstanceCreate, ClonePlanCreate, MirrorLinkCreate
from app.audit.schemas import AuditEventCreate
from app.audit.service import log_event


def create_instance(db: Session, payload: LegacyInstanceCreate) -> LegacyInstance:
    inst = LegacyInstance(**payload.dict())
    db.add(inst)
    db.commit()
    db.refresh(inst)
    log_event(
        db,
        payload=AuditEventCreate(
            actor="heimdall-bot",
            action="instance.create",
            target=f"legacy:{inst.id}",
            result="success",
            meta=payload.dict(),
        ),
    )
    return inst


def list_instances(db: Session) -> List[LegacyInstance]:
    return db.query(LegacyInstance).order_by(LegacyInstance.id.desc()).all()


def request_clone(db: Session, payload: ClonePlanCreate) -> ClonePlan:
    plan = ClonePlan(**payload.dict(), status="queued")
    db.add(plan)
    db.commit()
    db.refresh(plan)
    log_event(
        db,
        payload=AuditEventCreate(
            actor="heimdall-bot",
            action="clone.plan",
            target=f"clone:{plan.id}",
            result="success",
            meta=payload.dict(),
        ),
    )
    return plan


def mark_clone_status(
    db: Session, plan_id: int, status: str, result: Optional[dict] = None
) -> Optional[ClonePlan]:
    plan = db.get(ClonePlan, plan_id)
    if not plan:
        return None
    plan.status = status
    plan.result = result
    db.commit()
    db.refresh(plan)
    return plan


def create_mirror(db: Session, payload: MirrorLinkCreate) -> MirrorLink:
    link = MirrorLink(**payload.dict())
    db.add(link)
    db.commit()
    db.refresh(link)
    log_event(
        db,
        payload=AuditEventCreate(
            actor="heimdall-bot",
            action="mirror.link",
            target=f"mirror:{link.id}",
            result="success",
            meta=payload.dict(),
        ),
    )
    return link


def list_mirrors(db: Session) -> List[MirrorLink]:
    return db.query(MirrorLink).all()
