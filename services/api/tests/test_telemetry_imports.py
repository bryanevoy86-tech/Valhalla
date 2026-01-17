import importlib

def test_import_telemetry_router():
    m = importlib.import_module('app.routers.telemetry')
    assert hasattr(m, 'router')


def test_import_integrity_event_model():
    m = importlib.import_module('app.models.telemetry')
    assert hasattr(m, 'IntegrityEvent')
