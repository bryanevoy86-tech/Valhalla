from __future__ import annotations

import os

import aioboto3
from backend.storage.base import StorageAdapter, UploadSpec

AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
S3_BUCKET = os.getenv("STORAGE_S3_BUCKET")


class S3Storage(StorageAdapter):
    backend_name = "s3"

    async def generate_download_url(self, key: str, expires_in: int = 3600) -> str:
        session = aioboto3.Session()
        async with session.client("s3", region_name=AWS_REGION) as s3:
            return await s3.generate_presigned_url(
                "get_object",
                Params={"Bucket": S3_BUCKET, "Key": key},
                ExpiresIn=expires_in,
            )

    async def generate_upload_url(
        self, key: str, content_type: str, expires_in: int = 3600
    ) -> UploadSpec:
        session = aioboto3.Session()
        async with session.client("s3", region_name=AWS_REGION) as s3:
            presigned = await s3.generate_presigned_post(
                Bucket=S3_BUCKET,
                Key=key,
                Fields={"Content-Type": content_type},
                Conditions=[
                    {"Content-Type": content_type},
                    ["content-length-range", 1, 50 * 1024 * 1024],  # 50MB cap
                ],
                ExpiresIn=expires_in,
            )
            return UploadSpec(
                backend="s3",
                method="POST",
                url=presigned["url"],
                fields=presigned["fields"],
                headers={},
                key=key,
                expires_in=expires_in,
            )

    async def exists(self, key: str) -> bool:
        session = aioboto3.Session()
        async with session.client("s3", region_name=AWS_REGION) as s3:
            try:
                await s3.head_object(Bucket=S3_BUCKET, Key=key)
                return True
            except Exception:
                return False

    async def delete(self, key: str) -> None:
        session = aioboto3.Session()
        async with session.client("s3", region_name=AWS_REGION) as s3:
            await s3.delete_object(Bucket=S3_BUCKET, Key=key)
