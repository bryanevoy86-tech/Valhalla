from __future__ import annotations
import re
from typing import Any, Dict, Optional

RE_MONEY = re.compile(r"(?P<amt>\d+(?:\.\d{1,2})?)")
RE_DATE = re.compile(r"(?P<date>\d{4}-\d{2}-\d{2})")
RE_DAY_OF_MONTH = re.compile(r"(?:on|due|paid)\s+(?:the\s+)?(?P<day>\d{1,2})(?:st|nd|rd|th)?\b", re.IGNORECASE)

CAD_WORDS = {"cad", "canada", "canadian"}
USD_WORDS = {"usd", "us", "american"}

def infer_currency(text: str) -> str:
    t = (text or "").lower()
    if any(w in t for w in USD_WORDS):
        return "USD"
    return "CAD"

def infer_cadence(text: str) -> str:
    t = (text or "").lower()
    if "weekly" in t:
        return "weekly"
    if "biweekly" in t or "bi-weekly" in t:
        return "biweekly"
    if "every 3 months" in t or "quarter" in t or "quarterly" in t:
        return "quarterly"
    if "yearly" in t or "annual" in t:
        return "yearly"
    if "monthly" in t:
        return "monthly"
    # default if a day-of-month is mentioned
    if RE_DAY_OF_MONTH.search(t):
        return "monthly"
    return "once"

def extract_amount(text: str) -> Optional[float]:
    m = RE_MONEY.search(text or "")
    if not m:
        return None
    try:
        return float(m.group("amt"))
    except Exception:
        return None

def extract_date(text: str) -> str:
    m = RE_DATE.search(text or "")
    return (m.group("date") if m else "")

def extract_due_day(text: str) -> int:
    m = RE_DAY_OF_MONTH.search(text or "")
    if not m:
        return 0
    try:
        d = int(m.group("day"))
        return d if 1 <= d <= 31 else 0
    except Exception:
        return 0
