import importlib, traceback
try:
    m = importlib.import_module('valhalla.services.api.main')
    print('Imported app:', getattr(m, 'app', None))
    from fastapi.testclient import TestClient
    client = TestClient(m.app)
    r = client.get('/api/health')
    print('STATUS', r.status_code)
    print('BODY', r.json())
except Exception:
    traceback.print_exc()
