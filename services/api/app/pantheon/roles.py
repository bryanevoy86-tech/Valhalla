"""Canonical names and local monitoring lenses for the expanded Pantheon."""
from typing import Literal, get_args

Role = Literal[
    "HEIMDALL", "ODIN", "LOKI", "NORNS", "TYR", "FORSETI", "VIDAR", "MIMIR", "NJORD", "FREYJA",
    "BRAGI", "HUGINN", "MUNINN", "VALKYRIE", "FENRIR", "SKALD", "JOTUNN", "KING", "QUEEN",
    "VOICE", "VISION",
]
ROLES = get_args(Role)

# These lenses state what the current local adapters actually observe.
LENSES = {
    "HEIMDALL": "work_queue", "ODIN": "engine_readiness", "LOKI": "counter_evidence",
    "NORNS": "forecast_outcomes", "TYR": "approval_evidence", "FORSETI": "counter_evidence",
    "VIDAR": "work_queue", "MIMIR": "verified_learning", "NJORD": "engine_readiness",
    "FREYJA": "engine_readiness", "BRAGI": "verified_learning", "HUGINN": "engine_readiness",
    "MUNINN": "verified_learning", "VALKYRIE": "approval_evidence", "FENRIR": "counter_evidence",
    "SKALD": "verified_learning", "JOTUNN": "counter_evidence", "KING": "approval_evidence",
    "QUEEN": "work_queue", "VOICE": "work_queue", "VISION": "engine_readiness",
}
