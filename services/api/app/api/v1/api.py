from fastapi import APIRouter
from .endpoints import root   # ⬅ relative import, no more VS Code whining
from app.routers.loki import router as loki_router

api_router = APIRouter()
api_router.include_router(root.router, prefix="", tags=["Root"])
api_router.include_router(loki_router)