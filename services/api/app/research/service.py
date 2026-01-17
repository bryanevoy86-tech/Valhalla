from typing import List, Dict, Any
from .schemas import Result, Source

# In-memory registries (can be swapped to DB later)
SOURCES: List[Source] = []

# Example seed sources (public docs/APIs you frequently reference)
DEFAULT_SOURCES = [
    Source(name="Render Docs", url="https://render.com/docs", type="doc", tags=["deploy","render"]),
    Source(name="FastAPI Docs", url="https://fastapi.tiangolo.com", type="doc", tags=["api","python"]),
]

for s in DEFAULT_SOURCES:
    SOURCES.append(s)

class ResearchService:
    def __init__(self, fetcher=None):
        self.fetcher = fetcher or self._noop_fetch

    def _noop_fetch(self, query: str, limit: int, tags: List[str] | None) -> List[Dict[str, Any]]:
        # Placeholder: returns sources matching tags or all
        matched = [s for s in SOURCES if not tags or any(t in s.tags for t in tags)]
        out = []
        for s in matched[:limit]:
            out.append({
                'title': s.name, 'url': str(s.url), 'snippet': f'Reference: {s.type}', 'meta': {'tags': s.tags}
            })
        return out

    def search(self, query: str, limit: int = 8, tags: List[str] | None = None) -> List[Result]:
        raw = self.fetcher(query, limit, tags)
        return [Result(**r) for r in raw]

    def add_source(self, source: Source):
        # prevent dupes by url
        if any(str(x.url) == str(source.url) for x in SOURCES):
            return
        SOURCES.append(source)

    def list_sources(self) -> List[Source]:
        return list(SOURCES)
