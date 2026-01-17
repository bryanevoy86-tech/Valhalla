import importlib
from fastapi.testclient import TestClient


def get_client():
    mod = importlib.import_module('main')
    return TestClient(mod.app)


def test_contract_flow():
    c = get_client()
    # create template
    r = c.post('/api/contract/template', json={"name":"Test","jurisdiction":"MB","structure":["CL1","CL2"]})
    assert r.status_code == 200
    tid = r.json().get('template_id')
    assert tid == 100
    # draft
    r = c.post('/api/contract/draft', json={"deal_id":1,"template_id":tid,"variables":{"price":123},"counterparty_email":"x@y.z","counterparty_name":"Jane"})
    assert r.status_code == 200
    cid = r.json().get('contract_id')
    # build pdf
    r = c.post(f'/api/contract/pdf/{cid}')
    assert r.status_code == 200
    assert r.json().get('pdf_url')
    # send
    r = c.post(f'/api/contract/send/{cid}')
    assert r.status_code == 200
    # status
    r = c.get(f'/api/contract/status/{cid}')
    assert r.status_code == 200


def test_contract_webhook():
    c = get_client()
    r = c.post('/api/contract/webhook/esign', json={"event":"signed","contract_id":999})
    assert r.status_code == 200
    assert r.json().get('ok') is True
