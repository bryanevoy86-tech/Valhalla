import sqlite3
conn = sqlite3.connect('valhalla_local.db')
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = [row[0] for row in cursor.fetchall()]
print("Tables in database:")
for t in tables:
    print(f"  {t}")
conn.close()
