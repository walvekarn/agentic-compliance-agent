import os
import socket
import requests
from typing import Optional, Tuple

def _detect_lan_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

_env_backend = os.getenv("BACKEND_URL") or os.getenv("API_BASE_URL")
API_BASE_URL = (_env_backend.rstrip("/") if _env_backend and _env_backend.strip()
                else f"http://{_detect_lan_ip()}:8000")


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


