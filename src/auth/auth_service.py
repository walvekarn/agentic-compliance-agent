"""Authentication service and dependencies."""

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from src.db.base import get_db
from .auth_models import User
from .password_utils import verify_password, hash_password
from .jwt_utils import decode_token, create_access_token, create_refresh_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_user_by_username(db: Session, username: str) -> Optional[User]:
    return db.query(User).filter(User.username == username).first()


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    return db.query(User).filter(User.id == user_id).first()


def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    user = get_user_by_username(db, username)
    if not user or not user.is_active:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def create_user(db: Session, username: str, password: str, email: Optional[str]) -> User:
    if get_user_by_username(db, username):
        raise HTTPException(status_code=400, detail="Username already taken")
    hashed = hash_password(password)
    user = User(username=username, email=email, hashed_password=hashed, is_active=True)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def issue_tokens_for_user(user: User):
    subject = str(user.id)
    access = create_access_token(subject, {"username": user.username})
    refresh = create_refresh_token(subject, {"username": user.username})
    return access, refresh


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    Dependency that extracts and validates the access token and returns the user.
    """
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing token")
    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
        user = get_user_by_id(db, int(user_id))
        if user is None or not user.is_active:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")
        return user
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")


