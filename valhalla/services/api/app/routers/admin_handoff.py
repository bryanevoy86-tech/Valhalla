import time

from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

router = APIRouter(prefix="/admin/handoff", tags=["handoff"])


@router.get("/summary")
def summary():
    # toy: static text, in practice pull from Prom + Alertmanager
    txt = f"Valhalla On-Call Handoff\nGenerated {time.ctime()}\n\nOpen alerts: 0\nLast 24h incidents: HighErrorRate path=/api\n"
    return PlainTextResponse(txt)
