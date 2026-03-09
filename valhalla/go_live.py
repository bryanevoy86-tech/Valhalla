#!/usr/bin/env python3
"""
VALHALLA GO-LIVE DATA INGESTION
Production go-live activation with real data population
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def enable_go_live(api_base: str) -> bool:
    """Enable go-live mode on the API"""
    try:
        url = f"{api_base}/api/governance/go-live/enable"
        resp = requests.post(url, json={"enabled": True}, timeout=15)
        if resp.status_code in [200, 201]:
            data = resp.json()
            print(f"[OK] Go-live enabled: {data}")
            return True
        else:
            print(f"[ERROR] Failed to enable go-live: {resp.status_code} - {resp.text}")
            return False
    except Exception as e:
        print(f"[ERROR] Exception enabling go-live: {e}")
        return False


def ingest_data(api_base: str, csv_path: str) -> dict:
    """Ingest CSV data via the data ingestion endpoint"""
    try:
        with open(csv_path, "r", encoding="utf-8") as f:
            files = {"file": f}
            url = f"{api_base}/api/data/ingest/csv"
            resp = requests.post(url, files=files, timeout=30)
        
        if resp.status_code in [200, 201]:
            result = resp.json()
            print(f"[OK] Data ingested: {result.get('message', '')}")
            return {
                "ok": True,
                "status_code": resp.status_code,
                "data": result,
            }
        else:
            print(f"[ERROR] Ingestion failed: {resp.status_code} - {resp.text}")
            return {
                "ok": False,
                "status_code": resp.status_code,
                "error": resp.text,
            }
    except FileNotFoundError:
        print(f"[ERROR] CSV file not found: {csv_path}")
        return {"ok": False, "error": f"File not found: {csv_path}"}
    except Exception as e:
        print(f"[ERROR] Exception during ingestion: {e}")
        return {"ok": False, "error": str(e)}


def main():
    parser = argparse.ArgumentParser(description="Go-live with real data ingestion")
    parser.add_argument("--base", default="https://valhalla-api-ha6a.onrender.com",
                       help="API base URL")
    parser.add_argument("--csv", required=True, help="Path to CSV data file")
    parser.add_argument("--no-enable", action="store_true",
                       help="Skip go-live enablement (already enabled)")
    args = parser.parse_args()

    print("\n" + "="*60)
    print("VALHALLA GO-LIVE DATA INGESTION")
    print("="*60)
    print(f"Timestamp (UTC): {utc_now_iso()}")
    print(f"API Base: {args.base}")
    print(f"CSV File: {args.csv}")
    print("="*60 + "\n")

    # Verify CSV exists
    if not Path(args.csv).exists():
        print(f"[FATAL] CSV file not found: {args.csv}")
        return 2

    # Step 1: Enable go-live
    if not args.no_enable:
        print("[STEP 1] Enabling go-live mode...")
        if not enable_go_live(args.base):
            print("[FATAL] Failed to enable go-live. Aborting.")
            return 1
        print()

    # Step 2: Ingest data
    print("[STEP 2] Ingesting live data...")
    result = ingest_data(args.base, args.csv)
    print()

    # Step 3: Report
    print("="*60)
    print("GO-LIVE INGESTION SUMMARY")
    print("="*60)
    print(f"Status: {'SUCCESS' if result['ok'] else 'FAILED'}")
    print(f"Response: {json.dumps(result.get('data') or result.get('error'), indent=2)}")
    print("="*60 + "\n")

    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
