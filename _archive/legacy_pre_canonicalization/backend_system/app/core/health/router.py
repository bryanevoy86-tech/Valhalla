from __future__ import annotations

import os
from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/healthz")
def healthz():
    return {"ok": True}


@router.get("/version")
def version():
    return {
        "git_sha": os.getenv("GIT_SHA", "unknown"),
        "release": os.getenv("RELEASE", "dev"),
    }


@router.get("/readyz")
def readyz():
    # If you have a DB session helper, you can add a DB ping here later.
    # Keeping it dependency-light for now.
    return {"ready": True}
