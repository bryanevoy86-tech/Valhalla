from __future__ import annotations

import re
from typing import Tuple, Optional

# Very lightweight inference helpers.
# You can refine later with a real geocoder, but this is enough to wire systems now.

PROVINCES = {
    "BC": ["british columbia", "bc"],
    "AB": ["alberta", "ab"],
    "SK": ["saskatchewan", "sk"],
    "MB": ["manitoba", "mb"],
    "ON": ["ontario", "on"],
    "QC": ["quebec", "qc", "québec"],
    "NB": ["new brunswick", "nb"],
    "NS": ["nova scotia", "ns"],
    "PE": ["prince edward island", "pei", "pe"],
    "NL": ["newfoundland", "labrador", "nl"],
    "YT": ["yukon", "yt"],
    "NT": ["northwest territories", "nt"],
    "NU": ["nunavut", "nu"],
}

# Common Canadian cities we can treat as market labels when present in region text
COMMON_MARKETS = [
    "toronto", "ottawa", "hamilton", "london", "windsor",
    "montreal", "quebec city", "gatineau", "laval",
    "vancouver", "surrey", "burnaby", "richmond", "victoria",
    "calgary", "edmonton",
    "winnipeg", "brandon",
    "saskatoon", "regina",
    "halifax",
    "fredericton", "moncton", "saint john",
    "st. john's", "st johns",
]

def infer_province_market(region: Optional[str], address: Optional[str] = None) -> Tuple[Optional[str], str]:
    """
    Returns (province_code, market_label).
    market_label defaults to "ALL".
    """
    text = " ".join([region or "", address or ""]).strip().lower()
    if not text:
        return None, "ALL"

    # Province inference (by keyword)
    province = None
    for code, keys in PROVINCES.items():
        for k in keys:
            if re.search(rf"\b{re.escape(k)}\b", text):
                province = code
                break
        if province:
            break

    # Market inference (by common city)
    market = "ALL"
    for m in COMMON_MARKETS:
        if re.search(rf"\b{re.escape(m)}\b", text):
            market = m.upper().replace(" ", "_")
            break

    # If region contains "CA-ON" style, honor it
    m = re.search(r"\bCA[-\s]?([A-Z]{2})\b", (region or "").upper())
    if m:
        province = m.group(1)

    return province, market
