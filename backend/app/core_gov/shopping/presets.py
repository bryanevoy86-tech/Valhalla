from __future__ import annotations
from typing import Any, Dict, List

PRESETS = [
    {"name":"milk", "unit":"L", "category":"groceries"},
    {"name":"bread", "unit":"each", "category":"groceries"},
    {"name":"eggs", "unit":"dozen", "category":"groceries"},
    {"name":"toilet paper", "unit":"rolls", "category":"household"},
    {"name":"dish soap", "unit":"each", "category":"household"},
]

def presets() -> Dict[str, Any]:
    return {"presets": PRESETS}
