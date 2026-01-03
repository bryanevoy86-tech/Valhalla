import logging
from dataclasses import dataclass
from typing import Callable, Any

from ..canon.canon import PantheonRole

logger = logging.getLogger("valhalla.pantheon")

class PantheonViolation(RuntimeError):
    pass

@dataclass(frozen=True)
class AgentContext:
    role: PantheonRole
    name: str

def require_role(ctx: AgentContext, allowed: set[PantheonRole], action: str) -> None:
    if ctx.role not in allowed:
        raise PantheonViolation(f"{ctx.role} not permitted to '{action}'. Allowed={allowed}")

def heimdall_orchestrate(ctx: AgentContext, fn: Callable[..., Any], *args, **kwargs) -> Any:
    require_role(ctx, {PantheonRole.HEIMDALL}, "orchestrate")
    return fn(*args, **kwargs)

def loki_challenge(ctx: AgentContext, hypothesis: str) -> dict:
    require_role(ctx, {PantheonRole.LOKI}, "challenge")
    return {
        "hypothesis": hypothesis,
        "challenge": "List assumptions, failure modes, missing data, counterexamples.",
        "status": "placeholder_v1"
    }

def fenrir_halt(ctx: AgentContext, reason: str) -> dict:
    require_role(ctx, {PantheonRole.FENRIR}, "halt")
    logger.warning("FENRIR_HALT reason=%s", reason)
    return {"halted": True, "reason": reason}
