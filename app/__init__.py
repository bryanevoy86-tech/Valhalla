"""Application package initialization.

Expose the FastAPI `app` instance at package root.
Add routers/modules here as the project grows.
"""

from .main import app  # re-export for convenience

__all__ = ["app"]
