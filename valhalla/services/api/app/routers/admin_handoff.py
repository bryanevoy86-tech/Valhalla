from fastapi import APIRouter
router = APIRouter()
@router.get("/admin/handoff")
def get_admin_handoff():
    return {"message": "admin_handoff works"}
