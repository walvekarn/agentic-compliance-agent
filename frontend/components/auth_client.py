import os
import socket
import requests
from typing import Optional, Tuple
from contextlib import suppress
 
# Prefer Streamlit secrets for BACKEND_URL/API_BASE_URL if available (no hard dependency at import time)
_secrets_backend = None
with suppress(Exception):
    import streamlit as st  # type: ignore
    _secrets_backend = (
        (st.secrets.get("BACKEND_URL") or st.secrets.get("API_BASE_URL"))
        if hasattr(st, "secrets") else None
    )

def _detect_lan_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

# Load environment variables with python-dotenv
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not required, use os.getenv only

# Resolve API base URL in order of preference:
# 1) Streamlit secrets BACKEND_URL or API_BASE_URL
# 2) Environment variables BACKEND_URL or API_BASE_URL (loaded from .env)
# 3) Default to localhost:8000
_env_backend = os.getenv("BACKEND_URL") or os.getenv("API_BASE_URL")
_raw_backend = _secrets_backend or _env_backend
# Default to localhost if nothing configured
API_BASE_URL = (_raw_backend.rstrip("/") if _raw_backend and str(_raw_backend).strip()
                else "http://localhost:8000")


def login(username: str, password: str, timeout: int = 10) -> Tuple[bool, Optional[str], Optional[str], Optional[str]]:
    """
    Call backend /auth/login (OAuth2 password form).
    Returns (success, access_token, refresh_token, error_message)
    """
    try:
        resp = requests.post(
            f"{API_BASE_URL}/auth/login",
            data={"username": username, "password": password},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=timeout,
        )
        if resp.status_code == 200:
            data = resp.json()
            return True, data.get("access_token"), data.get("refresh_token"), None
        return False, None, None, f"Login failed (status {resp.status_code})"
    except requests.RequestException as e:
        return False, None, None, str(e)


def refresh(refresh_token: str, timeout: int = 10) -> Tuple[bool, Optional[str], Optional[str], Optional[str]]:
    """
    Call backend /auth/refresh with JSON {"refresh_token": refresh_token}.
    Returns (success, access_token, new_refresh_token, error_message)
    """
    try:
        resp = requests.post(
            f"{API_BASE_URL}/auth/refresh",
            json={"refresh_token": refresh_token},
            timeout=timeout,
        )
        if resp.status_code == 200:
            data = resp.json()
            return True, data.get("access_token"), data.get("refresh_token"), None
        return False, None, None, f"Refresh failed (status {resp.status_code})"
    except requests.RequestException as e:
        return False, None, None, str(e)


def validate_token(access_token: str, timeout: int = 8) -> bool:
    """
    Validate access token by calling protected /auth/me.
    Returns True if token is valid, False otherwise.
    """
    if not access_token:
        return False
    try:
        resp = requests.get(
            f"{API_BASE_URL}/auth/me",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=timeout,
        )
        return resp.status_code == 200
    except requests.RequestException:
        return False


