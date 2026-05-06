import os
import sys
import urllib.request
import urllib.error

# ===== CONFIG =====
# Make sure this env var exists in Render
url = os.environ.get("DAILY_EMAIL_URL")

print("========== CRON DEBUG START ==========", flush=True)

if not url:
    print("❌ ERROR: DAILY_EMAIL_URL is NOT set", flush=True)
    sys.exit(1)

print(f"➡️ URL being called: {url}", flush=True)

# Change method if needed (GET or POST)
req = urllib.request.Request(url, method="POST")

try:
    with urllib.request.urlopen(req, timeout=30) as resp:
        body = resp.read().decode("utf-8", errors="replace")
        print(f"✅ SUCCESS: Status {resp.status}", flush=True)
        print("📦 RESPONSE BODY:", flush=True)
        print(body, flush=True)

except urllib.error.HTTPError as e:
    print("❌ HTTP ERROR OCCURRED", flush=True)
    print(f"Status Code: {e.code}", flush=True)
    print(f"Reason: {e.reason}", flush=True)
    print(f"URL: {url}", flush=True)

    try:
        error_body = e.read().decode("utf-8", errors="replace")
        print("📦 ERROR RESPONSE BODY:", flush=True)
        print(error_body, flush=True)
    except:
        print("⚠️ Could not read error body", flush=True)

    sys.exit(1)

except Exception as e:
    print("❌ GENERAL ERROR OCCURRED", flush=True)
    print(str(e), flush=True)
    sys.exit(1)

print("========== CRON DEBUG END ==========", flush=True)
