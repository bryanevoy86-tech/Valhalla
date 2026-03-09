from __future__ import annotations


class UploadSpec(dict):
    """
    Standardized upload spec returned to the client:
    {
      "backend": "local"|"s3"|"gcs",
      "method": "POST"|"PUT",
      "url": "https://...",
      "fields": {k:v},       # for POST form fields (S3)
      "headers": {k:v},      # optional headers (GCS PUT)
      "key": "uploads/org_123/foo.png",
      "expires_in": 3600
    }
    """

    pass


class StorageAdapter:
    backend_name: str = "base"

    async def generate_download_url(self, key: str, expires_in: int = 3600) -> str:
        raise NotImplementedError

    async def generate_upload_url(
        self, key: str, content_type: str, expires_in: int = 3600
    ) -> UploadSpec:
        raise NotImplementedError

    async def exists(self, key: str) -> bool:
        raise NotImplementedError

    async def delete(self, key: str) -> None:
        raise NotImplementedError

    # Local only convenience:
    async def save_bytes(self, key: str, data: bytes, content_type: str) -> str:
        raise NotImplementedError
