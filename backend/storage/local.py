from __future__ import annotations

from pathlib import Path

from backend.storage.base import StorageAdapter, UploadSpec
from backend.utils.signed_url import generate_signed_url

BASE_DIR = Path("exports").resolve()  # reuse export dir
UPLOAD_ROOT = BASE_DIR / "uploads"
UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)


class LocalStorage(StorageAdapter):
    backend_name = "local"

    async def generate_download_url(self, key: str, expires_in: int = 3600) -> str:
        # key is relative to exports/, so compose path for signed link
        rel = str(key)
        return generate_signed_url(rel, expires_in)

    async def generate_upload_url(
        self, key: str, content_type: str, expires_in: int = 3600
    ) -> UploadSpec:
        # local uploads go through the API (multipart POST)
        return UploadSpec(
            backend="local",
            method="POST",
            url="/api/files/upload",
            fields={"key": key, "content_type": content_type},
            headers={},
            key=key,
            expires_in=expires_in,
        )

    async def save_bytes(self, key: str, data: bytes, content_type: str) -> str:
        dest = (UPLOAD_ROOT / key).resolve()
        dest.parent.mkdir(parents=True, exist_ok=True)
        with open(dest, "wb") as f:
            f.write(data)
        # return a path usable by /api/files/download signed route
        return f"uploads/{key}"

    async def exists(self, key: str) -> bool:
        return (UPLOAD_ROOT / key).exists()

    async def delete(self, key: str) -> None:
        p = UPLOAD_ROOT / key
        if p.exists():
            p.unlink()
