from __future__ import annotations

from typing import Any, Dict, List, Tuple

_ALLOWED_TASK_TYPES = {
    "scaffold_route",
    "scaffold_model",
    "scaffold_crud",
    "run_migration",
    "bundle",
    "spec",
    "job",
    "schedule",
}
_ALLOWED_METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"}


def _err(msg: str) -> Dict[str, str]:
    return {"error": msg}


def _warn(msg: str) -> Dict[str, str]:
    return {"warning": msg}


def _required(
    d: Dict[str, Any], key: str, ctx: str, typ=None, nonempty=True
) -> List[Dict[str, str]]:
    errs = []
    if key not in d:
        errs.append(_err(f"{ctx}: missing required key '{key}'"))
    else:
        val = d[key]
        if typ and not isinstance(val, typ):
            errs.append(_err(f"{ctx}: '{key}' must be {typ.__name__}"))
        elif nonempty and (val == "" or val == [] or val is None):
            errs.append(_err(f"{ctx}: '{key}' cannot be empty"))
    return errs


def _unknown_keys(d: Dict[str, Any], allowed: set[str], ctx: str) -> List[Dict[str, str]]:
    return [_warn(f"{ctx}: unknown key '{k}' will be ignored") for k in d.keys() - allowed]


def validate_task(task: Dict[str, Any]) -> Tuple[bool, List[Dict[str, str]], List[Dict[str, str]]]:
    """
    Returns (ok, errors, warnings)
    """
    errors: List[Dict[str, str]] = []
    warns: List[Dict[str, str]] = []

    if not isinstance(task, dict):
        return False, [_err("task must be a mapping/object")], []

    ttype = task.get("type")
    if ttype not in _ALLOWED_TASK_TYPES:
        return (
            False,
            [_err(f"unknown task type '{ttype}' (allowed: {sorted(_ALLOWED_TASK_TYPES)})")],
            [],
        )

    if ttype == "scaffold_route":
        allowed = {"type", "name", "method", "path", "prefix", "tag", "response"}
        errors += _required(task, "name", "scaffold_route", str)
        errors += _required(task, "method", "scaffold_route", str)
        errors += _required(task, "path", "scaffold_route", str)
        if "method" in task and str(task["method"]).upper() not in _ALLOWED_METHODS:
            errors.append(_err(f"scaffold_route: method must be one of {sorted(_ALLOWED_METHODS)}"))
        warns += _unknown_keys(task, allowed, "scaffold_route")

    elif ttype == "scaffold_model":
        allowed = {"type", "name", "table", "columns"}
        errors += _required(task, "name", "scaffold_model", str)
        errors += _required(task, "table", "scaffold_model", str)
        errors += _required(task, "columns", "scaffold_model", list)
        if isinstance(task.get("columns"), list):
            for i, col in enumerate(task["columns"]):
                if not isinstance(col, dict):
                    errors.append(_err(f"scaffold_model.columns[{i}] must be an object"))
                    continue
                errors += _required(col, "name", f"scaffold_model.columns[{i}]", str)
                errors += _required(col, "type", f"scaffold_model.columns[{i}]", str)
        warns += _unknown_keys(task, allowed, "scaffold_model")

    elif ttype == "scaffold_crud":
        allowed = {"type", "resource", "name", "storage", "table", "prefix", "tag", "fields"}
        # resource or name required
        if not (task.get("resource") or task.get("name")):
            errors.append(_err("scaffold_crud: require 'resource' (or 'name')"))
        storage = (task.get("storage") or "memory").lower()
        if storage not in {"memory", "db"}:
            errors.append(_err("scaffold_crud: storage must be 'memory' or 'db'"))
        if storage == "db" and "table" not in task:
            warns.append(
                _warn(
                    "scaffold_crud: storage=db but 'table' missing; will default to '{resource}s'"
                )
            )
        errors += _required(task, "fields", "scaffold_crud", list)
        if isinstance(task.get("fields"), list):
            for i, f in enumerate(task["fields"]):
                if not isinstance(f, dict):
                    errors.append(_err(f"scaffold_crud.fields[{i}] must be an object"))
                    continue
                errors += _required(f, "name", f"scaffold_crud.fields[{i}]", str)
                errors += _required(f, "type", f"scaffold_crud.fields[{i}]", str)
        warns += _unknown_keys(task, allowed, "scaffold_crud")

    elif ttype == "run_migration":
        allowed = {"type", "file"}
        errors += _required(task, "file", "run_migration", str)
        warns += _unknown_keys(task, allowed, "run_migration")

    elif ttype == "bundle":
        allowed = {"type", "tasks"}
        errors += _required(task, "tasks", "bundle", list)
        warns += _unknown_keys(task, allowed, "bundle")

    elif ttype == "spec":
        allowed = {"type", "name", "resource", "storage", "table", "fields", "routes"}
        errors += _required(task, "name", "spec", str)
        # fields list needed to build model/migration
        errors += _required(task, "fields", "spec", list)
        if "storage" in task and (str(task["storage"]).lower() not in {"memory", "db"}):
            errors.append(_err("spec: storage must be 'memory' or 'db'"))
        # routes are optional but must be well-formed if present
        if isinstance(task.get("routes"), list):
            for i, r in enumerate(task["routes"]):
                if not isinstance(r, dict):
                    errors.append(_err(f"spec.routes[{i}] must be an object"))
                    continue
                errors += _required(r, "name", f"spec.routes[{i}]", str)
                errors += _required(r, "method", f"spec.routes[{i}]", str)
                errors += _required(r, "path", f"spec.routes[{i}]", str)
                if "method" in r and str(r["method"]).upper() not in _ALLOWED_METHODS:
                    errors.append(
                        _err(f"spec.routes[{i}]: method must be one of {_ALLOWED_METHODS}")
                    )
        warns += _unknown_keys(task, allowed, "spec")

    # ---- job ----
    elif ttype == "job":
        allowed = {
            "type",
            "name",
            "shell",
            "python",
            "cwd",
            "timeout",
            "env",
            "artifacts",
            "notify",
        }
        errors += _required(task, "name", "job", str)
        has_shell = "shell" in task
        has_python = "python" in task
        if not (has_shell or has_python):
            errors.append(_err("job: provide either 'shell' or 'python'"))
        if has_shell and has_python:
            errors.append(_err("job: choose only one of 'shell' or 'python'"))
        if "timeout" in task:
            try:
                t = int(task["timeout"])
                if t <= 0:
                    errors.append(_err("job.timeout must be > 0"))
            except Exception:
                errors.append(_err("job.timeout must be an integer"))
        if "env" in task and not isinstance(task["env"], dict):
            errors.append(_err("job.env must be an object of key:value strings"))
        if "artifacts" in task and not isinstance(task["artifacts"], list):
            errors.append(_err("job.artifacts must be a list of path globs"))
        if "notify" in task and not isinstance(task["notify"], dict):
            errors.append(_err("job.notify must be an object with on_success/on_failure/channels"))
        warns += _unknown_keys(task, allowed, "job")

    # ---- schedule ----
    elif ttype == "schedule":
        allowed = {"type", "name", "action", "cron", "timezone", "task"}
        errors += _required(task, "name", "schedule", str)
        action = (task.get("action") or "upsert").lower()
        if action not in {"upsert", "remove"}:
            errors.append(_err("schedule.action must be 'upsert' or 'remove'"))
        if action == "upsert":
            errors += _required(task, "cron", "schedule", dict)
            errors += _required(task, "task", "schedule", dict)
            # nested task must be valid and cannot itself be a schedule
            from copy import deepcopy

            inner = deepcopy(task.get("task", {}))
            if isinstance(inner, dict):
                if inner.get("type") == "schedule":
                    errors.append(_err("schedule.task cannot be another 'schedule'"))
                else:
                    ok, e2, w2 = validate_task(inner)
                    if not ok:
                        errors.append(_err("schedule.task failed validation"))
                        errors.extend(e2)
        warns += _unknown_keys(task, allowed, "schedule")

    ok = len(errors) == 0
    return ok, errors, warns


def lint_task_yaml_str(yaml_str: str) -> Dict[str, Any]:
    try:
        import yaml

        data = yaml.safe_load(yaml_str) or {}
    except Exception as e:
        return {"ok": False, "errors": [{"error": f"yaml parse error: {e}"}], "warnings": []}
    ok, errs, warns = validate_task(data)
    return {"ok": ok, "errors": errs, "warnings": warns, "normalized": data}
