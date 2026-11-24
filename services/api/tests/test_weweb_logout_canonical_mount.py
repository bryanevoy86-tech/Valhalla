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



def test_weweb_preflight_uses_exact_origins_and_exposes_only_required_grant():
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.testclient import TestClient

    from app.core.settings import _parse_origins, settings

    canonical = importlib.import_module("app.main").app
    policy = next(middleware for middleware in canonical.user_middleware if middleware.cls is CORSMiddleware)
    assert policy.kwargs["allow_origins"] == settings.cors_allowed_origins
    assert _parse_origins("*") == _parse_origins(None) == []
    assert _parse_origins('["https://preview.example.invalid", "*", 123]') == ["https://preview.example.invalid"]
    assert _parse_origins(
        "https://example.invalid/path,http://preview.example.invalid,https://user@host,https://host?,http://localhost:4000"
    ) == ["http://localhost:4000"]

    api = FastAPI()
    origin = "https://preview.example.invalid"
    api.add_middleware(policy.cls, **{**policy.kwargs, "allow_origins": [origin]})

    @api.get("/fixture")
    def fixture():
        return {"ok": True}

    with TestClient(api) as client:
        preflight = {"Access-Control-Request-Method": "POST",
                     "Access-Control-Request-Headers": "authorization,content-type"}
        allowed = client.options("/fixture", headers={**preflight, "Origin": origin})
        assert allowed.status_code == 200 and allowed.headers["Access-Control-Allow-Origin"] == origin
        assert "Access-Control-Allow-Credentials" not in allowed.headers
        denied = client.options("/fixture", headers={**preflight, "Origin": "https://other.example.invalid"})
        assert denied.status_code == 400 and "Access-Control-Allow-Origin" not in denied.headers
        response = client.get("/fixture", headers={"Origin": origin})
        assert response.headers["Access-Control-Expose-Headers"] == "X-Delivery-Grant, Content-Disposition"
