"""
PACK Z: Global Holdings Engine Tests
"""

import pytest
from fastapi.testclient import TestClient


class TestHolding:
    """Test holdings functionality."""

    def test_create_holding(self, client: TestClient):
        """Create a new holding."""
        payload = {
            "asset_type": "property",
            "internal_ref": "property:123",
            "jurisdiction": "Canada",
            "entity_name": "Valhalla Holdings Inc.",
            "label": "Duplex #1",
            "value_estimate": 350000,
            "currency": "CAD",
        }
        res = client.post("/holdings/", json=payload)
        assert res.status_code == 200
        body = res.json()
        assert body["asset_type"] == "property"
        assert body["value_estimate"] == 350000
        assert body["jurisdiction"] == "Canada"

    def test_list_holdings(self, client: TestClient):
        """List all holdings."""
        # Create some holdings
        client.post(
            "/holdings/",
            json={
                "asset_type": "property",
                "jurisdiction": "USA",
                "value_estimate": 100000,
            },
        )
        client.post(
            "/holdings/",
            json={
                "asset_type": "resort",
                "jurisdiction": "Mexico",
                "value_estimate": 500000,
            },
        )

        res = client.get("/holdings/")
        assert res.status_code == 200
        holdings = res.json()
        assert isinstance(holdings, list)
        assert len(holdings) >= 2

    def test_get_holding(self, client: TestClient):
        """Get a specific holding."""
        res = client.post(
            "/holdings/",
            json={
                "asset_type": "property",
                "label": "Beach House",
                "value_estimate": 750000,
            },
        )
        holding_id = res.json()["id"]

        res = client.get(f"/holdings/{holding_id}")
        assert res.status_code == 200
        body = res.json()
        assert body["id"] == holding_id
        assert body["label"] == "Beach House"

    def test_update_holding(self, client: TestClient):
        """Update a holding."""
        res = client.post(
            "/holdings/",
            json={"asset_type": "property", "value_estimate": 100000},
        )
        holding_id = res.json()["id"]

        update = {
            "value_estimate": 125000,
            "label": "Updated Label",
            "notes": "Value increased",
        }
        res = client.patch(f"/holdings/{holding_id}", json=update)
        assert res.status_code == 200
        body = res.json()
        assert body["value_estimate"] == 125000
        assert body["label"] == "Updated Label"

    def test_filter_by_asset_type(self, client: TestClient):
        """Filter holdings by asset type."""
        # Create mixed holdings
        client.post("/holdings/", json={"asset_type": "property", "value_estimate": 100000})
        client.post("/holdings/", json={"asset_type": "resort", "value_estimate": 500000})
        client.post("/holdings/", json={"asset_type": "property", "value_estimate": 200000})

        res = client.get("/holdings/?asset_type=property")
        assert res.status_code == 200
        holdings = res.json()
        assert all(h["asset_type"] == "property" for h in holdings)

    def test_filter_by_jurisdiction(self, client: TestClient):
        """Filter holdings by jurisdiction."""
        # Create holdings in different jurisdictions
        client.post("/holdings/", json={"asset_type": "property", "jurisdiction": "USA"})
        client.post("/holdings/", json={"asset_type": "property", "jurisdiction": "Canada"})
        client.post("/holdings/", json={"asset_type": "resort", "jurisdiction": "USA"})

        res = client.get("/holdings/?jurisdiction=Canada")
        assert res.status_code == 200
        holdings = res.json()
        assert all(h["jurisdiction"] == "Canada" for h in holdings)

    def test_filter_active_only(self, client: TestClient):
        """Filter to show only active holdings."""
        # Create and deactivate one
        res1 = client.post("/holdings/", json={"asset_type": "property"})
        active_id = res1.json()["id"]

        res2 = client.post("/holdings/", json={"asset_type": "property"})
        inactive_id = res2.json()["id"]
        client.patch(f"/holdings/{inactive_id}", json={"is_active": False})

        res = client.get("/holdings/?only_active=true")
        assert res.status_code == 200
        holdings = res.json()
        assert all(h["is_active"] is True for h in holdings)

    def test_holdings_summary(self, client: TestClient):
        """Get holdings summary."""
        # Clear and create consistent holdings
        client.post(
            "/holdings/",
            json={
                "asset_type": "property",
                "jurisdiction": "USA",
                "value_estimate": 100000,
            },
        )
        client.post(
            "/holdings/",
            json={
                "asset_type": "property",
                "jurisdiction": "USA",
                "value_estimate": 150000,
            },
        )
        client.post(
            "/holdings/",
            json={
                "asset_type": "resort",
                "jurisdiction": "Mexico",
                "value_estimate": 500000,
            },
        )

        res = client.get("/holdings/summary")
        assert res.status_code == 200
        body = res.json()
        assert "total_value" in body
        assert "by_asset_type" in body
        assert "by_jurisdiction" in body
        assert body["total_value"] > 0

    def test_summary_by_asset_type(self, client: TestClient):
        """Summary should include breakdown by asset type."""
        client.post("/holdings/", json={"asset_type": "property", "value_estimate": 200000})
        client.post("/holdings/", json={"asset_type": "resort", "value_estimate": 800000})

        res = client.get("/holdings/summary")
        body = res.json()
        assert "property" in body["by_asset_type"]
        assert "resort" in body["by_asset_type"]

    def test_summary_by_jurisdiction(self, client: TestClient):
        """Summary should include breakdown by jurisdiction."""
        client.post(
            "/holdings/",
            json={
                "asset_type": "property",
                "jurisdiction": "USA",
                "value_estimate": 300000,
            },
        )
        client.post(
            "/holdings/",
            json={
                "asset_type": "resort",
                "jurisdiction": "Canada",
                "value_estimate": 700000,
            },
        )

        res = client.get("/holdings/summary")
        body = res.json()
        assert "USA" in body["by_jurisdiction"]
        assert "Canada" in body["by_jurisdiction"]

    def test_get_nonexistent_holding(self, client: TestClient):
        """Get nonexistent holding returns 404."""
        res = client.get("/holdings/9999")
        assert res.status_code == 404
