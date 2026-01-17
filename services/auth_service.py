"""
Compatibility wrapper.

This file previously contained demo-style hard-coded credentials and a default JWT secret.
It now mounts the real owner-auth router from the main API security module.

If you accidentally run:
    uvicorn services.auth_service:app --reload
…it will still work, but ONLY via env vars (no hard-coded secrets).
"""

from __future__ import annotations

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from services.api.app.security.auth import router as ops_router  # /ops/token, /ops/me


app = FastAPI(
    title="Valhalla Auth Wrapper",
    version="1.0.0",
)

cors = (os.getenv("CORS_ALLOWED_ORIGINS") or "http://localhost,http://localhost:3000").strip()
allow_origins = [o.strip() for o in cors.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)

app.include_router(ops_router)

# OAuth2 scheme for token-based authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class User(BaseModel):
    """User model for login"""
    username: str = Field(..., description="Username for authentication")
    password: str = Field(..., description="Password for authentication")

