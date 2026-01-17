from __future__ import annotations

import re
from typing import Any, Dict

def parse(text: str) -> Dict[str, Any]:
    t = (text or "").strip()
    if not t:
        raise ValueError("text required")

    # Patterns:
    # bill: "<name> <amount> on <day>"
    m = re.match(r"^(?P<name>[A-Za-z0-9 \-_/]+)\s+(?P<amount>\d+(\.\d+)?)\s+on\s+(?P<day>\d{1,2})(st|nd|rd|th)?$", t, re.IGNORECASE)
    if m:
        return {"intent": "add_bill", "payload": {"name": m.group("name").strip(), "amount": float(m.group("amount")), "cadence": "monthly", "due_day": int(m.group("day"))}}

    # add item: "add <item>"
    m = re.match(r"^add\s+(?P<item>.+)$", t, re.IGNORECASE)
    if m:
        return {"intent": "add_item", "payload": {"item": m.group("item").strip()}}

    # event: "event <title> <YYYY-MM-DD> <HH:MM>"
    m = re.match(r"^event\s+(?P<title>.+?)\s+(?P<date>\d{4}-\d{2}-\d{2})(\s+(?P<time>\d{2}:\d{2}))?$", t, re.IGNORECASE)
    if m:
        return {"intent": "add_event", "payload": {"title": m.group("title").strip(), "date": m.group("date"), "time": (m.group("time") or "")}}

    return {"intent": "unknown", "payload": {"raw": t}}
