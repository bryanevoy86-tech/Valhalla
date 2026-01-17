import logging
from typing import Dict

from ..canon.canon import get_engine_spec
from ..cone.service import decide
from .base import Engine, EngineResult

logger = logging.getLogger("valhalla.core_engine_registry")

_ENGINE_REGISTRY: Dict[str, Engine] = {}

class EngineNotRegisteredError(RuntimeError):
    pass

def register_engine(engine: Engine) -> None:
    _ = get_engine_spec(engine.name)  # must exist in Canon
    _ENGINE_REGISTRY[engine.name] = engine
    logger.info("ENGINE_REGISTERED name=%s", engine.name)

def execute(engine_name: str, action: str) -> EngineResult:
    d = decide(engine_name, action)
    if not d.allowed:
        logger.warning("ENGINE_DENIED engine=%s action=%s reason=%s", engine_name, action, d.reason)
        return EngineResult(ok=False, detail=d.reason)

    eng = _ENGINE_REGISTRY.get(engine_name)
    if not eng:
        raise EngineNotRegisteredError(f"Engine '{engine_name}' not registered.")

    if action == "run":
        return eng.run()
    if action == "optimize":
        return eng.optimize()
    if action == "scale":
        return eng.scale()

    return EngineResult(ok=False, detail=f"Unknown action '{action}'")
