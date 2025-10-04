from fastapi.testclient import TestClient

from ..main import app

client = TestClient(app)

LEAD_CSV = "id,name,email,phone,created_at,updated_at,owner_id\n1,Test,test@example.com,123,2023-01-01,2023-01-01,1\n"
BUYER_CSV = "id,name,email,phone,created_at,updated_at,legacy_id,markets,zips,price_min,price_max,beds_min,baths_min\n1,Buyer,buyer@example.com,456,2023-01-01,2023-01-01,LEG,NYC,10001,100000,500000,2,1\n"


def test_lead_csv_roundtrip():
    # Import
    resp = client.post("/leads/import", files={"file": ("leads.csv", LEAD_CSV)})
    assert resp.status_code == 200
    # Export
    resp = client.get("/leads/export")
    assert resp.status_code == 200
    assert "test@example.com" in resp.text


def test_buyer_csv_roundtrip():
    # Import
    resp = client.post("/buyers/import", files={"file": ("buyers.csv", BUYER_CSV)})
    assert resp.status_code == 200
    # Export
    resp = client.get("/buyers/export")
    assert resp.status_code == 200
    assert "buyer@example.com" in resp.text
