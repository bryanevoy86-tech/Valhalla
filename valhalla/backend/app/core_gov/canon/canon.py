from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional


class ConeBand(str, Enum):
    A_EXPANSION = "A"
    B_CAUTION = "B"
    C_STABILIZE = "C"
    D_SURVIVAL = "D"


class EngineClass(str, Enum):
    BORING = "boring"
    ALPHA = "alpha"
    OPPORTUNISTIC = "opportunistic"
    STANDBY = "standby"
    LEGACY = "legacy"


class PantheonRole(str, Enum):
    HEIMDALL = "heimdall"
    LOKI = "loki"
    MIMIR = "mimir"
    VALKYRIE = "valkyrie"
    FENRIR = "fenrir"
    TYR = "tyr"
    ODIN = "odin"
    FREYJA = "freyja"


@dataclass(frozen=True)
class EngineSpec:
    name: str
    engine_class: EngineClass
    allow_optimization: bool
    year1_allowed: bool
    hard_cap_usd: Optional[float] = None


@dataclass(frozen=True)
class Year1Limits:
    max_new_streams: int = 4


# LOCKED: boring engines
BORING_ENGINES: List[EngineSpec] = [
    EngineSpec("storage_units", EngineClass.BORING, allow_optimization=False, year1_allowed=True),
    EngineSpec("cleaning_services", EngineClass.BORING, allow_optimization=False, year1_allowed=True),
    EngineSpec("landscaping_maintenance", EngineClass.BORING, allow_optimization=False, year1_allowed=True),
]

# LOCKED: alpha engines
ALPHA_ENGINES: List[EngineSpec] = [
    EngineSpec("wholesaling", EngineClass.ALPHA, allow_optimization=True, year1_allowed=True),
    EngineSpec("brrrr", EngineClass.ALPHA, allow_optimization=True, year1_allowed=True),
    EngineSpec("flips", EngineClass.ALPHA, allow_optimization=True, year1_allowed=True),
    EngineSpec("residential_rentals", EngineClass.ALPHA, allow_optimization=True, year1_allowed=True),
]

# LOCKED: opportunistic (capped, never scaled)
OPPORTUNISTIC_ENGINES: List[EngineSpec] = [
    EngineSpec("fx_arbitrage", EngineClass.OPPORTUNISTIC, allow_optimization=True, year1_allowed=True, hard_cap_usd=25000.0),
    EngineSpec("collectibles_arbitrage", EngineClass.OPPORTUNISTIC, allow_optimization=True, year1_allowed=True, hard_cap_usd=25000.0),
    EngineSpec("sports_intelligence", EngineClass.OPPORTUNISTIC, allow_optimization=True, year1_allowed=True, hard_cap_usd=15000.0),
]

# LOCKED: standby (cold)
STANDBY_ENGINES: List[EngineSpec] = [
    EngineSpec("equipment_rental", EngineClass.STANDBY, allow_optimization=False, year1_allowed=False),
    EngineSpec("parking_rentals", EngineClass.STANDBY, allow_optimization=False, year1_allowed=False),
    EngineSpec("inspection_compliance", EngineClass.STANDBY, allow_optimization=False, year1_allowed=False),
    EngineSpec("conservative_yield_buckets", EngineClass.STANDBY, allow_optimization=False, year1_allowed=False),
]

# LOCKED: legacy (not counted)
LEGACY_ENGINES: List[EngineSpec] = [
    EngineSpec("ai_real_estate_school", EngineClass.LEGACY, allow_optimization=False, year1_allowed=False),
    EngineSpec("private_capital_fund", EngineClass.LEGACY, allow_optimization=False, year1_allowed=False),
    EngineSpec("childrens_trusts", EngineClass.LEGACY, allow_optimization=False, year1_allowed=False),
    EngineSpec("resort_chain", EngineClass.LEGACY, allow_optimization=False, year1_allowed=False),
    EngineSpec("exploration_salvage", EngineClass.LEGACY, allow_optimization=False, year1_allowed=False),
]

YEAR1_LIMITS = Year1Limits()

ENGINE_CANON: Dict[str, EngineSpec] = {
    e.name: e for e in (BORING_ENGINES + ALPHA_ENGINES + OPPORTUNISTIC_ENGINES + STANDBY_ENGINES + LEGACY_ENGINES)
}


def get_engine_spec(engine_name: str) -> EngineSpec:
    spec = ENGINE_CANON.get(engine_name)
    if not spec:
        raise ValueError(f"Engine '{engine_name}' is not in Canon. Add it to core_gov/canon/canon.py first.")
    return spec
