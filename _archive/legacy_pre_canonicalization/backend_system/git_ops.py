import os
import time
from pathlib import Path

try:
    from git import Actor, Repo  # type: ignore

    HAS_GIT = True
except Exception:
    HAS_GIT = False


def auto_commit(add_paths, branch_prefix="heimdall/", message="Heimdall generated changes"):
    """
    Adds and commits changes on a new branch. Returns (ok, msg_or_branch).
    """
    if not HAS_GIT:
        return False, "GitPython not available"

    repo = Repo(Path("."))
    for p in add_paths:
        # add path only if it exists to avoid errors
        if Path(p).exists():
            repo.git.add(p)

    if not repo.is_dirty():
        return False, "nothing to commit"

    branch = f"{branch_prefix}{int(time.time())}"
    repo.git.checkout("-B", branch)
    actor = Actor(
        os.getenv("GIT_AUTHOR_NAME", "Heimdall"), os.getenv("GIT_AUTHOR_EMAIL", "heimdall@local")
    )
    repo.index.commit(message, author=actor, committer=actor)
    return True, branch
