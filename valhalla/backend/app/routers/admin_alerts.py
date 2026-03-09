
import os
import time
import httpx
from fastapi import APIRouter, Header, HTTPException, Request


router = APIRouter(prefix="/admin/alerts", tags=["admin-alerts"])

GFX_EN = os.getenv("GRAFANA_ANNOTATE_ENABLED", "false").lower() in ("1", "true", "yes")
GFX_URL = os.getenv("GRAFANA_ANNOTATE_URL", "").rstrip("/")
GFX_TOKEN = os.getenv("GRAFANA_ANNOTATE_TOKEN", "")


@router.post("/grafana-annotate")
async def grafana_annotate(
    request: Request, x_alertmanager_token: str | None = Header(default=None)
) -> dict:
    if not GFX_EN:
        raise HTTPException(status_code=404, detail="disabled")

    payload: dict = await request.json()
    title: str = payload.get("commonLabels", {}).get("alertname", "alert")
    state: str = payload.get("status", "firing")
    summary: str = payload.get("commonAnnotations", {}).get("summary") or payload.get(
        "commonAnnotations", {}
    ).get("description", "")
    tags: list[str] = ["alert", state, payload.get("commonLabels", {}).get("severity", "")]

    ts_ms: int = int(time.time() * 1000)
    body: dict = {"time": ts_ms, "tags": [t for t in tags if t], "text": f"{title}: {summary}"}

    headers: dict = {"Authorization": f"Bearer {GFX_TOKEN}"} if GFX_TOKEN else {}
    async with httpx.AsyncClient(timeout=8) as cli:
        r = await cli.post(GFX_URL, json=body, headers=headers)
        r.raise_for_status()
    return {"ok": True}
