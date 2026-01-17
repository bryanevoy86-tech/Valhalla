import json
import urllib.error
import urllib.request
from typing import List

from ..core.config import get_settings


def _get_targets() -> List[str]:
    s = get_settings()
    csv = s.WEBHOOK_URLS_CSV or ""
    return [x.strip() for x in csv.split(",") if x.strip()]


def send_webhook(event: str, data: dict) -> None:
    targets = _get_targets()
    if not targets:
        return
    body = json.dumps({"event": event, "data": data}).encode("utf-8")
    for url in targets:
        try:
            req = urllib.request.Request(
                url, data=body, headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=5) as _:
                pass
        except urllib.error.URLError:
            pass
