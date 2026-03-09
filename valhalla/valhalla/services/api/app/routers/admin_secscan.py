from fastapi import APIRouter
router = APIRouter()
@router.get("/admin/secscan")
def get_admin_secscan():
    return {"message": "admin_secscan works"}
