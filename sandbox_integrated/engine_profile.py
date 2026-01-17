from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Protocol


@dataclass
class EngineItem:
    """Normalized unit of work produced by ingest()."""
    item_id: str
    payload: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EngineActionIntent:
    """
    Proposed action (ALWAYS DRY-RUN in sandbox).
    This is an intent only; the orchestrator never executes irreversible actions.
    """
    action_id: str
    kind: str
    payload: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EngineCycleResult:
    engine_name: str
    ingested: int = 0
    analyzed: int = 0
    intents: int = 0
    notes: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)


class EngineProfile(Protocol):
    """
    Engines must be sandbox-safe and side-effect-free.
    No outbound and no real transactions here—ever.
    """

    name: str

    def ingest(self, *, max_items: int) -> List[EngineItem]:
        ...

    def analyze(self, items: List[EngineItem]) -> List[EngineItem]:
        ...

    def propose_actions(self, items: List[EngineItem], *, max_actions: int) -> List[EngineActionIntent]:
        ...

    def export(self, items: List[EngineItem], intents: List[EngineActionIntent]) -> Dict[str, Any]:
        """
        Writes artifacts only (reports/exports). Returns export metadata for reporting.
        """
        ...

    def cost_model(self) -> Dict[str, Any]:
        """
        Returns estimated compute/capital demand signals used for resource simulation.
        """
        ...
