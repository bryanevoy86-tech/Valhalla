import base64
import hashlib
import hmac
import os
import time
from urllib.parse import urlencode

SECRET_KEY = os.getenv("SIGNED_URL_SECRET", "supersecret")


def generate_signed_url(file_path: str, expires_in: int = 3600) -> str:
    """
    Generates a signed URL for secure file download.
    """
    expiry = int(time.time()) + expires_in
    payload = f"{file_path}:{expiry}"
    signature = hmac.new(SECRET_KEY.encode(), payload.encode(), hashlib.sha256).digest()
    token = base64.urlsafe_b64encode(signature).decode()
    query = urlencode({"expiry": expiry, "token": token})
    return f"/api/files/download?path={file_path}&{query}"


def verify_signed_url(file_path: str, expiry: int, token: str) -> bool:
    """
    Verifies a signed URL before allowing download.
    """
    if time.time() > expiry:
        return False
    payload = f"{file_path}:{expiry}"
    expected_signature = hmac.new(SECRET_KEY.encode(), payload.encode(), hashlib.sha256).digest()
    expected_token = base64.urlsafe_b64encode(expected_signature).decode()
    return hmac.compare_digest(expected_token, token)
