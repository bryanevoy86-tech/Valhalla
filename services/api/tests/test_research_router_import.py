"""
Test that the research router can be imported (proves wiring works).
Marked as @pytest.mark.unit (no DB or network required).
"""
import pytest


@pytest.mark.unit
def test_research_router_import():
    from app.routers.research import router
    assert router is not None
    assert router.prefix == "/research"
    assert "research" in router.tags
