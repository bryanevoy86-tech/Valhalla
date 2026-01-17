# services/api/tests/test_flow_tax_snapshot.py

from __future__ import annotations

from unittest.mock import patch
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_tax_snapshot_happy_path():
    """
    Test tax snapshot with a mocked profit_allocation response.
    """
    # Mock the profit_allocation endpoint response
    mock_profit_response = {
        "backend_deal_id": 123,
        "result": {
            "metrics": {
                "purchase_price": 240000,
                "repairs": 30000,
                "total_cost_basis": 270000,
                "sale_price": 340000,
                "sale_closing_costs": 10000,
                "extra_expenses": 5000,
                "gross_profit": 55000,
                "taxes": 13750,
                "net_profit_after_tax": 41250,
            },
            "flags": {
                "breach_min_tax_rate": False,
                "notes": None,
            },
            "policy": {
                "min_tax_rate": 0.20,
            },
        },
        "freeze_event_created": False,
    }

    with patch("app.routers.flow_tax_snapshot._client.post") as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = mock_profit_response

        payload = {
            "backend_deal_id": 123,
            "sale_price": 340000,
            "sale_closing_costs": 10000,
            "extra_expenses": 5000,
            "tax_rate": 0.25,
        }

        resp = client.post("/api/flow/tax_snapshot_for_deal", json=payload)
        assert resp.status_code == 200, resp.text

        data = resp.json()
        assert data["backend_deal_id"] == 123

        numbers = data["numbers"]
        policy = data["policy"]

        assert numbers["sale_price"] == 340000
        assert numbers["gross_profit"] == 55000
        assert numbers["tax_amount"] == 13750
        assert numbers["net_after_tax"] == 41250

        # In happy path we should not be breaching min tax rate policy
        assert policy["breach_min_tax_rate"] is False


def test_tax_snapshot_below_min_tax_rate_flags_policy():
    """
    Test tax snapshot with low tax rate triggering policy flag.
    """
    # Mock the profit_allocation endpoint response with breach flag
    mock_profit_response = {
        "backend_deal_id": 456,
        "result": {
            "metrics": {
                "purchase_price": 240000,
                "repairs": 30000,
                "total_cost_basis": 270000,
                "sale_price": 340000,
                "sale_closing_costs": 5000,
                "extra_expenses": 2000,
                "gross_profit": 63000,
                "taxes": 3150,  # 5% tax rate
                "net_profit_after_tax": 59850,
            },
            "flags": {
                "breach_min_tax_rate": True,
                "notes": "Tax rate 0.05 is below minimum policy rate of 0.20",
            },
            "policy": {
                "min_tax_rate": 0.20,
            },
        },
        "freeze_event_created": True,
    }

    with patch("app.routers.flow_tax_snapshot._client.post") as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = mock_profit_response

        payload = {
            "backend_deal_id": 456,
            "sale_price": 340000,
            "sale_closing_costs": 5000,
            "extra_expenses": 2000,
            "tax_rate": 0.05,  # well below default 20% min
        }

        resp = client.post("/api/flow/tax_snapshot_for_deal", json=payload)
        assert resp.status_code == 200, resp.text

        data = resp.json()
        policy = data["policy"]

        # Should flag breach
        assert policy["breach_min_tax_rate"] is True
