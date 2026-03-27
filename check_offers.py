import sqlite3
conn = sqlite3.connect('valhalla_local.db')
cursor = conn.cursor()
cursor.execute("PRAGMA table_info(offers);")
cols = cursor.fetchall()
print("offers table:")
for col in cols:
    print(f'  {col[1]} {col[2]}')
conn.close()
