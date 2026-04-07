from dataclasses import dataclass
from typing import List, Optional


@dataclass
class PolicyResult:
    ok: bool
    blockers: List[str]
    warnings: List[str]

    def to_dict(self):
        return {"ok": self.ok, "blockers": self.blockers, "warnings": self.warnings}


@dataclass
class TransitionRequest:
    engine_name: str
    target_state: str
    reason: str = "policy_transition"
    actor: str = "heimdall"
