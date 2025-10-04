
import os
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

origins = [o.strip() for o in os.getenv("CORS_ALLOWED_ORIGINS", "").split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["Authorization", "Content-Type", "X-Requested-With"],
)

@app.get("/healthz")
def healthz():
    return {"ok": True}

@app.get("/")
def read_root():
    return {"message": "Valhalla API online"}

try:
    from valhalla.services.api.routers.features import router as features_router
    app.include_router(features_router)
except Exception:
    pass

