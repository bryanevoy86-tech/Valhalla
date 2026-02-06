"""
Module 41: Cron Registry
Central registry of all available cron jobs.
"""
from app.cron.daily_ops import run_daily_ops
from app.cron.monthly_rollup import rollup_monthly

# Registry of all cron jobs
CRON_JOBS = {
    "daily_ops": {
        "handler": run_daily_ops,
        "schedule": "0 2 * * *",  # 2 AM daily
        "description": "Daily contract checks, payment reconciliation, and alerts"
    },
    "monthly_rollup": {
        "handler": rollup_monthly,
        "schedule": "0 0 1 * *",  # 1st of month at midnight
        "description": "Monthly revenue and profit rollup"
    }
}


def get_job(name):
    """
    Get a cron job by name.
    
    Args:
        name: Job name (e.g., 'daily_ops')
    
    Returns:
        dict: Job config or None if not found
    """
    return CRON_JOBS.get(name)


def list_jobs():
    """
    List all available cron jobs.
    
    Returns:
        dict: All jobs with metadata
    """
    return {
        name: {
            "schedule": config["schedule"],
            "description": config["description"]
        }
        for name, config in CRON_JOBS.items()
    }
