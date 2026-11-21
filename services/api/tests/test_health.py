import importlib

import pytest


def test_import_app():
    mod = importlib.import_module("main")
    assert hasattr(mod, "app")


@pytest.mark.integration
def test_health(loopback_api):
    response = loopback_api.get("/api/health")
    assert response.status_code == 200, response.text
    assert response.json()["ok"] is True
