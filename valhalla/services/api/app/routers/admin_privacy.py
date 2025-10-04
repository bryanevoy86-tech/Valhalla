from fastapi import APIRouter
router = APIRouter()
@router.get("/admin/privacy")
def get_admin_privacy():
    return {"message": "admin_privacy works"}
