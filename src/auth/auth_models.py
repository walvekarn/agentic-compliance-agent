"""Auth domain models and Pydantic schemas."""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, Integer, String, DateTime, Boolean
from pydantic import BaseModel, Field

from src.db.base import Base


class User(Base):
    """
    Minimal user model for authentication.
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(150), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)


# Pydantic Schemas
class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = Field(default=15 * 60, description="Access token TTL in seconds")


class LoginRequest(BaseModel):
    username: str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class SignupRequest(BaseModel):
    username: str
    password: str
    email: Optional[str] = None


class UserResponse(BaseModel):
    id: int
    username: str
    email: Optional[str] = None
    is_active: bool = True

    class Config:
        from_attributes = True


