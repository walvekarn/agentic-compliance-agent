"""JWT Authentication router"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from src.db.base import get_db
from .user_manager import ensure_admin_user, authenticate_user
from .security import create_access_token, create_refresh_token, decode_token, get_current_user
from .models import User
from pydantic import BaseModel
from src.api.rate_limit import limiter, PUBLIC_RATE


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class UserResponse(BaseModel):
    id: int
    username: str
    is_active: bool

    class Config:
        from_attributes = True


router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login", response_model=TokenResponse)
@limiter.limit(PUBLIC_RATE)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    ensure_admin_user(db)
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    access_token = create_access_token(user.username, {"username": user.username})
    refresh_token = create_refresh_token(user.username, {"username": user.username})
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_tokens(
    req: RefreshRequest,
):
    payload = decode_token(req.refresh_token)
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")
    username = payload.get("username") or payload.get("sub")
    if not username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
    access_token = create_access_token(username, {"username": username})
    new_refresh = create_refresh_token(username, {"username": username})
    return TokenResponse(access_token=access_token, refresh_token=new_refresh)


@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)):
    return current_user

