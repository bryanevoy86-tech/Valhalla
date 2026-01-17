from fastapi import APIRouter

from .models import GoChecklist, GoNext, CompleteStepRequest
from .service import build_checklist, next_step, complete_step

router = APIRouter(prefix="/go", tags=["Core: Go"])

@router.get("/checklist", response_model=GoChecklist)
def checklist():
    return build_checklist()

@router.get("/next_step", response_model=GoNext)
def get_next_step():
    return next_step()

@router.post("/complete")
def complete(payload: CompleteStepRequest):
    return complete_step(payload.step_id, payload.done, payload.notes)
