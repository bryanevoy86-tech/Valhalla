import csv
import io
import os
import time

import httpx
from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse, PlainTextResponse

router = APIRouter(prefix="/admin/health", tags=["admin-health"])

EN = os.getenv("HEALTH_ENABLED", "false").lower() in ("1", "true", "yes")
PROM = os.getenv("TRIAGE_PROM_URL", "http://prometheus:9090").rstrip("/")
W_P95 = float(os.getenv("HEALTH_WEIGHTS_P95", "0.35"))
W_5XX = float(os.getenv("HEALTH_WEIGHTS_5XX", "0.35"))
W_BURN = float(os.getenv("HEALTH_WEIGHTS_BURN", "0.20"))
W_JOBS = float(os.getenv("HEALTH_WEIGHTS_JOBS", "0.10"))
WIN_D = int(os.getenv("HEALTH_REPORT_WINDOW_DAYS", "7"))


async def q(expr):
    async with httpx.AsyncClient(timeout=8) as cli:
        r = await cli.get(f"{PROM}/api/v1/query", params={"query": expr})
        r.raise_for_status()
        d = r.json()
        if d.get("status") != "success":
            return 0.0
        res = d["data"]["result"]
        if not res:
            return 0.0
        return float(res[0]["value"][1])


def clamp01(x):
    return max(0.0, min(1.0, x))


@router.get("/score")
async def score():
    if not EN:
        return JSONResponse({"ok": False, "error": "disabled"}, status_code=404)
    p95 = await q(
        "histogram_quantile(0.95, sum by (le)(rate(valhalla_http_request_duration_seconds_bucket[5m])))"
    )
    err = await q("sum(rate(valhalla_http_errors_total[5m]))")
    burn = await q("sum(valhalla:burnrate:30m)")
    jobe = await q('sum(rate(valhalla_jobs_runs_total{status="ERROR"}[15m]))')
    s_p95 = clamp01(1.0 - (p95 / 1.0))
    s_5xx = clamp01(1.0 - (err / 1.0))
    s_burn = clamp01(1.0 - (burn / 6.0))
    s_jobs = clamp01(1.0 - (jobe / 0.5))
    score = round(100 * (W_P95 * s_p95 + W_5XX * s_5xx + W_BURN * s_burn + W_JOBS * s_jobs), 1)
    return {
        "score": score,
        "components": {"p95": s_p95, "5xx": s_5xx, "burn": s_burn, "jobs": s_jobs},
    }


@router.get("/report.csv")
async def report_csv(days: int = Query(None, ge=1, le=30)):
    if not EN:
        return PlainTextResponse("disabled", status_code=404)
    days = days or WIN_D
    step = 3600
    now = int(time.time())
    start = now - days * 86400
    buf = io.StringIO()
    cw = csv.writer(buf)
    cw.writerow(["timestamp", "score"])
    for t in range(start, now + 1, step):

        async def q_at(expr):
            return await q(expr + f" @ {t}")

        p95 = await q_at(
            "histogram_quantile(0.95, sum by (le)(rate(valhalla_http_request_duration_seconds_bucket[5m])))"
        )
        err = await q_at("sum(rate(valhalla_http_errors_total[5m]))")
        burn = await q_at("sum(valhalla:burnrate:30m)")
        jobe = await q_at('sum(rate(valhalla_jobs_runs_total{status="ERROR"}[15m]))')
        s = round(
            100
            * (
                W_P95 * clamp01(1 - (p95 / 1.0))
                + W_5XX * clamp01(1 - (err / 1.0))
                + W_BURN * clamp01(1 - (burn / 6.0))
                + W_JOBS * clamp01(1 - (jobe / 0.5))
            ),
            1,
        )
        cw.writerow([t, s])
    return PlainTextResponse(buf.getvalue(), media_type="text/csv")
