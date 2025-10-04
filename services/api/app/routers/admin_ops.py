import asyncio
import os
import time
import urllib.parse

import httpx
from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/admin/ops", tags=["admin-ops"])

ENABLED = os.getenv("TRIAGE_ENABLED","false").lower() in ("1","true","yes")
PROM = os.getenv("TRIAGE_PROM_URL","http://localhost:9090").rstrip("/")
GRAFANA = os.getenv("TRIAGE_GRAFANA_URL","").rstrip("/")
TEMPO = os.getenv("TRIAGE_TEMPO_URL","").rstrip("/")
LOGS_TMPL = os.getenv("TRIAGE_LOGS_URL_TMPL","")

def _gf_explore_prom(q: str, range_min: str = "now-1h", range_max: str = "now"):
    if not GRAFANA: return None
    payload = {
      "datasource":"Prometheus",
      "queries":[{"expr":q, "refId":"A"}],
      "range":{"from":range_min, "to":range_max}
    }
    return f"{GRAFANA}/explore?left={urllib.parse.quote_plus(str(payload).replace("'","\""))}"

def _logs_link(q: str):
    if not LOGS_TMPL: return None
    return LOGS_TMPL.replace("{query}", urllib.parse.quote_plus(q))

async def _prom_query(cli: httpx.AsyncClient, expr: str):
    r = await cli.get(f"{PROM}/api/v1/query", params={"query": expr})
    r.raise_for_status()
    js = r.json()
    if js.get("status") != "success":
        raise RuntimeError(f"prom query failed: {expr}")
    return js.get("data", {}).get("result", [])

@router.get("/summary")
async def ops_summary():
    if not ENABLED:
        return JSONResponse({"ok": False, "error": "disabled"}, status_code=404)

    now = int(time.time())
    results = {}

    prom_exprs = {
        "rps":          'sum(rate(valhalla_http_requests_total[1m]))',
        "errors":       'sum(rate(valhalla_http_errors_total[5m]))',
        "p95":          'histogram_quantile(0.95, sum by (le)(rate(valhalla_http_request_duration_seconds_bucket[5m])))',
        "top5xx":       'topk(5, sum by (path)(rate(valhalla_http_errors_total[5m])))',
        "slow_p95":     'topk(5, histogram_quantile(0.95, sum by (le,path)(rate(valhalla_http_request_duration_seconds_bucket[5m]))))',
        "jobs_active":  'sum(valhalla_jobs_active)',
        "jobs_fail_rps":'topk(5, sum by (job_type)(rate(valhalla_jobs_runs_total{status="ERROR"}[15m])))',
        "burn_5m":      'sum(valhalla:burnrate:5m)',
        "burn_30m":     'sum(valhalla:burnrate:30m)',
        "burn_2h":      'sum(valhalla:burnrate:2h)',
        "burn_24h":     'sum(valhalla:burnrate:24h)',
    }

    alerts_url = f"{PROM}/api/v1/alerts"

    async with httpx.AsyncClient(timeout=10) as cli:
        tasks = {k: asyncio.create_task(_prom_query(cli, v)) for k, v in prom_exprs.items()}
        alerts_task = asyncio.create_task(cli.get(alerts_url))

        for k, t in tasks.items():
            try:
                results[k] = await t
            except Exception as e:
                results[k] = {"error": str(e)}

        alerts = []
        try:
            ar = await alerts_task
            ar.raise_for_status()
            aj = ar.json()
            if aj.get("status") == "success":
                alerts = aj.get("data", {}).get("alerts", [])
        except Exception as e:
            alerts = [{"labels":{"alertname":"FetchError"}, "state":"firing", "annotations":{"description":str(e)}}]

    def _val(x, default=0.0):
        try:
            if isinstance(x, list) and x:
                return float(x[0]["value"][1])
        except Exception:
            pass
        return default

    def _pairs(x, key_label):
        out=[]
        if isinstance(x,list):
            for it in x:
                labels = it.get("metric",{})
                value = float(it.get("value",[0,0])[1])
                out.append({"key": labels.get(key_label,""), "value": value})
        return out

    payload = {
        "ts": now * 1000,
        "overview": {
            "rps": _val(results.get("rps")),
            "errors_per_s": _val(results.get("errors")),
            "p95_s": _val(results.get("p95")),
            "jobs_active": _val(results.get("jobs_active"))
        },
        "top_5xx_paths": _pairs(results.get("top5xx"), "path"),
        "slow_p95_paths": _pairs(results.get("slow_p95"), "path"),
        "job_failures": _pairs(results.get("jobs_fail_rps"), "job_type"),
        "burn_rates": {
            "5m": _val(results.get("burn_5m")),
            "30m": _val(results.get("burn_30m")),
            "2h": _val(results.get("burn_2h")),
            "24h": _val(results.get("burn_24h")),
        },
        "alerts": [
            {
                "name": a.get("labels",{}).get("alertname",""),
                "severity": a.get("labels",{}).get("severity",""),
                "state": a.get("state",""),
                "desc": a.get("annotations",{}).get("summary") or a.get("annotations",{}).get("description",""),
                "labels": a.get("labels",{})
            } for a in alerts
        ],
        "links": {
            "grafana": GRAFANA or None,
            "tempo": TEMPO or None,
            "explore": {
                "rps": _gf_explore_prom(prom_exprs["rps"]),
                "errors": _gf_explore_prom(prom_exprs["errors"]),
                "p95": _gf_explore_prom(prom_exprs["p95"]),
                "top5xx": _gf_explore_prom(prom_exprs["top5xx"]),
                "slow": _gf_explore_prom(prom_exprs["slow_p95"]),
            },
            "logs": {
                "errors": _logs_link('level:ERROR OR status:"5xx"'),
                "path_5xx": _logs_link('status:"5xx" | stats count() by path'),
            }
        }
    }
    return JSONResponse(payload)
