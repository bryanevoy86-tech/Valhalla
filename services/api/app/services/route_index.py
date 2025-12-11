"""
PACK TY: Route Index & Debug Explorer Service
"""

from typing import List
from fastapi import FastAPI
from fastapi.routing import APIRoute

from app.schemas.route_index import RouteInfo, RouteIndex


def build_route_index(app: FastAPI) -> RouteIndex:
    items: List[RouteInfo] = []

    for route in app.routes:
        if not isinstance(route, APIRoute):
            continue

        methods = sorted(list(route.methods or []))
        tags = list(route.tags or [])
        summary = route.summary
        deprecated = bool(route.deprecated)

        # Skip OPTIONS, HEAD noise unless you want them
        if methods == ["OPTIONS"] or methods == ["HEAD"]:
            continue

        items.append(
            RouteInfo(
                path=route.path,
                methods=methods,
                name=route.name,
                tags=tags,
                summary=summary,
                deprecated=deprecated,
            )
        )

    return RouteIndex(total=len(items), routes=items)
