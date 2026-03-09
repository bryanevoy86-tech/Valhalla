"""S3-compatible contract document storage.

Supports AWS S3, Cloudflare R2, Wasabi, and Backblaze B2.
All documents are immutable blobs addressed by storage_key.
"""
from __future__ import annotations

import os
import hashlib
from dataclasses import dataclass
from typing import Optional

import boto3
from botocore.exceptions import ClientError


@dataclass(frozen=True)
class StoredObject:
    """Result of storing a document in S3."""
    storage_key: str
    sha256: str
    size_bytes: int


def _sha256(data: bytes) -> str:
    """Compute SHA256 hash of data."""
    return hashlib.sha256(data).hexdigest()


class S3ContractStorage:
    """
    S3-compatible contract storage (AWS S3 / Cloudflare R2 / Wasabi / B2 S3).
    Stores immutable blobs addressed by storage_key.
    """

    def __init__(self):
        self.bucket = os.getenv("CONTRACT_S3_BUCKET")
        if not self.bucket:
            raise RuntimeError("CONTRACT_S3_BUCKET is required")

        self.prefix = os.getenv("CONTRACT_S3_PREFIX", "").strip().strip("/")
        self.region = os.getenv("AWS_REGION", "us-east-1")
        self.endpoint_url = os.getenv("AWS_ENDPOINT_URL")  # needed for R2/Wasabi/B2

        self.sse = os.getenv("CONTRACT_S3_SSE")  # e.g. AES256
        self.kms_key_id = os.getenv("CONTRACT_S3_KMS_KEY_ID")

        self.client = boto3.client(
            "s3",
            region_name=self.region,
            endpoint_url=self.endpoint_url if self.endpoint_url else None,
        )

    def _key(self, contract_id: str, sha: str, filename: str) -> str:
        """Compute S3 object key from contract_id, hash, and filename."""
        safe = filename.replace("\\", "_").replace("/", "_")
        core = f"{contract_id}/{sha}_{safe}"
        return f"{self.prefix}/{core}" if self.prefix else core

    def put_bytes(self, contract_id: str, filename: str, data: bytes) -> StoredObject:
        """Upload document and return storage metadata."""
        sha = _sha256(data)
        key = self._key(contract_id, sha, filename)

        extra = {"ContentType": "application/pdf"}
        if self.kms_key_id:
            extra["ServerSideEncryption"] = "aws:kms"
            extra["SSEKMSKeyId"] = self.kms_key_id
        elif self.sse:
            extra["ServerSideEncryption"] = self.sse  # e.g. AES256

        self.client.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=data,
            **extra,
        )
        return StoredObject(storage_key=key, sha256=sha, size_bytes=len(data))

    def get_bytes(self, storage_key: str) -> bytes:
        """Download document from S3."""
        obj = self.client.get_object(Bucket=self.bucket, Key=storage_key)
        return obj["Body"].read()

    def exists(self, storage_key: str) -> bool:
        """Check if document exists in S3."""
        try:
            self.client.head_object(Bucket=self.bucket, Key=storage_key)
            return True
        except ClientError:
            return False

    def presign_get(self, storage_key: str, expires_seconds: int = 900) -> str:
        """Generate presigned URL for document download."""
        return self.client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket, "Key": storage_key},
            ExpiresIn=expires_seconds,
        )
