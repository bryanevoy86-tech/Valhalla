from __future__ import annotations

import importlib
import logging
from dataclasses import dataclass
from fastapi import FastAPI

log = logging.getLogger("valhalla.routers")


@dataclass(frozen=True)
class RouterSpec:
    name: str
    module: str
    attr: str = "router"
    prefix: str = ""
    required: bool = False


def include_router_safe(app: FastAPI, spec: RouterSpec) -> None:
    try:
        m = importlib.import_module(spec.module)
        router = getattr(m, spec.attr)
        if spec.prefix:
            app.include_router(router, prefix=spec.prefix)
        else:
            app.include_router(router)
        log.info("ROUTER_OK: %s (%s:%s) prefix=%s", spec.name, spec.module, spec.attr, spec.prefix)
    except Exception as e:
        msg = f"ROUTER_FAIL: {spec.name} ({spec.module}:{spec.attr}) -> {type(e).__name__}: {e}"
        if spec.required:
            log.error(msg)
            raise
        log.warning(msg)
