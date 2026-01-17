import importlib
from fastapi.testclient import TestClient


def get_client():
    mod = importlib.import_module('main')
    return TestClient(mod.app)


def test_buyer_upsert_and_match():
    c = get_client()
    # upsert
    r = c.post('/api/buyer/upsert', json={"email":"b@example.com","name":"Buyer"})
    assert r.status_code == 200
    bid = r.json().get('buyer_id')
    assert bid
    # prefs
    prefs = {"regions":["MB-WPG"],"asset_types":["single_family"],"min_arv":0,"max_arv":999999}
    r = c.post(f'/api/buyer/{bid}/prefs', json=prefs)
    assert r.status_code == 200
    # match
    r = c.get('/api/buyer/match/123?min_score=60&limit=25')
    assert r.status_code == 200
    data = r.json()
    assert 'matches' in data and isinstance(data['matches'], list)


def test_buyer_claim_assign():
    c = get_client()
    r = c.post('/api/buyer/claim', params={"deal_id":123,"buyer_id":7001})
    assert r.status_code == 200
    assert r.json().get('status') in ("claimed","assigned")
    r = c.post('/api/buyer/assign', params={"deal_id":123,"buyer_id":7001})
    assert r.status_code == 200
