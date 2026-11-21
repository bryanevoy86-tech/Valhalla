import json


def test_intake_normalize_to_deal(legacy_http_client):
    client, _ = legacy_http_client
    # Create raw lead
    lead = {
      "source":"webform","name":"Jane Seller","email":"jane@example.com",
      "phone":"204-555-0101","address":"123 Maple St","region":"Winnipeg",
      "property_type":"single family","price":275000,"beds":3,"baths":1,
      "notes":"needs TLC","raw":{"br":3,"ba":1}
    }
    r = client.post("/api/intake/leads", data=json.dumps(lead))
    assert r.status_code == 200
    lid = r.json()["id"]

    # Normalize -> creates DealBrief
    r = client.post(f"/api/intake/leads/{lid}/normalize")
    assert r.status_code == 200
    j = r.json()
    assert j["ok"] is True and j["deal_id"] is not None


def test_notify_queue_only(legacy_http_client):
    client, _ = legacy_http_client
    # Queue webhook (won't send here) - provide explicit URL
    r = client.post("/api/notify/webhook", data=json.dumps({"url":"https://example.com/webhook","payload":{"ping":"ok"}}))
    assert r.status_code == 200
    # Queue email (won't send without SMTP env)
    r = client.post("/api/notify/email", data=json.dumps({
        "to":"bryan@example.com","subject":"Test","body_text":"Hello"
    }))
    assert r.status_code == 200
