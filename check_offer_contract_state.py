#!/usr/bin/env python
"""
Check actual state of deal 11, offers, and contracts
"""
import sqlite3

conn = sqlite3.connect('valhalla_local.db')
cursor = conn.cursor()

print("\n" + "="*80)
print("DEAL 11 AND RELATED DATA")
print("="*80)

print("\nDEAL 11:")
cursor.execute('SELECT id, stage, status, arv, estimated_repair_cost FROM deals WHERE id = 11')
deal = cursor.fetchone()
print(f"  ID: {deal[0]}, Stage: {deal[1]}, Status: {deal[2]}, ARV: {deal[3]}, Repairs: {deal[4]}")

print("\nOFFERS FOR DEAL 11:")
cursor.execute('SELECT id, deal_id, offer_price, status FROM offers WHERE deal_id = 11')
offers = cursor.fetchall()
for offer in offers:
    print(f"  ID: {offer[0]}, Deal: {offer[1]}, Price: ${offer[2]}, Status: {offer[3]}")

print("\nCONTRACTS FOR DEAL 11:")
cursor.execute('SELECT id, deal_id, offer_id, status FROM contracts WHERE deal_id = 11')
contracts = cursor.fetchall()
for contract in contracts:
    print(f"  ID: {contract[0]}, Deal: {contract[1]}, Offer: {contract[2]}, Status: {contract[3]}")

print("\nALL OFFERS:")
cursor.execute('SELECT id, deal_id, offer_price FROM offers ORDER BY id')
all_offers = cursor.fetchall()
for offer in all_offers:
    print(f"  ID: {offer[0]}, Deal: {offer[1]}, Price: ${offer[2]}")

print("\nALL CONTRACTS:")
cursor.execute('SELECT id, deal_id, offer_id FROM contracts ORDER BY id')
all_contracts = cursor.fetchall()
for contract in all_contracts:
    print(f"  ID: {contract[0]}, Deal: {contract[1]}, Offer: {contract[2]}")

conn.close()
print()
