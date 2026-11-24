#!/usr/bin/env python3
"""Execute one separately authorized native sandbox refund intent."""
import argparse
import json
import os
from pathlib import Path
import runpy
from uuid import UUID

import business_factory_worker  # adds the API package path

from fastapi import HTTPException

from app.core.db import SessionLocal
from app.services.stripe_sandbox_refund import configured_dispatch


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--order-id", type=UUID, required=True)
    args = parser.parse_args()
    check = runpy.run_path(str(Path(__file__).resolve().parents[4] / "scripts" / "staging_preflight.py"))["check"]
    if check(os.environ, "refund-writer"):
        print(json.dumps({"status": "HELD", "reason": "STAGING_PREFLIGHT"}))
        return 2
    try:
        with SessionLocal() as db:
            result = configured_dispatch(db, args.order_id)
    except HTTPException as exc:
        print(json.dumps({"status": "HELD", "http_status": exc.status_code}))
        return 2
    print(json.dumps({"status": result["status"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
