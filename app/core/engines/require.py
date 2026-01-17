from app.core.engines.guard_runtime import enforce_engine
from app.core.engines.actions import EngineAction


def require(engine_name: str, action: EngineAction) -> None:
    """
    Standardized guard enforcement.
    Use this as the first line in every endpoint that can cause a real-world effect.
    
    Example:
        from app.core.engines.require import require
        from app.core.engines.actions import OUTREACH
        
        @router.post("/send")
        def send_outreach():
            require("wholesaling", OUTREACH)
            # ... proceed with send logic
    """
    enforce_engine(engine_name, action)
