import pytest

@pytest.mark.unit
def test_research_db_status_route_present():
    from app.routers.research import router
    paths = [getattr(r, 'path', '') for r in router.routes]
    assert any(p.endswith('/db-status') for p in paths)
