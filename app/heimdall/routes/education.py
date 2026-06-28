from fastapi import APIRouter
from app.heimdall.education.heimdall_education_loader import load_heimdall_education_layer

router = APIRouter(prefix="/heimdall/education", tags=["Heimdall Education"])


@router.get("/base")
def get_heimdall_education_base():
    """
    Returns Heimdall's education layer: trusted sources, error-catcher rules, and deal scoring framework.
    """
    return load_heimdall_education_layer()
