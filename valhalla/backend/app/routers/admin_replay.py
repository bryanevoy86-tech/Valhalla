import ipaddress
import json
import os
import urllib.parse

import httpx
from fastapi import APIRouter, Header, HTTPException, Query
from fastapi.responses import JSONResponse, PlainTextResponse

from ..observability.logging import get_logger
from ..observability.replay import ALLOW_HOSTS, DEFAULT_DEST, JSON_PATH, TIMEOUT

router = APIRouter(prefix="/admin/replay", tags=["admin-replay"])
log = get_logger("admin.replay")


def _require_token(token_header: str | None):
    needed = os.getenv("REPLAY_ADMIN_TOKEN", "")
    if not needed:
        return
    if not token_header or token_header != needed:
        raise HTTPException(status_code=401, detail="missing/invalid token")


def _load_lines():
    if not os.path.exists(JSON_PATH):
        return []
    with open(JSON_PATH, encoding="utf-8", errors="ignore") as f:
        return [json.loads(line) for line in f if line.strip()]


@router.get("/list")
def list_items(
    x_admin_token: str | None = Header(default=None), limit: int = Query(200, ge=1, le=2000)
):
    _require_token(x_admin_token)
    items = _load_lines()
    items = items[-limit:]
    return {"count": len(items), "items": items}


@router.get("/get")
def get_item(x_admin_token: str | None = Header(default=None), id: str = Query(...)):
    _require_token(x_admin_token)
    for it in _load_lines():
        if it.get("id") == id:
            return JSONResponse(it)
    return PlainTextResponse("Not found", status_code=404)


def _host_allowed(url: str) -> bool:
    try:
        u = urllib.parse.urlparse(url)
        host = (u.hostname or "").lower()
        if not host:
            return False
        if host in ALLOW_HOSTS:
            return True
        # allow loopback
        try:
            ip = ipaddress.ip_address(host)
            if ip.is_loopback or ip.is_private:
                return True
        except Exception:
            pass
        return False
    except Exception:
        return False


@router.post("/replay")
def replay_one(
    x_admin_token: str | None = Header(default=None),
    id: str = Query(..., description="captured item id"),
    dest: str | None = Query(
        None, description="override destination base URL, e.g. http://backend:8000"
    ),
):
    _require_token(x_admin_token)
    items = _load_lines()
    target = next((x for x in items if x.get("id") == id), None)
    if not target:
        raise HTTPException(status_code=404, detail="not found")

    base = (dest or target.get("default_dest") or DEFAULT_DEST).rstrip("/")
    if not _host_allowed(base):
        raise HTTPException(status_code=400, detail="destination host not allowed")

    url = f"{base}{target.get('path','')}"
    if target.get("query"):
        url += f"?{target['query']}"

    # rebuild headers, skip hop-by-hop, ensure content-type present
    hdrs = {k: v for k, v in (target.get("headers") or {}).items()}
    for k in list(hdrs.keys()):
        if k.lower() in ("content-length", "host", "connection", "transfer-encoding"):
            hdrs.pop(k, None)
    if "content-type" not in {k.lower() for k in hdrs}:
        hdrs["content-type"] = "application/json"

    method = (target.get("method") or "POST").upper()
    data = target.get("body_b64", "").encode("utf-8")

    timeout = float(target.get("timeout_secs") or TIMEOUT)
    try:
        with httpx.Client(timeout=timeout) as cli:
            resp = cli.request(method, url, content=data, headers=hdrs)
            log.info("replay.sent", id=id, dest=base, code=resp.status_code, bytes=len(data))
            return {
                "id": id,
                "dest": base,
                "status_code": resp.status_code,
                "headers": dict(resp.headers),
                "body": resp.text[:8192],
            }
    except Exception as e:
        log.error("replay.error", id=id, dest=base, err=str(e))
        raise HTTPException(status_code=502, detail=str(e))


@router.post("/replay/batch")
def replay_batch(
    x_admin_token: str | None = Header(default=None),
    status: int = Query(500, description="replay items with this captured status"),
    limit: int = Query(50, ge=1, le=500),
    dest: str | None = Query(None),
):
    _require_token(x_admin_token)
    items = [x for x in _load_lines() if x.get("status") == int(status)][-limit:]
    results = []
    for it in items:
        try:
            r = replay_one(x_admin_token, it["id"], dest)  # reuse handler
            results.append({"id": it["id"], "ok": True, "status": r["status_code"]})
        except Exception as e:
            results.append({"id": it.get("id"), "ok": False, "error": str(e)})
    return {"count": len(results), "results": results}


@router.delete("/purge")
def purge(x_admin_token: str | None = Header(default=None)):
    _require_token(x_admin_token)
    if os.path.exists(JSON_PATH):
        os.remove(JSON_PATH)
    return {"ok": True}
