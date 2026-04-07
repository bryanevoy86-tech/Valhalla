import os
import urllib.request

URL = os.environ.get(
    "DAILY_EMAIL_URL",
    "https://valhalla-api-ha6a.onrender.com/api/notify/daily-ops-email"
)

req = urllib.request.Request(URL, method="POST")
with urllib.request.urlopen(req, timeout=30) as resp:
    print(resp.read().decode())
