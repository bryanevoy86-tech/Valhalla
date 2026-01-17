from app.core.engines.states import EngineState


ENGINE_REGISTRY = {
    "wholesaling": {
        "layer": 1,
        "initial_state": EngineState.SANDBOX,
        "allows_real_world_effects": True,
        "capital_domain": "OPS_CAPITAL",
    },

    "ops_automation": {
        "layer": 2,
        "initial_state": EngineState.DORMANT,
        "allows_real_world_effects": True,
        "capital_domain": "OPS_CAPITAL",
    },

    "market_intelligence": {
        "layer": 3,
        "initial_state": EngineState.SANDBOX,
        "allows_real_world_effects": False,
        "capital_domain": None,
    },

    "trading_advisory": {
        "layer": 4,
        "initial_state": EngineState.DORMANT,
        "allows_real_world_effects": False,
        "capital_domain": "TRADING_CAPITAL",
    },
}
