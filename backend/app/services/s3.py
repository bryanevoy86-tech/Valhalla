from __future__ import annotations

import boto3
from botocore.config import Config as BotoConfig

from ..core.config import get_settings


def _client():
    s = get_settings()
    return boto3.client(
        "s3",
        endpoint_url=s.S3_ENDPOINT_URL,
        aws_access_key_id=s.S3_ACCESS_KEY,
        aws_secret_access_key=s.S3_SECRET_KEY,
        region_name=s.S3_REGION,
        config=BotoConfig(s3={"addressing_style": "path"} if s.S3_FORCE_PATH_STYLE else None),
    )


def presign_put(key: str, content_type: str | None = "application/octet-stream") -> str:
    s = get_settings()
    return _client().generate_presigned_url(
        "put_object",
        Params={"Bucket": s.S3_BUCKET, "Key": key, "ContentType": content_type},
        ExpiresIn=s.S3_PRESIGN_EXPIRE_SEC,
    )


def presign_get(key: str) -> str:
    s = get_settings()
    return _client().generate_presigned_url(
        "get_object",
        Params={"Bucket": s.S3_BUCKET, "Key": key},
        ExpiresIn=s.S3_PRESIGN_EXPIRE_SEC,
    )
