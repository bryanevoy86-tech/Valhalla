"""
Main entry point for Valhalla API.
This module exposes the FastAPI app for deployment with uvicorn.
"""
from valhalla.services.api.main import app

__all__ = ["app"]
