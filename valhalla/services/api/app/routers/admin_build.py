from fastapi import APIRouter
router = APIRouter()
@router.get("/admin/build")
def get_admin_build():
    return {"message": "admin_build works"}
