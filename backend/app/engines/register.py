"""Engine registration - single source of engine lifecycle management."""
from ..core_gov.engines.registry import register_engine
from .wholesaling import WholesalingEngine
from .fx_arbitrage import FXArbitrageEngine


def register_all_engines():
    """Register all engine implementations at startup."""
    register_engine(WholesalingEngine())
    register_engine(FXArbitrageEngine())
