from __future__ import annotations

from fastapi import APIRouter, HTTPException
from . import service

router = APIRouter(prefix="/core/entity_checklists", tags=["core-entity-checklists"])

@router.post("/apply")
def apply(entity_id: str, template: str, due_days: int = 30, create_followups: bool = True):
    try:
        return service.apply_template(entity_id=entity_id, template=template, due_days=due_days, create_followups=create_followups)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
