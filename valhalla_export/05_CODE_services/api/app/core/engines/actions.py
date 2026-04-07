from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EngineAction:
    """
    An action the system may attempt.

    If real_world_effect=True, it must be blocked in SANDBOX.
    """
    name: str
    real_world_effect: bool = False


# Outbound actions (blocked in SANDBOX)
OUTREACH = EngineAction("OUTREACH", real_world_effect=True)
CONTRACT_SEND = EngineAction("CONTRACT_SEND", real_world_effect=True)

# Optional future actions (examples)
DISPO_SEND = EngineAction("DISPO_SEND", real_world_effect=True)
MONEY_MOVE = EngineAction("MONEY_MOVE", real_world_effect=True)

# Read-only / internal actions (allowed in SANDBOX)
READ_ONLY = EngineAction("READ_ONLY", real_world_effect=False)
COMPUTE = EngineAction("COMPUTE", real_world_effect=False)
