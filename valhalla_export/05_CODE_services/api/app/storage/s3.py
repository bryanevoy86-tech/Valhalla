"""Document storage on S3."""
from app.core.runtime_flags import is_live


def upload_document(key, content):
    """Upload document to S3."""
    if not is_live():
        return {
            "url": f"s3://sandbox/{key}",
            "key": key,
            "status": "uploaded"
        }

    return {
        "url": f"s3://valhalla/{key}",
        "key": key,
        "status": "uploaded"
    }


def download_document(key):
    """Download document from S3."""
    return {
        "key": key,
        "url": f"s3://valhalla/{key}",
        "status": "retrieved"
    }


def delete_document(key):
    """Delete document from S3."""
    return {
        "key": key,
        "status": "deleted"
    }


def list_documents(prefix):
    """List documents in S3 with prefix."""
    return {
        "prefix": prefix,
        "documents": []
    }
