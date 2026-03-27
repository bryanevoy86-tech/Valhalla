import sqlite3
conn = sqlite3.connect('valhalla_local.db')
cursor = conn.cursor()

# Get audit_logs schema
cursor.execute("PRAGMA table_info(audit_logs)")
columns = cursor.fetchall()

print("audit_logs TABLE SCHEMA:")
for col in columns:
    print(f"  {col[1]:25} {col[2]:15} NULL={col[3]}")
    
conn.close()
