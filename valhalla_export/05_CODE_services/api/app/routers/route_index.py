"""
PACK TY: Route Index & Debug Explorer Router
Prefix: /debug/routes
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.route_index import RouteIndex
from app.services.route_index import build_route_index

router = APIRouter(prefix="/debug/routes", tags=["Debug"])


def get_app():
    from app.main import app
    return app


@router.get("/", response_model=RouteIndex)
def list_routes(
    app=Depends(get_app),
    db: Session = Depends(get_db),
):
    """
    Returns an index of all API routes.

    Heimdall can use this to:
    - discover capabilities
    - verify that packs are mounted
    - generate higher-level maps.
    """
    return build_route_index(app)
