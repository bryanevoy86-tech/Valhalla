from fastapi import APIRouter
from app.heimdall.knowledge.knowledge_loader import load_heimdall_knowledge_base

router = APIRouter(prefix="/heimdall/knowledge", tags=["Heimdall Knowledge"])


@router.get("/base")
def get_heimdall_knowledge_base():
    """
    Returns Heimdall's trusted source registry and base decision rules.
    """
    return load_heimdall_knowledge_base()
