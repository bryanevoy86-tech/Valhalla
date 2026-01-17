"""One-screen dashboard - aggregates status, alerts, capital, and summary."""
from __future__ import annotations

from ..health.status import ryg_status
from ..alerts.router import alerts as alerts_fn
from ..capital.router import capital_status as capital_status_fn
from ..visibility.router import system_summary as system_summary_fn


def one_screen_dashboard() -> dict:
    """Call the underlying functions directly to avoid multiple HTTP requests in UI."""
    status = ryg_status()
    alerts = alerts_fn()
    capital = capital_status_fn()
    summary = system_summary_fn()

    return {
        "status": status,
        "alerts": alerts,
        "capital": capital,
        "summary": summary,
    }
