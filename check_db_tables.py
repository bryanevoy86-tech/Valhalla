#!/usr/bin/env python3
import os
import sqlite3

os.environ.setdefault('DATABASE_URL', 'sqlite:///valhalla_local.db')
os.environ.setdefault('VALHALLA_JWT_SECRET', 'dev-secret-key')

conn = sqlite3.connect('valhalla_local.db')
cursor = conn.cursor()

# Check tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
tables = cursor.fetchall()
print('Database tables:')
for table in tables[:30]:  # Show first 30
    print(f'  - {table[0]}')

# Check leads table specifically
try:
    cursor.execute('PRAGMA table_info(leads);')
    cols = cursor.fetchall()
    if cols:
        print(f'\nleads table columns:')
        for col in cols:
            print(f'  {col[1]} {col[2]}')
    else:
        print('\nNo leads table found')
except Exception as e:
    print(f'Error querying leads: {e}')

# Check deals table
try:
    cursor.execute('PRAGMA table_info(deals);')
    cols = cursor.fetchall()
    if cols:
        print(f'\ndeals table columns:')
        for col in cols:
            print(f'  {col[1]} {col[2]}')
except Exception as e:
    print(f'Error querying deals: {e}')

conn.close()
