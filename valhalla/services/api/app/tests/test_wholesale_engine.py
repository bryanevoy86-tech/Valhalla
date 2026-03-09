"""
PACK X: Wholesaling Engine Tests
"""

import pytest
from fastapi.testclient import TestClient


class TestWholesalePipeline:
    """Test wholesale pipeline functionality."""

    def test_create_wholesale_pipeline(self, client: TestClient):
        """Create a new wholesale pipeline."""
        payload = {
            "deal_id": 1,
            "property_id": 10,
            "stage": "lead",
            "lead_source": "PPC",
            "seller_motivation": "Tired landlord",
        }
        res = client.post("/wholesale/", json=payload)
        assert res.status_code == 200
        body = res.json()
        assert body["stage"] == "lead"
        assert body["deal_id"] == 1
        assert body["property_id"] == 10

    def test_list_wholesale_pipelines(self, client: TestClient):
        """List wholesale pipelines."""
        # Create a pipeline first
        payload = {"deal_id": 1, "property_id": 10}
        client.post("/wholesale/", json=payload)

        # List all
        res = client.get("/wholesale/")
        assert res.status_code == 200
        pipelines = res.json()
        assert isinstance(pipelines, list)
        assert len(pipelines) > 0

    def test_get_wholesale_pipeline(self, client: TestClient):
        """Get a specific wholesale pipeline."""
        # Create a pipeline
        payload = {"deal_id": 2, "property_id": 20}
        res = client.post("/wholesale/", json=payload)
        pid = res.json()["id"]

        # Get it
        res = client.get(f"/wholesale/{pid}")
        assert res.status_code == 200
        body = res.json()
        assert body["id"] == pid
        assert body["deal_id"] == 2

    def test_update_wholesale_stage(self, client: TestClient):
        """Update wholesale pipeline stage."""
        # Create first
        payload = {"deal_id": 1, "property_id": 10}
        res = client.post("/wholesale/", json=payload)
        pid = res.json()["id"]

        # Update stage
        res = client.patch(f"/wholesale/{pid}", json={"stage": "under_contract"})
        assert res.status_code == 200
        assert res.json()["stage"] == "under_contract"

    def test_filter_by_stage(self, client: TestClient):
        """Filter pipelines by stage."""
        # Create pipelines with different stages
        client.post("/wholesale/", json={"stage": "lead"})
        client.post("/wholesale/", json={"stage": "under_contract"})

        # Filter by stage
        res = client.get("/wholesale/?stage=lead")
        assert res.status_code == 200
        pipelines = res.json()
        assert all(p["stage"] == "lead" for p in pipelines)

    def test_add_wholesale_activity(self, client: TestClient):
        """Log an activity on a wholesale pipeline."""
        # Create pipeline
        payload = {"deal_id": 2, "property_id": 20}
        res = client.post("/wholesale/", json=payload)
        pid = res.json()["id"]

        # Add activity
        act_payload = {"event_type": "call", "description": "Spoke with seller"}
        res = client.post(f"/wholesale/{pid}/activities", json=act_payload)
        assert res.status_code == 200
        body = res.json()
        assert body["event_type"] == "call"
        assert body["description"] == "Spoke with seller"

    def test_pipeline_includes_activities(self, client: TestClient):
        """Pipeline retrieval includes activities."""
        # Create pipeline
        res = client.post("/wholesale/", json={"deal_id": 3, "property_id": 30})
        pid = res.json()["id"]

        # Add activities
        client.post(f"/wholesale/{pid}/activities", json={"event_type": "call"})
        client.post(f"/wholesale/{pid}/activities", json={"event_type": "email"})

        # Get pipeline and check activities
        res = client.get(f"/wholesale/{pid}")
        body = res.json()
        assert len(body["activities"]) == 2
        assert body["activities"][0]["event_type"] in ["call", "email"]

    def test_update_metrics(self, client: TestClient):
        """Update pipeline metrics (ARV, MAO, spread, etc.)."""
        res = client.post("/wholesale/", json={"deal_id": 1, "property_id": 10})
        pid = res.json()["id"]

        # Update metrics
        update = {
            "arv_estimate": 250000,
            "max_allowable_offer": 150000,
            "assignment_fee_target": 10000,
            "expected_spread": 20000,
        }
        res = client.patch(f"/wholesale/{pid}", json=update)
        assert res.status_code == 200
        body = res.json()
        assert body["arv_estimate"] == 250000
        assert body["expected_spread"] == 20000

    def test_get_nonexistent_pipeline(self, client: TestClient):
        """Get nonexistent pipeline returns 404."""
        res = client.get("/wholesale/9999")
        assert res.status_code == 404
