#!/usr/bin/env python
"""
Minimal test app for lead engine router without full app dependencies.
"""

import os
import sys

os.environ['VALHALLA_JWT_SECRET'] = 'dev-secret'
os.environ['DATABASE_URL'] = 'sqlite:///./backend_validation.db'

sys.path.insert(0, 'd:/dev/services/api')
os.chdir('d:/dev/services/api')

from fastapi import FastAPI
from app.routers import lead_engine

app = FastAPI(title="Lead Engine Test")
app.include_router(lead_engine.router)

if __name__ == "__main__":
    import uvicorn
    print("Starting minimal lead engine test server...")
    uvicorn.run(app, host="0.0.0.0", port=9001, reload=False)
