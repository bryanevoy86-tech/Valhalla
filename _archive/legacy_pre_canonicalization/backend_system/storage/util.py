import re
from pathlib import PurePosixPath

SAFE_NAME = re.compile(r"[^A-Za-z0-9._-]+")


def sanitize_filename(name: str) -> str:
    name = name.strip().replace(" ", "_")
    return SAFE_NAME.sub("", name)


def build_key(base_prefix: str, org_id: str | int, filename: str) -> str:
    filename = sanitize_filename(filename)
    return str(PurePosixPath(base_prefix) / f"org_{org_id}" / filename)
