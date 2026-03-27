import sqlite3
conn = sqlite3.connect('valhalla_local.db')
cursor = conn.cursor()

# Get leads schema
cursor.execute("PRAGMA table_info(leads)")
columns = cursor.fetchall()

print("leads TABLE SCHEMA:")
for col in columns:
    print(f"  {col[1]:25} {col[2]:15}")
    
conn.close()
