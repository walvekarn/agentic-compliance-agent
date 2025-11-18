from typing import Optional
from sqlalchemy.orm import Session

from .auth_models import User
from .security import hash_password


DEFAULT_ADMIN_USERNAME = "demo"
DEFAULT_ADMIN_PASSWORD = "demo123"


def ensure_admin_user(db: Session) -> User:
    user: Optional[User] = db.query(User).filter(User.username == DEFAULT_ADMIN_USERNAME).first()
    if user:
        return user
    user = User(
        username=DEFAULT_ADMIN_USERNAME,
        hashed_password=hash_password(DEFAULT_ADMIN_PASSWORD),
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    user: Optional[User] = db.query(User).filter(User.username == username).first()
    from .security import verify_password

    if not user or not verify_password(password, user.hashed_password):
        return None
    return user


