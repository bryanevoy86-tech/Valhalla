import os, requests, pytest

pytestmark = pytest.mark.integration

API = os.environ.get('API')

@pytest.mark.skipif(not API, reason='API not set')
def test_health_live():
    r = requests.get(API.rstrip('/') + '/healthz', timeout=3)
    assert r.status_code == 200
