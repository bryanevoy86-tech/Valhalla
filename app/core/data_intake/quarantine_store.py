import json
import os
from typing import Dict, List, Optional

from app.core.data_intake.models import IntakeItem


DEFAULT_QUARANTINE_FILE = os.environ.get(
    "QUARANTINE_FILE",
    os.path.join(os.getcwd(), "var", "quarantine.json"),
)


class QuarantineStore:
    """
    Simple JSON store for quarantine items with statuses.
    Fail-closed: items are QUARANTINE until promoted.
    """
    def __init__(self, path: str = DEFAULT_QUARANTINE_FILE):
        self.path = path

    def _ensure_dir(self):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)

    def _load_raw(self) -> Dict[str, Dict]:
        if not os.path.exists(self.path):
            return {}
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                return json.load(f) or {}
        except Exception:
            return {}

    def _save_raw(self, raw: Dict[str, Dict]) -> None:
        self._ensure_dir()
        tmp = self.path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(raw, f, indent=2, ensure_ascii=False)
        os.replace(tmp, self.path)

    def upsert(self, item: IntakeItem) -> IntakeItem:
        raw = self._load_raw()
        item = item.normalize()
        raw[item.item_id] = item.__dict__
        self._save_raw(raw)
        return item

    def get(self, item_id: str) -> Optional[IntakeItem]:
        raw = self._load_raw()
        data = raw.get(item_id)
        if not data:
            return None
        try:
            return IntakeItem(**data)
        except Exception:
            return None

    def list(self, status: str = "QUARANTINE", limit: int = 200) -> List[IntakeItem]:
        raw = self._load_raw()
        items: List[IntakeItem] = []
        for _, data in raw.items():
            try:
                itm = IntakeItem(**data)
                if itm.status.upper() == status.upper():
                    items.append(itm)
            except Exception:
                continue
        # newest-ish last write order not guaranteed; fine for now
        return items[:limit]

    def count_by_status(self, status: str) -> int:
        return len(self.list(status=status, limit=10_000))
