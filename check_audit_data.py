import sqlite3
conn = sqlite3.connect('valhalla_local.db')
cursor = conn.cursor()

# Check audit_logs data
cursor.execute("SELECT COUNT(*) FROM audit_logs")
count = cursor.fetchone()[0]
print(f"audit_logs has {count} rows")

if count > 0:
    cursor.execute("SELECT * FROM audit_logs LIMIT 1")
    row = cursor.fetchone()
    cols = [desc[0] for desc in cursor.description]
    print(f"\nColumns: {cols}")
    print(f"Sample row: {row}")
else:
    print("\nNo data in audit_logs")
    
conn.close()
