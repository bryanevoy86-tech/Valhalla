import base64
import hashlib
import hmac
import json
import time
from typing import Dict

import aiohttp


def sign_payload(secret: str, payload: Dict) -> Dict[str, str]:
    body = json.dumps(payload, separators=(",", ":"), ensure_ascii=False)
    ts = str(int(time.time()))
    to_sign = f"{ts}.{body}".encode()
    sig = hmac.new(secret.encode("utf-8"), to_sign, hashlib.sha256).digest()
    b64 = base64.urlsafe_b64encode(sig).decode("ascii")
    return {
        "X-Timestamp": ts,
        "X-Signature": b64,
        "Content-Type": "application/json",
    }


async def post_webhook(url: str, headers: Dict[str, str], payload: Dict) -> tuple[bool, str | None]:
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15)) as sess:
        async with sess.post(url, headers=headers, json=payload) as resp:
            ok = 200 <= resp.status < 300
            text = await resp.text()
            return ok, None if ok else f"HTTP {resp.status}: {text}"
