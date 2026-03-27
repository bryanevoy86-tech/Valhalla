import os

from backend.storage.base import StorageAdapter
from backend.storage.local import LocalStorage

try:
    from backend.storage.s3 import S3Storage
except Exception:
    S3Storage = None
try:
    from backend.storage.gcs import GCSStorage
except Exception:
    GCSStorage = None


def get_storage() -> StorageAdapter:
    backend = os.getenv("STORAGE_BACKEND", "local").lower()
    if backend == "s3" and S3Storage:
        return S3Storage()
    if backend == "gcs" and GCSStorage:
        return GCSStorage()
    return LocalStorage()
