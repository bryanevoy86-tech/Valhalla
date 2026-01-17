from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm


# ----------------------------
# Settings
# ----------------------------

@dataclass(frozen=True)
class AuthSettings:
    app_env: str
    enabled: bool
    jwt_secret: str
    owner_username: str
    owner_password_hash: Optional[str]
    owner_password_plain: Optional[str]
    token_ttl_seconds: int


def _truthy(v: Optional[str], default: bool = False) -> bool:
    if v is None:
        return default
    return v.strip().lower() in {"1", "true", "yes", "y", "on"}


def load_settings() -> AuthSettings:
    app_env = (os.getenv("APP_ENV") or os.getenv("ENV") or "dev").strip().lower()
    enabled = _truthy(os.getenv("VALHALLA_AUTH_ENABLED"), True)

    owner_username = (os.getenv("VALHALLA_OWNER_USERNAME") or "").strip()
    if enabled and not owner_username:
        raise RuntimeError("VALHALLA_OWNER_USERNAME must be set when auth is enabled")

    jwt_secret = (os.getenv("VALHALLA_JWT_SECRET") or "").strip()
    if enabled and app_env == "production" and not jwt_secret:
        raise RuntimeError("VALHALLA_JWT_SECRET must be set in production")
    if enabled and not jwt_secret:
        # dev/sandbox: generate ephemeral (prevents default-secret footguns)
        jwt_secret = secrets.token_urlsafe(48)

    owner_password_hash = os.getenv("VALHALLA_OWNER_PASSWORD_HASH")
    owner_password_plain = os.getenv("VALHALLA_OWNER_PASSWORD")

    if enabled and app_env == "production" and not owner_password_hash:
        raise RuntimeError("VALHALLA_OWNER_PASSWORD_HASH must be set in production")

    if enabled and not owner_password_hash and not owner_password_plain:
        raise RuntimeError(
            "Set VALHALLA_OWNER_PASSWORD_HASH (preferred) OR VALHALLA_OWNER_PASSWORD (dev/sandbox only)"
        )

    ttl = int(os.getenv("VALHALLA_TOKEN_TTL_SECONDS") or "3600")

    return AuthSettings(
        app_env=app_env,
        enabled=enabled,
        jwt_secret=jwt_secret,
        owner_username=owner_username,
        owner_password_hash=owner_password_hash,
        owner_password_plain=owner_password_plain,
        token_ttl_seconds=ttl,
    )


SETTINGS = load_settings()


# ----------------------------
# Password hashing (PBKDF2-SHA256)
# ----------------------------

def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(data: str) -> bytes:
    pad = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode((data + pad).encode("ascii"))


def pbkdf2_hash_password(password: str, *, iterations: int = 210_000) -> str:
    salt = secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations, dklen=32)
    return f"pbkdf2_sha256${iterations}${_b64url(salt)}${_b64url(dk)}"


def pbkdf2_verify(password: str, encoded: str) -> bool:
    try:
        algo, iters_s, salt_b64, dk_b64 = encoded.split("$", 3)
        if algo != "pbkdf2_sha256":
            return False
        iterations = int(iters_s)
        salt = _b64url_decode(salt_b64)
        expected = _b64url_decode(dk_b64)
        actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations, dklen=len(expected))
        return hmac.compare_digest(actual, expected)
    except Exception:
        return False


def verify_owner_password(password: str) -> bool:
    if SETTINGS.owner_password_hash:
        return pbkdf2_verify(password, SETTINGS.owner_password_hash)

    # plaintext allowed only outside production
    if SETTINGS.app_env == "production":
        return False

    return bool(SETTINGS.owner_password_plain) and hmac.compare_digest(password, SETTINGS.owner_password_plain)


# ----------------------------
# Minimal JWT HS256
# ----------------------------

def _jwt_sign(message: bytes, secret: str) -> str:
    sig = hmac.new(secret.encode("utf-8"), message, hashlib.sha256).digest()
    return _b64url(sig)


def jwt_encode(payload: Dict[str, Any], secret: str) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    h = _b64url(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    p = _b64url(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    msg = f"{h}.{p}".encode("ascii")
    s = _jwt_sign(msg, secret)
    return f"{h}.{p}.{s}"


def jwt_decode(token: str, secret: str) -> Dict[str, Any]:
    try:
        h_b64, p_b64, s_b64 = token.split(".")
        msg = f"{h_b64}.{p_b64}".encode("ascii")
        expected = _jwt_sign(msg, secret)
        if not hmac.compare_digest(expected, s_b64):
            raise ValueError("bad signature")
        payload = json.loads(_b64url_decode(p_b64))
        exp = int(payload.get("exp", 0))
        if exp and int(time.time()) > exp:
            raise ValueError("expired")
        return payload
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e


# ----------------------------
# FastAPI dependency + router
# ----------------------------

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/ops/token")
router = APIRouter(prefix="/ops", tags=["ops"])


def require_owner(token: str = Depends(oauth2_scheme)) -> Dict[str, Any]:
    if not SETTINGS.enabled:
        raise HTTPException(status_code=503, detail="Auth disabled")
    payload = jwt_decode(token, SETTINGS.jwt_secret)
    if payload.get("sub") != SETTINGS.owner_username:
        raise HTTPException(status_code=403, detail="Forbidden")
    return payload


@router.post("/token")
def issue_token(form: OAuth2PasswordRequestForm = Depends()) -> Dict[str, Any]:
    if not SETTINGS.enabled:
        raise HTTPException(status_code=503, detail="Auth disabled")

    if form.username != SETTINGS.owner_username or not verify_owner_password(form.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    now = int(time.time())
    payload = {"sub": SETTINGS.owner_username, "iat": now, "exp": now + SETTINGS.token_ttl_seconds}
    token = jwt_encode(payload, SETTINGS.jwt_secret)
    return {"access_token": token, "token_type": "bearer", "expires_in": SETTINGS.token_ttl_seconds}


@router.get("/me")
def whoami(_: Dict[str, Any] = Depends(require_owner)) -> Dict[str, Any]:
    return {"ok": True, "user": SETTINGS.owner_username}
