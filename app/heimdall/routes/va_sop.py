from fastapi import APIRouter

from app.heimdall.services.va_sop_service import (
    get_task_sop,
)

router = APIRouter(
    prefix="/heimdall/va-sop",
    tags=["Heimdall VA SOP"],
)


@router.get("/{task_title}")
def task_sop(task_title: str):
    return get_task_sop(task_title)
