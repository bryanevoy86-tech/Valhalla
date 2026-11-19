"""Execute registered cron handlers without mistaking invocation for success."""
from app.cron.registry import CRON_JOBS, get_job


def run_job(name: str) -> dict:
    job_config = get_job(name)
    if not job_config:
        return {"status": "error", "error": "job_not_found", "job_name": name}

    try:
        result = job_config["handler"]()
    except Exception as exc:
        return {"status": "error", "error": str(exc), "job_name": name}

    # Calling a handler is not proof the underlying business operation ran.
    # Every handler must provide positive evidence of verified completion.
    if isinstance(result, dict):
        if result.get("status") in {"error", "failed", "blocked"}:
            return {"status": result["status"], "job_name": name, "result": result}
        if result.get("verified") is True and result.get("status") in {"success", "complete"}:
            return {"status": "success", "job_name": name, "result": result}

    return {
        "status": "unverified",
        "job_name": name,
        "result": result,
        "error": "handler did not provide verified completion evidence",
    }


def list_available_jobs():
    return {
        name: {"schedule": config["schedule"], "description": config["description"]}
        for name, config in CRON_JOBS.items()
    }
