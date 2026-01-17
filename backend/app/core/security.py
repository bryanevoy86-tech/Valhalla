from datetime import datetime, timedelta, timezone

from jose import jwt
from passlib.context import CryptContext

from ..core.config import get_settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_token(subject: str, minutes: int) -> str:
    s = get_settings()
    now = datetime.now(tz=timezone.utc)
    payload = {"sub": subject, "iat": now, "exp": now + timedelta(minutes=minutes)}
    return jwt.encode(payload, s.SECRET_KEY, algorithm="HS256")


def verify_password(plain, hashed):
    return pwd_context.verify(plain, hashed)


def hash_password(plain):
    return pwd_context.hash(plain)
