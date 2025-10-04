import boto3
from app.core.settings import settings

class S3Storage:
    def __init__(self):
        self.client = boto3.client(
            "s3",
            aws_access_key_id=settings.s3_access_key_id,
            aws_secret_access_key=settings.s3_secret_access_key,
            region_name=settings.s3_region,
        )
        self.bucket = settings.s3_bucket

    def upload_file(self, file_path, key):
        self.client.upload_file(file_path, self.bucket, key)
        return f"s3://{self.bucket}/{key}"

    def upload_bytes(self, data, key):
        self.client.put_object(Bucket=self.bucket, Key=key, Body=data)
        return f"s3://{self.bucket}/{key}"
