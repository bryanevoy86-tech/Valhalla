from __future__ import annotations

import json
import os

from backend.storage.base import StorageAdapter, UploadSpec
from google.cloud import storage
from google.oauth2 import service_account

GCS_BUCKET = os.getenv("STORAGE_GCS_BUCKET")
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")
SA_PATH = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
SA_JSON = os.getenv("GCP_SERVICE_ACCOUNT_JSON")


def _client():
    if SA_JSON:
        creds = service_account.Credentials.from_service_account_info(json.loads(SA_JSON))
        return storage.Client(project=GCP_PROJECT_ID, credentials=creds)
    if SA_PATH:
        return storage.Client(project=GCP_PROJECT_ID)
    return storage.Client()  # use default creds if running on GCP


class GCSStorage(StorageAdapter):
    backend_name = "gcs"

    async def generate_download_url(self, key: str, expires_in: int = 3600) -> str:
        client = _client()
        bucket = client.bucket(GCS_BUCKET)
        blob = bucket.blob(key)
        return blob.generate_signed_url(expiration=expires_in, method="GET")

    async def generate_upload_url(
        self, key: str, content_type: str, expires_in: int = 3600
    ) -> UploadSpec:
        client = _client()
        bucket = client.bucket(GCS_BUCKET)
        blob = bucket.blob(key)
        url = blob.generate_signed_url(
            version="v4",
            expiration=expires_in,
            method="PUT",
            content_type=content_type,
        )
        return UploadSpec(
            backend="gcs",
            method="PUT",
            url=url,
            fields={},
            headers={"Content-Type": content_type},
            key=key,
            expires_in=expires_in,
        )

    async def exists(self, key: str) -> bool:
        client = _client()
        bucket = client.bucket(GCS_BUCKET)
        return bucket.blob(key).exists()

    async def delete(self, key: str) -> None:
        client = _client()
        bucket = client.bucket(GCS_BUCKET)
        bucket.blob(key).delete()
