from fastapi import FastAPI, Response
from fastapi.responses import JSONResponse
from app.core.policy.router import router as policy_router

app = FastAPI(title="Valhalla API", version="0.1.0")

# Register policy router
app.include_router(policy_router)


@app.api_route("/", methods=["GET", "HEAD"])
def root(_: Response):
    # Render/uptime monitors often send HEAD /
    return {"ok": True, "service": "valhalla-api"}


@app.get("/health", summary="Health check")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/healthz", summary="Health check alias")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


# Optional: make 404s easier to recognize in logs
@app.exception_handler(404)
def not_found(_, __):
    return JSONResponse(status_code=404, content={"detail": "Not Found"})
