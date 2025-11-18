"""Password hashing and verification utilities using bcrypt."""

from passlib.context import CryptContext


# Configure passlib context once
password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    """
    Hash a plaintext password using bcrypt.
    """
    if not isinstance(plain_password, str) or plain_password == "":
        raise ValueError("Password must be a non-empty string")
    return password_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plaintext password against its bcrypt hash.
    """
    if not plain_password or not hashed_password:
        return False
    return password_context.verify(plain_password, hashed_password)


