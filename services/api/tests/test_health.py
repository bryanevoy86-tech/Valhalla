import importlib
import pytest
import httpx
import asyncio

# Minimal import test; avoids spinning server
def test_import_app():
    mod = importlib.import_module('main')
    assert hasattr(mod, 'app')

@pytest.mark.asyncio
@pytest.mark.integration
async def test_health():
    async with httpx.AsyncClient(base_url="http://127.0.0.1:4000") as c:
        r = await c.get("/api/health")
        assert r.status_code == 200
        data = r.json()
        assert data.get("ok") is True
