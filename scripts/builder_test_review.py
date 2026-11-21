#!/usr/bin/env python3
"""Run a verified API review bundle against a committed suite in an offline container."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tarfile
import tempfile
import uuid

from builder_materialize_review import MAX_ENVELOPE_BYTES, materialize, sha


DOCKER = ["docker", "--host=unix:///var/run/docker.sock"]
SUITE = "services/api/tests"


def test_review(review: dict, repository: Path, commit: str, image_id: str, timeout: int) -> dict:
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ValueError("a full committed Git SHA is required")
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", image_id):
        raise ValueError("a preloaded, pinned Docker image ID is required")
    if not 15 <= timeout <= 600:
        raise ValueError("timeout outside supported limits")

    with tempfile.TemporaryDirectory(prefix="builder-test-") as temp:
        root = Path(temp)
        source = root / "checkout"
        source.mkdir()
        archive = root / "source.tar"
        with archive.open("wb") as stream:
            subprocess.run(
                ["git", "-C", str(repository), "archive", "--format=tar", commit, "--", "services/api", "pytest.ini"],
                check=True, stdout=stream, stderr=subprocess.DEVNULL, timeout=60,
            )
        with tarfile.open(archive, "r") as bundle:
            for entry in bundle:
                if any(part.startswith(".env") for part in Path(entry.name).parts):
                    continue
                bundle.extract(entry, source, filter="data")

        artifact = materialize(review, source, root)
        receipt = json.loads((artifact / "receipt.json").read_bytes())
        for entry in receipt["files"]:
            relative = Path(entry["path"])
            if relative.parts[:2] != ("services", "api"):
                raise ValueError("offline backend testing supports API review bundles")
            candidate = artifact / "files" / relative
            if sha(candidate.read_bytes()) != entry["content_sha256"]:
                raise ValueError("candidate artifact changed")
            target = source / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(candidate, target)

        name = "valhalla-builder-" + uuid.uuid4().hex
        settings = {
            "HOME": "/tmp", "PYTHONDONTWRITEBYTECODE": "1", "DATABASE_URL": "sqlite://", "VALHALLA_JWT_SECRET": "offline-builder-test-only",
            "VALHALLA_EMERGENCY_STOP": "true", "VALHALLA_OWNER_USERNAME": "isolated-ci-owner",
            "VALHALLA_OWNER_PASSWORD": "offline-builder-test-only", "ENV": "dev", "APP_ENV": "dev",
        }
        command = DOCKER + [
            "run", "--rm", "--name", name, "--pull=never", "--log-driver=none",
            "--network=none", "--read-only", "--user=65534:65534", "--cap-drop=ALL",
            "--security-opt=no-new-privileges", "--pids-limit=96", "--memory=768m",
            "--cpus=2", "--tmpfs=/tmp:rw,nosuid,nodev,size=256m",
            "--mount", f"type=bind,src={source},dst=/snapshot,readonly", "--workdir=/snapshot",
        ]
        for key, value in settings.items():
            command.extend(("--env", f"{key}={value}"))
        command += ["--entrypoint=python", image_id, "-m", "pytest", "-q", "-p", "no:cacheprovider", SUITE]
        docker_env = {"HOME": str(root), "PATH": os.defpath}
        try:
            result = subprocess.run(
                command, env=docker_env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=timeout,
            )
            exit_code = result.returncode
            status = "suite_exited_zero" if exit_code == 0 else "suite_exited_nonzero"
            if exit_code in (125, 126, 127) or exit_code < 0:
                status = "sandbox_unavailable"
        except subprocess.TimeoutExpired:
            status, exit_code = "sandbox_timeout", None
        except FileNotFoundError:
            status, exit_code = "sandbox_unavailable", None
        finally:
            if shutil.which("docker", path=os.defpath):
                subprocess.run(
                    DOCKER + ["rm", "--force", name], env=docker_env, stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL, timeout=15,
                )

    return {
        "status": status, "exit_code": exit_code, "suite": SUITE,
        "base_commit": commit, "image_id": image_id, "bundle_sha256": receipt["bundle_sha256"],
        "source_modified": False, "committed": False, "deployed": False, "release_authorized": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--review", required=True, type=Path)
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--image-id", required=True)
    parser.add_argument("--timeout", type=int, default=180)
    args = parser.parse_args()
    try:
        with args.review.open("rb") as stream:
            raw = stream.read(MAX_ENVELOPE_BYTES + 1)
        if len(raw) > MAX_ENVELOPE_BYTES:
            raise ValueError("review envelope too large")
        result = test_review(json.loads(raw), args.repository, args.commit, args.image_id, args.timeout)
    except (OSError, SyntaxError, ValueError, TypeError, subprocess.SubprocessError, tarfile.TarError) as exc:
        parser.exit(2, f"Builder test refused: {type(exc).__name__}\n")
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "suite_exited_zero" else 2


if __name__ == "__main__":
    raise SystemExit(main())
