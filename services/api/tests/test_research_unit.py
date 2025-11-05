"""
Unit tests for Pack 8 Research Agent (TTL cache, service, schemas).
Mark as @pytest.mark.unit for the CI coverage gate.
"""
import pytest
from app.research.cache import TTLCache
from app.research.service import ResearchService
from app.research.schemas import Source, SearchQuery, Result
import time


@pytest.mark.unit
def test_ttl_cache_roundtrip():
    cache = TTLCache(ttl_seconds=2, max_items=2)
    cache.set("key1", "value1")
    assert cache.get("key1") == "value1"
    assert cache.get("nonexistent") is None


@pytest.mark.unit
def test_ttl_cache_expiry():
    cache = TTLCache(ttl_seconds=1, max_items=10)
    cache.set("ephemeral", "data")
    assert cache.get("ephemeral") == "data"
    time.sleep(1.1)
    assert cache.get("ephemeral") is None


@pytest.mark.unit
def test_ttl_cache_lru_eviction():
    cache = TTLCache(ttl_seconds=60, max_items=2)
    cache.set("a", 1)
    cache.set("b", 2)
    cache.set("c", 3)  # should evict oldest (a)
    assert cache.get("a") is None
    assert cache.get("b") == 2
    assert cache.get("c") == 3


@pytest.mark.unit
def test_research_service_search():
    svc = ResearchService()
    results = svc.search("test", limit=2, tags=None)
    assert isinstance(results, list)
    for r in results:
        assert isinstance(r, Result)


@pytest.mark.unit
def test_research_service_add_source():
    svc = ResearchService()
    before_count = len(svc.list_sources())
    src = Source(name="TestDocs", url="https://test.example.com", type="doc", tags=["test"])
    svc.add_source(src)
    after_count = len(svc.list_sources())
    assert after_count >= before_count
    # no dupe
    svc.add_source(src)
    assert len(svc.list_sources()) == after_count


@pytest.mark.unit
def test_search_query_schema():
    q = SearchQuery(q="fastapi docs", limit=5, tags=["api"])
    assert q.q == "fastapi docs"
    assert q.limit == 5
    assert "api" in q.tags
