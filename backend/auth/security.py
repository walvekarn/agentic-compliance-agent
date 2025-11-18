import os
import hmac
import hashlib
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any

import jwt
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from backend.config import settings
from backend.db.base import get_db
from .auth_models import User

logger = logging.getLogger(__name__)


def _jwt_secret() -> str:
    return settings.JWT_SECRET or settings.SECRET_KEY


def hash_password(password: str, salt: Optional[str] = None) -> str:
    salt = salt or os.getenv("PASSWORD_SALT", "static_salt_v1")
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100_000)
    return dk.hex()


def verify_password(password: str, password_hash: str) -> bool:
    return hmac.compare_digest(hash_password(password), password_hash)


def _create_token(subject: str, expires_delta: timedelta, token_type: str = "access", extra: Optional[Dict[str, Any]] = None) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "type": token_type,
        "iat": int(now.timestamp()),
        "exp": int((now + expires_delta).timestamp()),
    }
    if extra:
        payload.update(extra)
    token = jwt.encode(payload, _jwt_secret(), algorithm=settings.JWT_ALGORITHM)
    return token


def create_access_token(subject: str, extra: Optional[Dict[str, Any]] = None) -> str:
    minutes = int(settings.ACCESS_TOKEN_EXPIRE_MINUTES or 30)
    return _create_token(subject, timedelta(minutes=minutes), "access", extra)


def create_refresh_token(subject: str, extra: Optional[Dict[str, Any]] = None) -> str:
    days = int(settings.REFRESH_TOKEN_EXPIRE_DAYS or 7)
    return _create_token(subject, timedelta(days=days), "refresh", extra)


def decode_token(token: str) -> Dict[str, Any]:
    try:
        payload = jwt.decode(token, _jwt_secret(), algorithms=[settings.JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("Token expired", extra={"token_preview": token[:20] + "..." if len(token) > 20 else token})
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid token: {str(e)}", extra={"token_preview": token[:20] + "..." if len(token) > 20 else token})
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> User:
    if not credentials or credentials.scheme.lower() != "bearer":
        logger.warning(f"Authentication failed: No credentials or invalid scheme", extra={
            "path": request.url.path,
            "method": request.method
        })
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    
    try:
        payload = decode_token(credentials.credentials)
    except HTTPException as e:
        logger.warning(f"Token decode failed: {e.detail}", extra={
            "path": request.url.path,
            "method": request.method
        })
        raise
    
    if payload.get("type") != "access":
        logger.warning(f"Invalid token type: {payload.get('type')}", extra={
            "path": request.url.path,
            "method": request.method,
            "username": payload.get("username") or payload.get("sub")
        })
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid access token")
    
    username = payload.get("username") or payload.get("sub")
    if not username:
        logger.warning("Token missing username/sub", extra={
            "path": request.url.path,
            "method": request.method
        })
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
    
    user: Optional[User] = db.query(User).filter(User.username == username).first()
    if not user or not user.is_active:
        logger.warning(f"User not found or inactive: {username}", extra={
            "path": request.url.path,
            "method": request.method,
            "user_exists": user is not None,
            "is_active": user.is_active if user else False
        })
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User inactive or not found")
    
    logger.debug(f"Authenticated user: {username}", extra={
        "path": request.url.path,
        "method": request.method,
        "user_id": user.id
    })
    return user


