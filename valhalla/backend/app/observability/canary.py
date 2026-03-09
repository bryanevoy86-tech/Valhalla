import json
import os
import random
import re
import threading
import time
from typing import Any, Dict

import httpx

ENABLED = os.getenv("CANARY_ENABLED", "false").lower() in ("1", "true", "yes")
UPSTREAM = os.getenv("CANARY_UPSTREAM", "http://localhost:9000").rstrip("/")
PERCENT = int(os.getenv("CANARY_PERCENT", "0"))
PATHS_RE = re.compile(os.getenv("CANARY_PATHS_REGEX", r"^/"), re.IGNORECASE)
REQUIRE_HEADER = os.getenv("CANARY_REQUIRE_HEADER", "true").lower() in ("1", "true", "yes")
STICKY_COOKIE = os.getenv("CANARY_STICKY_COOKIE", "va_canary")
TIMEOUT = float(os.getenv("CANARY_TIMEOUT_SECS", "15"))

FAIL_BUDGET = int(os.getenv("CANARY_FAIL_BUDGET", "10"))
FAIL_WINDOW = int(os.getenv("CANARY_FAIL_WINDOW_SEC", "120"))
STATE_PATH = os.getenv("CANARY_STATE_PATH", "")

GUARD_ENABLED = os.getenv("CANARY_GUARD_ENABLED", "true").lower() in ("1", "true", "yes")
GUARD_DROP_STEP = int(os.getenv("CANARY_GUARD_DROP_STEP", "50"))
GUARD_MIN_PERCENT = int(os.getenv("CANARY_GUARD_MIN_PERCENT", "0"))
GUARD_DISABLE_ON_SEVERE = os.getenv("CANARY_GUARD_DISABLE_ON_SEVERE", "true").lower() in (
    "1",
    "true",
    "yes",
)
WEBHOOK_TOKEN = os.getenv("CANARY_WEBHOOK_TOKEN", "")

_lock = threading.Lock()
_state = {
    "enabled": ENABLED,
    "upstream": UPSTREAM,
    "percent": max(0, min(100, PERCENT)),
    "fail_events": [],
}


def _save():
    if not STATE_PATH:
        return
    try:
        os.makedirs(os.path.dirname(STATE_PATH), exist_ok=True)
        with open(STATE_PATH, "w", encoding="utf-8") as f:
            json.dump(_state, f)
    except Exception:
        pass


def _load():
    if not STATE_PATH or not os.path.exists(STATE_PATH):
        return
    try:
        with open(STATE_PATH, encoding="utf-8") as f:
            data = json.load(f)
        with _lock:
            _state.update(
                {
                    "enabled": bool(data.get("enabled", _state["enabled"])),
                    "upstream": str(data.get("upstream", _state["upstream"])),
                    "percent": int(data.get("percent", _state["percent"])),
                }
            )
    except Exception:
        pass


_load()


def status() -> Dict[str, Any]:
    with _lock:
        now = time.time()
        _state["fail_events"] = [t for t in _state["fail_events"] if now - t <= FAIL_WINDOW]
        return dict(_state, paths_regex=PATHS_RE.pattern)


def set_enabled(flag: bool):
    with _lock:
        _state["enabled"] = bool(flag)
        _save()


def set_percent(p: int):
    with _lock:
        _state["percent"] = max(0, min(100, int(p)))
        _save()


def set_upstream(url: str):
    with _lock:
        _state["upstream"] = url.rstrip("/")
        _save()


def _eligible(path: str, headers: Dict[str, str], cookies: Dict[str, str]) -> bool:
    if not PATHS_RE.search(path):
        return False
    if REQUIRE_HEADER and headers.get("x-canary", "").lower() not in ("1", "true", "yes"):
        return False
    if STICKY_COOKIE and cookies.get(STICKY_COOKIE) == "1":
        return True
    return True


def decide(path: str, headers: Dict[str, str], cookies: Dict[str, str]) -> bool:
    with _lock:
        if not _state["enabled"] or _state["percent"] <= 0:
            return False
        if not _eligible(path, headers, cookies):
            return False
        if STICKY_COOKIE and cookies.get(STICKY_COOKIE) == "1":
            return True
        return random.randint(1, 100) <= _state["percent"]


def record_failure():
    with _lock:
        now = time.time()
        _state["fail_events"].append(now)
        _state["fail_events"] = [t for t in _state["fail_events"] if now - t <= FAIL_WINDOW]
        if len(_state["fail_events"]) >= FAIL_BUDGET:
            _state["enabled"] = False
            _state["percent"] = 0
        _save()


def clear_failures():
    with _lock:
        _state["fail_events"].clear()
        _save()


async def proxy_request(
    method: str, url: str, body: bytes, headers: Dict[str, str]
) -> httpx.Response:
    h = {
        k: v
        for k, v in headers.items()
        if k.lower() not in ("host", "content-length", "connection", "transfer-encoding")
    }
    async with httpx.AsyncClient(timeout=TIMEOUT) as cli:
        return await cli.request(method, url, content=body, headers=h)


def guard_drop(severe: bool = False) -> Dict[str, Any]:
    with _lock:
        if severe and GUARD_DISABLE_ON_SEVERE:
            _state["enabled"] = False
            _state["percent"] = 0
        else:
            newp = max(GUARD_MIN_PERCENT, _state["percent"] - GUARD_DROP_STEP)
            _state["percent"] = newp
            if newp == 0:
                _state["enabled"] = False
        _save()
        return dict(_state)
