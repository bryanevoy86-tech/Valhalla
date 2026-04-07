from app.core.engines.actions import EngineAction
from app.core.engines.errors import EngineBlocked
from app.core.engines.guard import engine_guard
from app.core.engines.runtime import engine_state_store


def enforce_engine(engine_name: str, action: EngineAction) -> None:
    """
    Runtime enforcement helper.
    Use this in routers/services before doing anything meaningful.
    """
    state = engine_state_store.get_state(engine_name)
    try:
        engine_guard(
            engine_name=engine_name,
            current_state=state,
            requires_real_world_effect=action.real_world_effect,
        )
    except Exception as e:
        raise EngineBlocked(str(e)) from e
