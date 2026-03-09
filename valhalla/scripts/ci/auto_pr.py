#!/usr/bin/env python3
import glob
import json
import os
import pathlib
import shlex
import subprocess
import urllib.request
from datetime import datetime
from urllib.parse import urlparse

ROOT = pathlib.Path(".").resolve()
CFG = ROOT / "heimdall/agent.config.json"


def cfg():
    try:
        return json.loads(CFG.read_text(encoding="utf-8"))
    except Exception:
        return {}


def run(cmd, cwd=None, check=True):
    if isinstance(cmd, str):
        cmd = shlex.split(cmd)
    p = subprocess.run(cmd, cwd=cwd or ROOT, capture_output=True, text=True)
    if check and p.returncode != 0:
        raise RuntimeError(f"CMD failed {cmd}\nSTDOUT:\n{p.stdout}\nSTDERR:\n{p.stderr}")
    return p


def git(*args, check=True):
    return run(["git", *args], check=check)


def ensure_safe_dir():
    try:
        git("config", "--global", "--add", "safe.directory", str(ROOT))
    except Exception:
        pass


def stamp(fmt):
    now = datetime.now()
    repl = {
        "{{YYYY}}": now.strftime("%Y"),
        "{{MM}}": now.strftime("%m"),
        "{{DD}}": now.strftime("%d"),
        "{{hh}}": now.strftime("%H"),
        "{{mm}}": now.strftime("%M"),
        "{{ss}}": now.strftime("%S"),
    }
    for k, v in repl.items():
        fmt = fmt.replace(k, v)
    return fmt


def repo_owner_repo_from_remote(url: str):
    if url.startswith("git@github.com:"):
        path = url.split(":", 1)[1]
    else:
        u = urlparse(url)
        if "github.com" not in (u.netloc or ""):
            return None, None
        path = u.path.lstrip("/")
    path = path[:-4] if path.endswith(".git") else path
    try:
        owner, repo = path.split("/", 1)
        return owner, repo
    except ValueError:
        return None, None


def github_api(url, token, method="GET", payload=None, timeout=8):
    req = urllib.request.Request(url, method=method)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "Heimdall-Autopilot")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    data = None
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        req.add_header("Content-Type", "application/json")
        data = body
    with urllib.request.urlopen(req, data=data, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def main():
    C = cfg()
    a = C.get("autopr") or {}
    status_file = ROOT / a.get("status_file", "dist/docs/auto_pr_status.json")

    respect = bool(a.get("respect_global_dry_run", True))
    global_dry = bool(C.get("dry_run", False))
    do_write = not (respect and global_dry)

    allowed = a.get("allowed_paths") or []
    if not allowed:
        print("No allowed_paths configured; nothing to add.")
        return 0

    ensure_safe_dir()

    author_name = os.getenv("GIT_AUTHOR_NAME", "Heimdall Bot")
    author_email = os.getenv("GIT_AUTHOR_EMAIL", "heimdall@example.com")
    try:
        git("config", "user.name", author_name)
        git("config", "user.email", author_email)
    except Exception:
        pass

    try:
        git("rev-parse", "--is-inside-work-tree")
    except Exception as e:
        print("Not a git repo?", e)
        return 0

    staged = []
    for pat in allowed:
        matches = [p for p in glob.glob(pat, recursive=True) if pathlib.Path(p).is_file()]
        if matches:
            try:
                git("add", "--", *matches, check=True)
                staged.extend(matches)
            except Exception:
                try:
                    git("add", pat, check=True)
                    staged.append(pat)
                except Exception:
                    pass

    diff_cached = git("diff", "--cached", "--name-only", check=False)
    changed = [ln.strip() for ln in (diff_cached.stdout or "").splitlines() if ln.strip()]
    if not changed:
        status_file.parent.mkdir(parents=True, exist_ok=True)
        status = {
            "ok": True,
            "action": "noop",
            "reason": "no changes in allowed_paths",
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "dry_run": global_dry,
            "write_enabled": do_write,
        }
        status_file.write_text(json.dumps(status, indent=2), encoding="utf-8")
        print("No changes; nothing to commit.")
        return 0

    branch_prefix = a.get("branch_prefix", "heimdall/autopilot/")
    bn = branch_prefix + datetime.now().strftime("%Y%m%d-%H%M")
    commit_msg = stamp(a.get("commit_message", "Heimdall autopilot update"))

    status = {
        "ok": True,
        "dry_run": global_dry,
        "write_enabled": do_write,
        "branch": bn,
        "commit": None,
        "pushed": False,
        "pr_url": None,
        "pr_number": None,
        "changes": changed,
        "timestamp": datetime.now().isoformat(timespec="seconds"),
    }

    if not do_write:
        status["action"] = "preview_only"
        status_file.parent.mkdir(parents=True, exist_ok=True)
        status_file.write_text(json.dumps(status, indent=2), encoding="utf-8")
        print("Dry-run: preview only.")
        return 0

    base = a.get("main_branch", "main")
    remote_name = a.get("remote_name", "origin")
    try:
        git("fetch", remote_name, check=False)
    except Exception:
        pass
    git("checkout", "-B", bn)

    git("commit", "-m", commit_msg)
    status["commit"] = git("rev-parse", "HEAD").stdout.strip()

    push_ok = True
    try:
        git("push", "-u", remote_name, bn)
        status["pushed"] = True
    except Exception as e:
        push_ok = False
        status["pushed"] = False
        status["ok"] = False
        status["error"] = f"push failed: {e}"

    if push_ok and (a.get("pr", {}).get("create", True)):
        token = os.getenv("GITHUB_TOKEN")
        remote_url = os.getenv("GIT_REMOTE_URL")
        if not remote_url:
            remote_url = git("remote", "get-url", remote_name, check=False).stdout.strip()
        owner, repo = repo_owner_repo_from_remote(remote_url or "")
        if token and owner and repo:
            pr_title = stamp(a.get("pr", {}).get("title", "Heimdall autopilot"))
            pr_body = a.get("pr", {}).get("body", "")
            draft = bool(a.get("pr", {}).get("draft", True))
            try:
                api_base = f"https://api.github.com/repos/{owner}/{repo}"
                pr = github_api(
                    api_base + "/pulls",
                    token,
                    method="POST",
                    payload={
                        "title": pr_title,
                        "body": pr_body,
                        "head": bn,
                        "base": base,
                        "draft": draft,
                    },
                )
                status["pr_url"] = pr.get("html_url")
                status["pr_number"] = pr.get("number")
                labels = a.get("pr", {}).get("labels", [])
                if labels:
                    github_api(
                        api_base + f"/issues/{pr['number']}/labels",
                        token,
                        method="POST",
                        payload={"labels": labels},
                    )
            except Exception as e:
                status["ok"] = False
                status["error"] = f"PR create failed: {e}"
        else:
            status["note"] = "No GITHUB_TOKEN or non-GitHub remote; skipped PR."
    else:
        status["note"] = "Push failed or PR.create disabled; skipped PR."

    status_file.parent.mkdir(parents=True, exist_ok=True)
    status_file.write_text(json.dumps(status, indent=2), encoding="utf-8")
    print(json.dumps(status, indent=2))
    return 0 if status.get("ok", False) else 1


if __name__ == "__main__":
    raise SystemExit(main())
