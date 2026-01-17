from fastapi import APIRouter

router = APIRouter(prefix="/shield", tags=["shield"])


@router.get("/health")
def health():
    return {"ok": True, "module": "shield"}
