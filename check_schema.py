#!/usr/bin/env python
import sqlite3

conn = sqlite3.connect('valhalla_local.db')
cursor = conn.cursor()

print("OFFERS TABLE SCHEMA:")
cursor.execute("PRAGMA table_info(offers)")
for col in cursor.fetchall():
    print(f"  {col[1]}: {col[2]}")

print("\nCONTRACTS TABLE SCHEMA:")
cursor.execute("PRAGMA table_info(contracts)")
for col in cursor.fetchall():
    print(f"  {col[1]}: {col[2]}")

print("\nDEALS TABLE SCHEMA:")
cursor.execute("PRAGMA table_info(deals)")
for col in cursor.fetchall():
    print(f"  {col[1]}: {col[2]}")

print("\n\nCURRENT OFFERS:")
cursor.execute("SELECT id, deal_id, offer_price, status FROM offers LIMIT 5")
for row in cursor.fetchall():
    print(f"  ID={row[0]}, deal_id={row[1]}, price={row[2]}, status={row[3]}")

print("\nCURRENT CONTRACTS:")
cursor.execute("SELECT id, deal_id, offer_id, status FROM contracts LIMIT 5")
for row in cursor.fetchall():
    print(f"  ID={row[0]}, deal_id={row[1]}, offer_id={row[2]}, status={row[3]}")

conn.close()
