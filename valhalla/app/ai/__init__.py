"""AI helpers and orchestrators for Valhalla.

Expose a small, stable surface for higher-level app code to import:
- `interlink` — cross-document linking helpers
- `providers` — provider-specific adapter layer (OpenAI, local LMs)
- `builder` — builder pipeline orchestration
- `learn` — retrieval/embedding helpers, knowledge management
- `jobs` — background jobs (training, indexing, etc.)
"""
from . import interlink, providers, builder, learn, jobs

__all__ = [
    "interlink",
    "providers",
    "builder",
    "learn",
    "jobs",
]
