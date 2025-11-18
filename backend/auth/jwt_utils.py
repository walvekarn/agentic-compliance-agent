"""JWT creation and verification utilities."""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from jose import jwt, JWTError
import os


ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7


def _get_secret_key() -> str:
    secret = os.getenv("SECRET_KEY")
    if not secret or len(secret) < 32:
        raise RuntimeError("SECRET_KEY is missing or too short (>=32 chars required)")
    return secret


def create_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta],
) -> str:
    """
    Create a JWT token with given payload and expiry.
    """
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    if expires_delta is None:
        raise ValueError("expires_delta must be provided")
    expire = now + expires_delta
    to_encode.update({"iat": int(now.timestamp()), "exp": int(expire.timestamp())})
    encoded_jwt = jwt.encode(to_encode, _get_secret_key(), algorithm=ALGORITHM)
    return encoded_jwt


def create_access_token(subject: str, extra_claims: Optional[Dict[str, Any]] = None) -> str:
    """
    Create a short-lived access token for the given subject (user id).
    """
    claims = {"sub": subject, "type": "access"}
    if extra_claims:
        claims.update(extra_claims)
    return create_token(claims, timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))


def create_refresh_token(subject: str, extra_claims: Optional[Dict[str, Any]] = None) -> str:
    """
    Create a long-lived refresh token for the given subject (user id).
    """
    claims = {"sub": subject, "type": "refresh"}
    if extra_claims:
        claims.update(extra_claims)
    return create_token(claims, timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS))


def decode_token(token: str) -> Dict[str, Any]:
    """
    Decode and validate a JWT token.
    """
    try:
        payload = jwt.decode(token, _get_secret_key(), algorithms=[ALGORITHM])
        return payload
    except JWTError as exc:
        raise ValueError("Invalid or expired token") from exc


