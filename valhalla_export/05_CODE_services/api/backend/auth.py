from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Callable, Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

CONFIG_PATH = Path("heimdall/agent.config.json")


def _load_cfg() -> dict:
    if CONFIG_PATH.exists():
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    return {}


def _extract_token(req: Request, cfg: dict) -> Optional[str]:
    header_name = (cfg.get("admin_auth", {}) or {}).get("header", "x-heimdall-token")
    qp = (cfg.get("admin_auth", {}) or {}).get("query_param", "token")
    tok = req.headers.get(header_name)
    if not tok:
        tok = req.query_params.get(qp)
    if not tok and (cfg.get("admin_auth", {}) or {}).get("accept_bearer", True):
        auth = req.headers.get("authorization", "")
        if auth.lower().startswith("bearer "):
            tok = auth[7:].strip()
    return tok


def _role_for_token(tok: Optional[str], cfg: dict, client_host: str) -> Optional[str]:
    aa = cfg.get("admin_auth", {}) or {}
    admin_env = aa.get("admin_token_env", "HEIMDALL_ADMIN_TOKEN")
    viewer_env = aa.get("viewer_token_env", "HEIMDALL_VIEWER_TOKEN")
    admin_tok = os.getenv(admin_env, "") or ""
    viewer_tok = os.getenv(viewer_env, "") or ""
    # allow local without token (defaults to True)
    if aa.get("allow_local_without_token", True) and (
        client_host in {"127.0.0.1", "::1", "localhost"}
    ):
        if not tok:
            return "admin"
    if tok and admin_tok and tok == admin_tok:
        return "admin"
    if tok and viewer_tok and tok == viewer_tok:
        return "viewer"
    return None


class HeimdallAuthMiddleware(BaseHTTPMiddleware):
    """Protects /admin/* endpoints with admin/viewer roles and enforces read_only mode."""

    def __init__(self, app, publish_now_allow_fn: Optional[Callable[[str], bool]] = None):
        super().__init__(app)
        self.publish_now_allow_fn = publish_now_allow_fn

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if not path.startswith("/admin"):
            return await call_next(request)

        cfg = _load_cfg()
        role = _role_for_token(
            _extract_token(request, cfg), cfg, request.client.host if request.client else ""
        )
        if not role:
            return JSONResponse({"error": "unauthorized"}, status_code=401)

        # Stash role/read_only on request.state for templates
        aa = cfg.get("admin_auth", {}) or {}
        read_only = bool(aa.get("read_only", False))
        request.state.role = role
        request.state.read_only = read_only

        # Viewer is GET-only
        if role == "viewer" and request.method != "GET":
            return JSONResponse({"error": "forbidden (viewer: read-only)"}, status_code=403)

        # Global read-only: block non-GET even for admin, EXCEPT the queue-enqueue path we explicitly allow
        if read_only and request.method != "GET":
            allow_path = str(aa.get("read_only_publish_now_path", "/admin/heimdall/publish-now"))
            ok = path == allow_path
            if self.publish_now_allow_fn is not None:
                try:
                    ok = ok or self.publish_now_allow_fn(path)  # optional extra allow predicate
                except Exception:
                    pass
            if not ok:
                return JSONResponse(
                    {"error": "read-only mode: writes are disabled"}, status_code=423
                )

        return await call_next(request)
