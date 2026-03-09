from __future__ import annotations

from typing import List

from ..cone.service import get_cone_state
from ..health.status import ryg_status
from .models import GoStep

def _band_rank(band: str) -> int:
    # A best -> D worst. Rank higher means "worse".
    order = {"A": 1, "B": 2, "C": 3, "D": 4}
    return order.get(band, 99)

def build_steps() -> List[GoStep]:
    """
    Steps are designed to be:
      - operational and concrete
      - band-aware (B default safe)
      - no automation required
    """
    return [
        GoStep(
            id="preflight_view_dashboard",
            title="Open the Dashboard and confirm status + Cone band",
            why="You only operate when the system is visible. No invisible running.",
            band_min="D",
            blocked_if_red=False,
        ),
        GoStep(
            id="set_opportunistic_caps",
            title="Confirm opportunistic capital caps are set (FX/Collectibles/Sports)",
            why="Caps prevent excitement from becoming risk.",
            band_min="C",
        ),
        GoStep(
            id="confirm_boring_sop",
            title="Confirm boring engines are SOP-only (no optimization tinkering)",
            why="Boring engines exist to reduce pressure and stabilize cashflow.",
            band_min="C",
        ),
        GoStep(
            id="intake_ready",
            title="Turn on Intake (even manual): create a single intake entry path",
            why="No intake = no flow. One door in, everything tracked.",
            band_min="B",
        ),
        GoStep(
            id="lead_log_ready",
            title="Create the Lead Log (single source of truth)",
            why="If it's not logged, it didn't happen — and you can't optimize it.",
            band_min="B",
        ),
        GoStep(
            id="weekly_rhythm",
            title="Set the weekly rhythm: 1 weekly audit + 2 short check-ins",
            why="The system wins by cadence, not hero effort.",
            band_min="B",
        ),
        GoStep(
            id="start_engine_wholesaling_run",
            title="Start Wholesaling (Band B): RUN only what Cone allows",
            why="This is your primary controlled engine in the build phase.",
            band_min="B",
        ),
        GoStep(
            id="start_one_boring_engine",
            title="Start ONE boring engine first (cleaning OR landscaping OR storage)",
            why="One stabilizer first. You earn runway before expansion.",
            band_min="B",
        ),
        GoStep(
            id="first_week_review",
            title="End of Week 1: review dashboard + weekly audit and adjust only if allowed",
            why="We correct course through governance, not emotion.",
            band_min="B",
        ),
    ]

def band_allows(step_band_min: str, current_band: str) -> bool:
    # If current band is worse (C/D), it still "allows" steps that are designed for worse bands.
    # Example: step_min=C is okay when current=C or D, not okay when current=B/A? (Actually if current is better, it's fine.)
    return _band_rank(current_band) >= _band_rank(step_band_min) or _band_rank(current_band) <= _band_rank(step_band_min)

def get_checklist_context() -> tuple[str, str, list[str]]:
    cone = get_cone_state()
    status = ryg_status()
    blocked = []
    if status["status"] == "red":
        blocked.append("System status is RED — resolve failures before progressing.")
    return cone.band, status["status"], blocked
