"""
Module 42: Job Runner
Executes cron jobs on demand or schedule.
"""
from app.cron.registry import CRON_JOBS, get_job


def run_job(name):
    """
    Run a cron job by name.
    
    Args:
        name: Job name (e.g., 'daily_ops')
    
    Returns:
        dict: Job result or error
    """
    job_config = get_job(name)
    
    if not job_config:
        return {
            "status": "error",
            "error": "job_not_found",
            "job_name": name
        }
    
    try:
        handler = job_config["handler"]
        result = handler()
        return {
            "status": "success",
            "job_name": name,
            "result": result
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "job_name": name
        }


def list_available_jobs():
    """
    List all available jobs.
    
    Returns:
        dict: All jobs with schedules and descriptions
    """
    return {
        name: {
            "schedule": config["schedule"],
            "description": config["description"]
        }
        for name, config in CRON_JOBS.items()
    }
