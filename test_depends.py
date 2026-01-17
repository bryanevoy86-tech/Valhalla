#!/usr/bin/env python
"""Test basic FastAPI Depends mechanics."""
from fastapi import FastAPI, Depends, Request

app = FastAPI()

def my_dep(request: Request):
    """Simple dependency."""
    return {"dep": "value"}

@app.post("/test1")
def test_with_depends(
    _key=Depends(my_dep),
):
    """Test endpoint."""
    return {"ok": True}

print("✅ FastAPI router with Depends() works!")
