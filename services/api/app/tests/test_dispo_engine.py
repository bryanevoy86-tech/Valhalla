"""
PACK Y: Dispo Engine Tests
"""

import pytest
from fastapi.testclient import TestClient


class TestDispoBuyer:
    """Test dispo buyer profile functionality."""

    def test_create_buyer(self, client: TestClient):
        """Create a new dispo buyer profile."""
        payload = {"name": "VIP Buyer", "email": "vip@example.com"}
        res = client.post("/dispo/buyers", json=payload)
        assert res.status_code == 200
        body = res.json()
        assert body["name"] == "VIP Buyer"
        assert body["email"] == "vip@example.com"
        assert body["is_active"] is True

    def test_list_buyers(self, client: TestClient):
        """List dispo buyers."""
        # Create some buyers
        client.post("/dispo/buyers", json={"name": "Buyer A"})
        client.post("/dispo/buyers", json={"name": "Buyer B"})

        res = client.get("/dispo/buyers")
        assert res.status_code == 200
        buyers = res.json()
        assert isinstance(buyers, list)
        assert len(buyers) >= 2

    def test_get_buyer(self, client: TestClient):
        """Get a specific dispo buyer."""
        res = client.post("/dispo/buyers", json={"name": "Buyer C"})
        buyer_id = res.json()["id"]

        res = client.get(f"/dispo/buyers/{buyer_id}")
        assert res.status_code == 200
        body = res.json()
        assert body["id"] == buyer_id
        assert body["name"] == "Buyer C"

    def test_update_buyer(self, client: TestClient):
        """Update a dispo buyer."""
        res = client.post("/dispo/buyers", json={"name": "Buyer D"})
        buyer_id = res.json()["id"]

        update = {"email": "buyer@example.com", "phone": "555-1234"}
        res = client.patch(f"/dispo/buyers/{buyer_id}", json=update)
        assert res.status_code == 200
        body = res.json()
        assert body["email"] == "buyer@example.com"
        assert body["phone"] == "555-1234"

    def test_deactivate_buyer(self, client: TestClient):
        """Deactivate a dispo buyer."""
        res = client.post("/dispo/buyers", json={"name": "Buyer E"})
        buyer_id = res.json()["id"]

        res = client.patch(f"/dispo/buyers/{buyer_id}", json={"is_active": False})
        assert res.status_code == 200
        assert res.json()["is_active"] is False

    def test_list_only_active_buyers(self, client: TestClient):
        """List only active buyers."""
        # Create and deactivate one
        res1 = client.post("/dispo/buyers", json={"name": "Active Buyer"})
        active_id = res1.json()["id"]

        res2 = client.post("/dispo/buyers", json={"name": "Inactive Buyer"})
        inactive_id = res2.json()["id"]
        client.patch(f"/dispo/buyers/{inactive_id}", json={"is_active": False})

        res = client.get("/dispo/buyers?active_only=true")
        assert res.status_code == 200
        buyers = res.json()
        names = [b["name"] for b in buyers]
        assert "Active Buyer" in names


class TestDispoAssignment:
    """Test dispo assignment functionality."""

    def test_create_assignment(self, client: TestClient):
        """Create a new dispo assignment."""
        # Create a buyer first
        buyer_res = client.post("/dispo/buyers", json={"name": "Buyer A"})
        buyer_id = buyer_res.json()["id"]

        payload = {"pipeline_id": 1, "buyer_id": buyer_id, "status": "offered"}
        res = client.post("/dispo/assignments", json=payload)
        assert res.status_code == 200
        body = res.json()
        assert body["buyer_id"] == buyer_id
        assert body["status"] == "offered"
        assert body["pipeline_id"] == 1

    def test_update_assignment_status(self, client: TestClient):
        """Update assignment status."""
        buyer_res = client.post("/dispo/buyers", json={"name": "Buyer B"})
        buyer_id = buyer_res.json()["id"]

        res = client.post(
            "/dispo/assignments",
            json={"pipeline_id": 2, "buyer_id": buyer_id},
        )
        assignment_id = res.json()["id"]

        # Update status
        res = client.patch(
            f"/dispo/assignments/{assignment_id}",
            json={"status": "assigned"},
        )
        assert res.status_code == 200
        assert res.json()["status"] == "assigned"

    def test_set_assignment_price_and_fee(self, client: TestClient):
        """Set assignment price and fee."""
        buyer_res = client.post("/dispo/buyers", json={"name": "Buyer C"})
        buyer_id = buyer_res.json()["id"]

        res = client.post(
            "/dispo/assignments",
            json={"pipeline_id": 3, "buyer_id": buyer_id},
        )
        assignment_id = res.json()["id"]

        # Update price and fee
        update = {"assignment_price": 150000, "assignment_fee": 10000}
        res = client.patch(f"/dispo/assignments/{assignment_id}", json=update)
        assert res.status_code == 200
        body = res.json()
        assert body["assignment_price"] == 150000
        assert body["assignment_fee"] == 10000

    def test_list_assignments_for_pipeline(self, client: TestClient):
        """List all assignments for a pipeline."""
        # Create buyers
        buyer1 = client.post("/dispo/buyers", json={"name": "Buyer 1"}).json()["id"]
        buyer2 = client.post("/dispo/buyers", json={"name": "Buyer 2"}).json()["id"]

        # Create assignments for same pipeline
        client.post("/dispo/assignments", json={"pipeline_id": 5, "buyer_id": buyer1})
        client.post("/dispo/assignments", json={"pipeline_id": 5, "buyer_id": buyer2})

        res = client.get("/dispo/assignments/by-pipeline/5")
        assert res.status_code == 200
        assignments = res.json()
        assert len(assignments) == 2

    def test_assignment_lifecycle(self, client: TestClient):
        """Test full assignment lifecycle: offered -> assigned -> closed."""
        buyer_res = client.post("/dispo/buyers", json={"name": "Buyer Lifecycle"})
        buyer_id = buyer_res.json()["id"]

        # Create (offered)
        res = client.post(
            "/dispo/assignments",
            json={"pipeline_id": 6, "buyer_id": buyer_id, "status": "offered"},
        )
        assignment_id = res.json()["id"]

        # Update to assigned
        client.patch(f"/dispo/assignments/{assignment_id}", json={"status": "assigned"})

        # Update to closed
        res = client.patch(f"/dispo/assignments/{assignment_id}", json={"status": "closed"})
        assert res.status_code == 200
        assert res.json()["status"] == "closed"

    def test_get_nonexistent_assignment(self, client: TestClient):
        """Get nonexistent assignment returns 404."""
        res = client.patch("/dispo/assignments/9999", json={"status": "closed"})
        assert res.status_code == 404
