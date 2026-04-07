import os
import subprocess
from typing import Optional, Tuple


def _run(cmd: list[str], cwd: Optional[str] = None) -> Tuple[int, str, str]:
    p = subprocess.Popen(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    out, err = p.communicate()
    return p.returncode, out, err


def git_autocommit_and_push(
    repo_dir: str,
    message: str,
    remote: str = "origin",
    branch: str = "main",
    user_name: str = "Heimdall Bot",
    user_email: str = "heimdall-bot@valhalla.local",
    token: str = "",
) -> dict:
    result: dict = {"ok": False, "steps": []}

    if not repo_dir:
        return {"ok": False, "error": "repo_dir not provided"}

    # Ensure repo exists
    code, out, err = _run(["git", "rev-parse", "--is-inside-work-tree"], cwd=repo_dir)
    result["steps"].append({"cmd": "rev-parse", "code": code, "out": out, "err": err})
    if code != 0:
        return {"ok": False, "error": f"Not a git repo: {repo_dir}", "steps": result["steps"]}

    # Config user
    for k, v in (("user.name", user_name), ("user.email", user_email)):
        code, out, err = _run(["git", "config", k, v], cwd=repo_dir)
        result["steps"].append({"cmd": f"config {k}", "code": code, "out": out, "err": err})

    # Optional: embed token into remote URL if provided
    if token:
        code, out, err = _run(["git", "remote", "get-url", remote], cwd=repo_dir)
        result["steps"].append({"cmd": f"remote get-url {remote}", "code": code, "out": out, "err": err})
        if code == 0:
            url = out.strip()
            if url.startswith("https://") and "@" not in url:
                # Turn https://github.com/owner/repo.git into https://x-access-token:TOKEN@github.com/owner/repo.git
                parts = url.split("https://", 1)[1]
                new_url = f"https://x-access-token:{token}@{parts}"
                code, out, err = _run(["git", "remote", "set-url", remote, new_url], cwd=repo_dir)
                result["steps"].append({"cmd": f"remote set-url {remote}", "code": code, "out": out, "err": err})

    # Add and commit
    code, out, err = _run(["git", "add", "-A"], cwd=repo_dir)
    result["steps"].append({"cmd": "add -A", "code": code, "out": out, "err": err})

    code, out, err = _run(["git", "commit", "-m", message], cwd=repo_dir)
    result["steps"].append({"cmd": "commit", "code": code, "out": out, "err": err})
    # If nothing to commit, git returns non-zero. Not fatal.

    # Rebase pull then push
    code, out, err = _run(["git", "pull", "--rebase", remote, branch], cwd=repo_dir)
    result["steps"].append({"cmd": f"pull --rebase {remote} {branch}", "code": code, "out": out, "err": err})

    code, out, err = _run(["git", "push", remote, f"HEAD:{branch}"], cwd=repo_dir)
    result["steps"].append({"cmd": f"push {remote} HEAD:{branch}", "code": code, "out": out, "err": err})

    result["ok"] = (code == 0)
    if code != 0 and not result.get("error"):
        result["error"] = err.strip() or "push failed"
    return result
