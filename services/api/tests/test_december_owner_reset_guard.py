"""No database or password reset may be reached by unauthorized requests."""
from unittest.mock import Mock

import pytest
from fastapi import HTTPException
from starlette.requests import Request

from app.routers.auth_weweb import admin_reset_password


@pytest.mark.parametrize(
    "enabled, configured, supplied, expected",
    [
        ("false", "configured-token", "configured-token", 403),
        ("true", None, None, 503),
        ("true", "", None, 503),
        ("true", "   ", None, 503),
        ("true", "configured-token", None, 401),
        ("true", "configured-token", "wrong-token", 401),
        ("true", "configured-token", "configured-token", 400),
    ],
)
def test_reset_requires_explicit_enable_and_setup_token(
    monkeypatch, enabled, configured, supplied, expected
):
    monkeypatch.setenv("RESET_OWNER_PASSWORD", enabled)
    monkeypatch.delenv("VALHALLA_OWNER_EMAIL", raising=False)
    monkeypatch.delenv("VALHALLA_OWNER_PASSWORD", raising=False)
    if configured is None:
        monkeypatch.delenv("VALHALLA_SETUP_TOKEN", raising=False)
    else:
        monkeypatch.setenv("VALHALLA_SETUP_TOKEN", configured)
    headers = [] if supplied is None else [(b"x-setup-token", supplied.encode())]
    request = Request({"type": "http", "headers": headers})
    db = Mock()
    with pytest.raises(HTTPException) as exc:
        admin_reset_password(request, db)
    assert exc.value.status_code == expected
    assert db.mock_calls == []
