import json
import sys
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

BASE = "http://localhost:8000"

ENDPOINTS = [
    "/health",
    "/docs",
    "/api/launch/status",
    "/api/go-button/status",
    "/api/eia/status",
]

def fetch(path):
    req = Request(BASE + path, method="GET")
    with urlopen(req, timeout=10) as r:
        return r.status, r.read().decode("utf-8", errors="ignore")

def main():
    results = []
    for ep in ENDPOINTS:
        try:
            status, body = fetch(ep)
            results.append({"endpoint": ep, "status": status, "ok": status == 200})
        except HTTPError as e:
            results.append({"endpoint": ep, "status": e.code, "ok": False})
        except URLError as e:
            results.append({"endpoint": ep, "status": "CONNECTION_ERROR", "ok": False})
        except Exception as e:
            results.append({"endpoint": ep, "status": f"ERROR: {e}", "ok": False})

    print(json.dumps(results, indent=2))

    failed = [r for r in results if not r["ok"]]
    if failed:
        sys.exit(1)

if __name__ == "__main__":
    main()
