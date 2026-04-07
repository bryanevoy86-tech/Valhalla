"""Automated monthly target tracker."""

MONTHLY_TARGET = 5_000_000  # $5M in cents


def target_met(current_cents):
    """Check if monthly target is met."""
    return current_cents >= MONTHLY_TARGET


def get_target_progress(current_cents):
    """Get progress toward monthly target."""
    progress_pct = (current_cents / MONTHLY_TARGET * 100) if MONTHLY_TARGET > 0 else 0
    remaining = max(0, MONTHLY_TARGET - current_cents)
    
    return {
        "target": MONTHLY_TARGET,
        "current": current_cents,
        "remaining": remaining,
        "progress_percent": progress_pct,
        "status": "met" if target_met(current_cents) else "pending",
        "days_left": 30 - (1)  # Simplified
    }


def get_daily_target_pace(day_of_month, current_cents):
    """Get required daily pace to hit target."""
    if day_of_month < 1 or day_of_month > 30:
        return {"error": "Invalid day"}
    
    daily_required = MONTHLY_TARGET / 30
    days_remaining = 30 - day_of_month
    
    if days_remaining <= 0:
        return {
            "daily_target": daily_required,
            "days_remaining": 0,
            "daily_pace_required": 0
        }
    
    daily_pace_required = (MONTHLY_TARGET - current_cents) / days_remaining
    
    return {
        "daily_target": daily_required,
        "days_remaining": days_remaining,
        "daily_pace_required": daily_pace_required,
        "on_track": daily_pace_required <= daily_required
    }


def forecast_month_end(current_cents, days_elapsed, daily_average):
    """Forecast month-end revenue."""
    days_remaining = 30 - days_elapsed
    projected_additional = daily_average * days_remaining
    projected_total = current_cents + projected_additional
    
    return {
        "current": current_cents,
        "days_elapsed": days_elapsed,
        "daily_average": daily_average,
        "projected_total": int(projected_total),
        "vs_target": projected_total - MONTHLY_TARGET,
        "on_track": projected_total >= MONTHLY_TARGET
    }
