import glob
import os
import re

from .logging import get_logger

log = get_logger("secscan")

EN = os.getenv("SECSCAN_ENABLED", "false").lower() in ("1", "true", "yes")
MAX = int(os.getenv("SECSCAN_MAX_LINES", "2000"))
LOG_PATH = os.getenv("LOG_JSON_PATH", "/data/app.jsonl")

PATTERNS = [
    re.compile(r"(?i)aws_secret_access_key[:=]\s*[A-Za-z0-9/+=]{35,45}"),
    re.compile(r"(?i)authorization[:=]\s*Bearer\s+[A-Za-z0-9\-_\.]{16,}"),
    re.compile(r"(?i)api[\-_ ]?key[:=]\s*[A-Za-z0-9\-_]{12,}"),
]


def scan_recent():
    if not EN:
        return {"ok": True, "hits": []}
    hits = []
    for f in sorted(glob.glob(LOG_PATH + "*"))[-3:]:
        try:
            for i, line in enumerate(open(f, encoding="utf-8", errors="ignore")):
                if i > MAX:
                    break
                for rx in PATTERNS:
                    if rx.search(line):
                        hits.append({"file": f.split("/")[-1], "line": line[:240]})
                        break
        except Exception:
            pass
    if hits:
        log.error("secscan.hit", count=len(hits))
    return {"ok": True, "hits": hits}
