import os

from fastapi import Request

from .logging import get_logger
from .metrics import NS, Counter, _registry

log = get_logger("geoip")

EN = os.getenv("GEOIP_ENABLED", "false").lower() in ("1", "true", "yes")
COUNTS = Counter(f"{NS}_country_hits_total", "Hits by country", ["country"], registry=_registry)

reader = None
if EN:
    try:
        import maxminddb

        reader = maxminddb.open_database(os.getenv("GEOIP_DB_PATH", "/data/GeoLite2-Country.mmdb"))
    except Exception as e:
        log.error("geoip.db.error", err=str(e))


async def middleware(request: Request, call_next):
    country = "ZZ"
    if EN and reader:
        ip = request.client.host
        try:
            r = reader.get(ip) or {}
            country = (r.get("country") or {}).get("iso_code") or country
        except Exception:
            pass
    COUNTS.labels(country=country).inc()
    return await call_next(request)
