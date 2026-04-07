import json
import os
from typing import List

from app.core.outcomes.models import OutcomeRecord


DEFAULT_OUTCOMES_FILE = os.environ.get(
    "OUTCOMES_FILE",
    os.path.join(os.getcwd(), "var", "outcomes.jsonl"),
)


class OutcomeStore:
    """
    Append-only JSONL store for outcomes.
    - No DB assumptions.
    - Works in dev + prod.
    """
    def __init__(self, path: str = DEFAULT_OUTCOMES_FILE):
        self.path = path

    def _ensure_dir(self):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)

    def append(self, rec: OutcomeRecord) -> OutcomeRecord:
        self._ensure_dir()
        rec = rec.normalize()
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec.__dict__, ensure_ascii=False) + "\n")
        return rec

    def read_all(self, limit: int = 500) -> List[OutcomeRecord]:
        if not os.path.exists(self.path):
            return []
        out: List[OutcomeRecord] = []
        with open(self.path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    raw = json.loads(line)
                    out.append(OutcomeRecord(**raw))
                except Exception:
                    continue
        return out[-limit:]
