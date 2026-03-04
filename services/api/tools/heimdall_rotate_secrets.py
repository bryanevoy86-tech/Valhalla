#!/usr/bin/env python3
"""
Heimdall - Safe Secret Rotation (human-in-the-loop)

WHAT THIS DOES
- Generates new high-entropy secrets locally
- Prints exact Render environment keys with values (copy/paste-ready)
- Never writes secrets to disk
- Never calls Render APIs
- Never stores secrets (only stdout)

WHAT YOU DO
- Run this locally (VS Code terminal) when you want rotation
- Copy/paste values into Render manually
- Redeploy
- Verify endpoints

USAGE
  python services/api/tools/heimdall_rotate_secrets.py --rotate jwt
  python services/api/tools/heimdall_rotate_secrets.py --rotate weweb
  python services/api/tools/heimdall_rotate_secrets.py --rotate jwt,weweb
  python services/api/tools/heimdall_rotate_secrets.py --rotate owner
  python services/api/tools/heimdall_rotate_secrets.py --rotate jwt,weweb,owner
"""

from __future__ import annotations

import argparse
import base64
import getpass
import hashlib
import secrets
import sys
from dataclasses import dataclass
from typing import List


# --------- crypto helpers ---------

def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _pbkdf2_sha256_hash(password: str, iterations: int = 210_000) -> str:
    """
    Produces: pbkdf2_sha256$<iters>$<salt_b64url>$<hash_b64url>
    Compatible with typical PBKDF2-SHA256 validators.
    """
    salt = secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations, dklen=32)
    return f"pbkdf2_sha256${iterations}${_b64url(salt)}${_b64url(dk)}"


def _new_secret_urlsafe(n: int = 48) -> str:
    # token_urlsafe(n) yields ~1.33n chars, strong enough for JWT/shared secrets.
    return secrets.token_urlsafe(n)


@dataclass(frozen=True)
class KV:
    key: str
    value: str


def _banner(title: str) -> None:
    print("\n" + "=" * 78)
    print(title)
    print("=" * 78 + "\n")


def _print_kvs(kvs: List[KV]) -> None:
    _banner("COPY/PASTE THESE INTO RENDER → Valhalla API Service → Environment")
    print("Rules:")
    print("- Do NOT paste these into chat.")
    print("- Do NOT commit these values to git.")
    print("- Paste values directly into the matching keys in Render.\n")

    for kv in kvs:
        print(f"{kv.key}={kv.value}")

    print("\nNext steps (after updating Render):")
    print("1) Render → Manual Deploy → Clear build cache & deploy")
    print("2) Verify:")
    print("   curl -sS https://valhalla-api-ha6a.onrender.com/health")
    print("   curl -sS https://valhalla-api-ha6a.onrender.com/api/runbook/status")
    print("3) Confirm old secret no longer works (where applicable).")
    print("-" * 78 + "\n")


def main(argv: List[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--rotate",
        required=True,
        help="Comma-separated list: jwt,weweb,owner (e.g. jwt,weweb)",
    )
    args = parser.parse_args(argv)

    targets = {t.strip().lower() for t in args.rotate.split(",") if t.strip()}
    allowed = {"jwt", "weweb", "owner"}
    unknown = sorted(list(targets - allowed))
    if unknown:
        print(f"ERROR: Unknown rotate target(s): {unknown}. Allowed: jwt,weweb,owner", file=sys.stderr)
        return 2

    kvs: List[KV] = []

    if "jwt" in targets:
        kvs.append(KV("VALHALLA_JWT_SECRET", _new_secret_urlsafe(48)))

    if "weweb" in targets:
        kvs.append(KV("WEWEB_SHARED_SECRET", _new_secret_urlsafe(48)))

    if "owner" in targets:
        pw1 = getpass.getpass("Enter NEW owner password (won't echo): ")
        pw2 = getpass.getpass("Re-enter NEW owner password: ")
        if pw1 != pw2:
            print("ERROR: Passwords did not match. Aborting.", file=sys.stderr)
            return 1
        kvs.append(KV("VALHALLA_OWNER_PASSWORD_HASH", _pbkdf2_sha256_hash(pw1)))

    if not kvs:
        print("Nothing to rotate. Use --rotate jwt,weweb,owner", file=sys.stderr)
        return 2

    _print_kvs(kvs)

    if "weweb" in targets:
        _banner("IMPORTANT (WeWeb)")
        print("If you rotated WEWEB_SHARED_SECRET, you MUST also update it in WeWeb")
        print("wherever the API Authorization/Bearer token is set, or WeWeb will get 401s.\n")

    _banner("Done")
    print("Secrets were generated locally and printed once to stdout.\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
