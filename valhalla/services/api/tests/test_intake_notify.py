import os, httpx, json
API = os.getenv("API_BASE", "http://localhost:8000/api")
KEY = os.getenv("HEIMDALL_BUILDER_API_KEY", "test123")
H = {"X-API-Key": KEY, "Content-Type": "application/json"}


def test_intake_normalize_to_deal():
    # Create raw lead
    lead = {
      "source":"webform","name":"Jane Seller","email":"jane@example.com",
      "phone":"204-555-0101","address":"123 Maple St","region":"Winnipeg",
      "property_type":"single family","price":275000,"beds":3,"baths":1,
      "notes":"needs TLC","raw":{"br":3,"ba":1}
    }
    r = httpx.post(f"{API}/intake/leads", headers=H, data=json.dumps(lead), timeout=10)
    assert r.status_code == 200
    lid = r.json()["id"]

    # Normalize -> creates DealBrief
    r = httpx.post(f"{API}/intake/leads/{lid}/normalize", headers=H, timeout=10)
    assert r.status_code == 200
    j = r.json()
    assert j["ok"] is True and j["deal_id"] is not None


def test_notify_queue_only():
    # Queue webhook (won't send here) - provide explicit URL
    r = httpx.post(f"{API}/notify/webhook", headers=H, data=json.dumps({"url":"https://example.com/webhook","payload":{"ping":"ok"}}), timeout=10)
    assert r.status_code == 200
    # Queue email (won't send without SMTP env)
    r = httpx.post(f"{API}/notify/email", headers=H, data=json.dumps({
        "to":"bryan@example.com","subject":"Test","body_text":"Hello"
    }), timeout=10)
    assert r.status_code == 200
