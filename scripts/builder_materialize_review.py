#!/usr/bin/env python3
"""Materialize a verified Builder review bundle into a NEW artifact directory.

This does not edit a checkout, execute generated code, run its tests, commit,
push, or deploy. A later isolated runner must apply the exact artifact to a
clean checkout and test it with no production credentials.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import runpy
import shutil
import tempfile
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
POLICY = runpy.run_path(str(ROOT / "services/api/app/core/builder_path_policy.py"))
resolve_path = POLICY["resolve_builder_path"]
DEFAULT_ALLOWED_DIRS = (
    "services/api/app/routers", "services/api/app/models",
    "services/api/app/schemas", "services/api/jobs",
    "services/api/alembic/versions", "web/weweb-datasources",
    "web/weweb-widgets",
)
MAX_FILES = 25
MAX_FILE_BYTES = 200_000
MAX_BATCH_BYTES = 1_000_000
MAX_ENVELOPE_BYTES = 2_100_000


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical(data: Any) -> bytes:
    return json.dumps(data, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":")).encode("utf-8")


def materialize(review: dict, base_root: Path, output_parent: Path,
                allowed_dirs: tuple[str, ...] = DEFAULT_ALLOWED_DIRS) -> Path:
    base_root = base_root.resolve(strict=True)
    output_parent = output_parent.resolve(strict=True)
    if not base_root.is_dir() or not output_parent.is_dir():
        raise ValueError("base and output parent must be directories")
    if output_parent.is_relative_to(base_root):
        raise ValueError("output must be outside the base checkout")
    if not isinstance(review, dict) or review.get("status") != "review_ready":
        raise ValueError("Builder review-ready evidence required")
    if any(review.get(flag) is not False for flag in ("source_modified", "tests_verified", "deployed")):
        raise ValueError("unexpected Builder review claims")
    if len(canonical(review)) > MAX_ENVELOPE_BYTES:
        raise ValueError("review envelope too large")
    bundle = review.get("bundle")
    if (not isinstance(bundle, dict) or set(bundle) != {"version", "task_id", "files"}
            or bundle["version"] != 2 or type(bundle["task_id"]) is not int
            or bundle["task_id"] <= 0 or sha(canonical(bundle)) != review.get("sha256")):
        raise ValueError("invalid Builder bundle identity")
    rows = bundle["files"]
    if not isinstance(rows, list) or not 1 <= len(rows) <= MAX_FILES:
        raise ValueError("invalid Builder file count")

    prepared, seen, total = [], set(), 0
    for row in rows:
        if not isinstance(row, dict) or set(row) != {
            "path", "content", "mode", "base_sha256", "content_sha256"
        }:
            raise ValueError("malformed Builder file record")
        path = row["path"]
        target = resolve_path(path, list(allowed_dirs), base_root)
        if target.relative_to(base_root).as_posix() != path or target in seen:
            raise ValueError("noncanonical or duplicate Builder target")
        seen.add(target)
        if not isinstance(row["content"], str):
            raise ValueError("Builder content must be UTF-8 text")
        data = row["content"].encode("utf-8")
        total += len(data)
        if len(data) > MAX_FILE_BYTES or total > MAX_BATCH_BYTES:
            raise ValueError("Builder output exceeds byte limit")
        if sha(data) != row["content_sha256"]:
            raise ValueError("Builder output checksum mismatch")
        if row["mode"] == "add":
            if target.exists() or row["base_sha256"] is not None:
                raise ValueError("add base has changed")
        elif row["mode"] == "replace":
            if not target.is_file() or target.stat().st_size > MAX_FILE_BYTES:
                raise ValueError("replace base missing or oversized")
            old = target.read_bytes()
            if len(old) > MAX_FILE_BYTES or sha(old) != row["base_sha256"]:
                raise ValueError("replace base checksum changed")
            if old == data:
                raise ValueError("replacement does not change source")
        else:
            raise ValueError("unsupported Builder mode")
        validation = "bytes_only"
        if target.suffix == ".py":
            # Compile in memory; do NOT import, execute, or run proposed code.
            compile(data, path, "exec", dont_inherit=True)
            validation = "python_syntax_only"
        elif target.suffix == ".json":
            json.loads(data.decode("utf-8"))
            validation = "json_syntax_only"
        prepared.append((row, data, validation))

    # No output exists until the entire batch has passed verification.
    output = Path(tempfile.mkdtemp(prefix="builder-review-", dir=output_parent))
    try:
        proof = []
        for row, data, validation in prepared:
            artifact = output / "files" / row["path"]
            artifact.parent.mkdir(parents=True, exist_ok=True)
            with artifact.open("xb") as handle:
                handle.write(data)
            if sha(artifact.read_bytes()) != row["content_sha256"]:
                raise ValueError("materialized artifact failed read-back")
            proof.append({"path": row["path"], "mode": row["mode"],
                          "base_sha256": row["base_sha256"],
                          "content_sha256": row["content_sha256"],
                          "validation": validation})
        receipt = {
            "status": "artifact_materialized", "task_id": bundle["task_id"],
            "bundle_sha256": review["sha256"], "files": proof,
            "source_modified": False, "tests_verified": False,
            "code_executed": False, "committed": False, "deployed": False,
        }
        (output / "receipt.json").write_bytes(canonical(receipt))
        return output
    except BaseException:
        # Only our newly created, private artifact directory is removed.
        shutil.rmtree(output)
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--review", required=True, type=Path)
    parser.add_argument("--base-root", required=True, type=Path)
    parser.add_argument("--output-parent", required=True, type=Path)
    args = parser.parse_args()
    try:
        if args.review.stat().st_size > MAX_ENVELOPE_BYTES:
            raise ValueError("review envelope too large")
        raw = args.review.read_bytes()
        if len(raw) > MAX_ENVELOPE_BYTES:
            raise ValueError("review envelope too large")
        output = materialize(json.loads(raw), args.base_root, args.output_parent)
    except (OSError, ValueError, TypeError, SyntaxError) as exc:
        # Do not print generated code or potentially sensitive file contents.
        parser.exit(2, f"Builder materialization refused: {type(exc).__name__}\n")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
