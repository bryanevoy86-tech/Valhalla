#!/usr/bin/env python3
import os
os.environ['DATABASE_URL'] = 'postgresql://user:pass@localhost/valhalla'
os.environ['VALHALLA_JWT_SECRET'] = 'test-secret'

from services.api.main_launch import app
print(f'Launch routes: {len(app.routes)}')
