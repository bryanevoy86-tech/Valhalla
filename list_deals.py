import sqlite3
conn = sqlite3.connect('valhalla_local.db')
cursor = conn.cursor()
cursor.execute("SELECT id, title, lead_id, stage, status FROM deals LIMIT 10")
rows = cursor.fetchall()
print("Deals in database:")
if rows:
    for row in rows:
        print(f"  ID={row[0]}, Title={row[1]}, LeadID={row[2]}, Stage={row[3]}, Status={row[4]}")
else:
    print("  (no deals found)")
conn.close()
