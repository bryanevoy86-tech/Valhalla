from __future__ import annotations

from ..audit.audit_log import audit
from .models import GoChecklist, GoNext, GoStep
from .playbook import build_steps, get_checklist_context, band_allows
from .store import load_progress, save_progress

def build_checklist() -> GoChecklist:
    band, status, blocked_reasons = get_checklist_context()
    steps = build_steps()

    progress = load_progress()
    for s in steps:
        if s.id in progress:
            s.done = bool(progress[s.id].get("done", False))
            s.notes = progress[s.id].get("notes")

    # Determine hard blocks
    if status == "red":
        # Mark steps as blocked via reasons; UI will show blocked state
        pass

    return GoChecklist(
        cone_band=band,
        status=status,
        steps=steps,
        blocked_reasons=blocked_reasons,
    )

def complete_step(step_id: str, done: bool, notes: str | None) -> dict:
    progress = load_progress()
    progress[step_id] = {"done": bool(done), "notes": notes}
    save_progress(progress)
    audit("GO_STEP_SET", {"step_id": step_id, "done": done, "notes": notes or ""})
    return {"ok": True, "step_id": step_id, "done": done, "notes": notes}

def next_step() -> GoNext:
    checklist = build_checklist()

    # If RED, we still allow "view dashboard" but block progression steps
    if checklist.status == "red":
        # Find the preflight step (always safe)
        for s in checklist.steps:
            if s.id == "preflight_view_dashboard":
                return GoNext(
                    cone_band=checklist.cone_band,
                    status=checklist.status,
                    next_step=s,
                    message="Status is RED. Only preflight is allowed until failures are resolved.",
                )
        return GoNext(
            cone_band=checklist.cone_band,
            status=checklist.status,
            next_step=None,
            message="Status is RED. Resolve failures before proceeding.",
        )

    # Choose first not-done step that is band-compatible
    for s in checklist.steps:
        if s.done:
            continue
        # band rules: if current band is B, steps with band_min B/C/D are fine; if current is C, steps with B may be too advanced.
        if checklist.cone_band in ("C", "D") and s.band_min == "B":
            continue
        return GoNext(
            cone_band=checklist.cone_band,
            status=checklist.status,
            next_step=s,
            message="Next step ready.",
        )

    return GoNext(
        cone_band=checklist.cone_band,
        status=checklist.status,
        next_step=None,
        message="All Go steps are complete. Maintain weekly rhythm and operate by Cone.",
    )
