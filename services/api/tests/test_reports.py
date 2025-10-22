from fastapi.testclient import TestClient
from app.routers.reports import router
from fastapi import FastAPI

app = FastAPI()
app.include_router(router)
client = TestClient(app)


def test_reports_summary():
    """Test the /reports/summary endpoint"""
    response = client.get("/reports/summary")
    assert response.status_code == 200
    data = response.json()
    assert data.get("ok") is True
    assert "summary" in data
    assert "total_reports" in data["summary"]
    assert "pending" in data["summary"]
    assert "completed" in data["summary"]
