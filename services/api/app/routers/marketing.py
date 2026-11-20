"""Mount the historical Pack 87 marketing registry under explicit owner auth.

This registers campaigns/posts with Valhalla. These endpoints DO NOT publish
to social platforms and must not report that an external post was sent.
"""
from fastapi import APIRouter, Depends

from app.core.dependencies import require_builder_key
from app.routes.marketing import router as campaign_registry_router

router = APIRouter(dependencies=[Depends(require_builder_key)])
router.include_router(campaign_registry_router)
