import importlib

def test_canonical_app_openapi_exposes_weweb_logout_and_refresh(monkeypatch):
    # Required by auth settings during router autoload.
    monkeypatch.setenv("VALHALLA_OWNER_EMAIL", "owner@example.com")
    monkeypatch.setenv("VALHALLA_OWNER_USERNAME", "owner")
    monkeypatch.setenv("VALHALLA_OWNER_PASSWORD", "OwnerPass!1")
    monkeypatch.setenv("VALHALLA_JWT_SECRET", "test-secret")

    app_main = importlib.import_module("app.main")
    app = app_main.app

    paths = app.openapi().get("paths", {})

    assert "/api/weweb/logout" in paths
    assert "post" in paths["/api/weweb/logout"]

    assert "/api/weweb/refresh" in paths
    assert "post" in paths["/api/weweb/refresh"]
