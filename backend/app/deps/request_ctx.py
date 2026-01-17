import uuid

from fastapi import Request


def get_request_id(request: Request) -> str:
    rid = request.headers.get("X-Request-Id") or uuid.uuid4().hex
    request.state.request_id = rid
    return rid
