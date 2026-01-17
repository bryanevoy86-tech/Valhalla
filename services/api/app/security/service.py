from datetime import datetime, timedelta
from typing import Optional

try:  # Allow running without pyotp installed (dev/test); real deploy will have it
    import pyotp  # type: ignore
except Exception:  # pragma: no cover - fallback stub
    class _PyOtpStub:
        @staticmethod
        def random_base32() -> str:
            return "BASE32DUMMYSECRET"

    pyotp = _PyOtpStub()  # type: ignore

from cryptography.fernet import Fernet
from sqlalchemy.orm import Session

from .schemas import TwoFactorAuthOut, RateLimitOut, EncryptedData
from sqlalchemy.orm import Session

from .schemas import TwoFactorAuthOut, RateLimitOut


class SecurityService:
    def __init__(self, db: Session):
        self.db = db

    def generate_2fa_token(self, user_id: str) -> TwoFactorAuthOut:
        # Generate a random base32 secret; in a real system you'd store this per-user
        _secret = pyotp.random_base32()
        # Example: create a TOTP for display/verification flows if needed
        # totp = pyotp.TOTP(_secret)
        expiry = datetime.utcnow() + timedelta(minutes=10)
        # Persisting the secret/token association is omitted in this pack (placeholder)
        return TwoFactorAuthOut(
            user_id=user_id,
            verified=False,
            token_expiry=expiry.isoformat(),
        )

    def verify_2fa_token(self, user_id: str, token: str) -> TwoFactorAuthOut:
        # Placeholder verification: always returns True in this pack
        # In a real implementation, fetch user's secret and verify with pyotp.TOTP(secret).verify(token)
        is_valid = True
        return TwoFactorAuthOut(
            user_id=user_id,
            verified=is_valid,
            token_expiry=(datetime.utcnow() + timedelta(minutes=10)).isoformat(),
        )

    def check_rate_limit(self, user_id: str) -> RateLimitOut:
        # Placeholder: static number to demonstrate the shape; replace with real counters
        request_count = 5
        reset_time = datetime.utcnow() + timedelta(minutes=1)
        return RateLimitOut(
            request_count=request_count,
            reset_time=reset_time.isoformat(),
        )


class EncryptionService:
    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def generate_encryption_key() -> str:
        return Fernet.generate_key().decode()

    def encrypt_data(self, data: str, key: str) -> EncryptedData:
        f = Fernet(key)
        encrypted_data = f.encrypt(data.encode()).decode()
        return EncryptedData(
            data=encrypted_data,
            encrypted=True,
            encryption_key=key,
        )

    def decrypt_data(self, encrypted_data: str, key: str) -> str:
        f = Fernet(key)
        decrypted_data = f.decrypt(encrypted_data.encode()).decode()
        return decrypted_data
