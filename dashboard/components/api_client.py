"""
API Client
==========
Unified API client for Streamlit dashboard with:
- Auth header injection
- Auto-refresh on 401 (and logout on failure)
- Retry with exponential backoff
- Connection/timeout handling
- Structured APIResponse
"""

from typing import Dict, Any, Optional, Tuple, Union
import time
import requests
import streamlit as st
from .constants import API_BASE_URL, API_TIMEOUT
from .auth_utils import get_auth_headers, refresh_tokens_if_needed, logout


class APIResponse:
    """Standardized API response wrapper"""
    def __init__(
        self,
        success: bool,
        data: Optional[Union[Dict[str, Any], list]] = None,
        error: Optional[str] = None,
        status_code: Optional[int] = None
    ):
        self.success = success
        self.data = data
        self.error = error
        self.status_code = status_code

    def __bool__(self):
        return self.success


class APIClient:
    """Centralized API client with consistent auth, retries, and error handling."""

    def __init__(self, base_url: str = API_BASE_URL, timeout: int = API_TIMEOUT, max_retries: int = 3, backoff_base: float = 0.4):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff_base = backoff_base

    def _build_url(self, endpoint: str) -> str:
        if endpoint.startswith("http://") or endpoint.startswith("https://"):
            return endpoint
        if not endpoint.startswith("/"):
            endpoint = f"/{endpoint}"
        return f"{self.base_url}{endpoint}"

    def _get_error_message(self, status_code: int, response_text: str) -> str:
        error_messages = {
            400: "❌ Invalid Request",
            401: "🔐 Authentication Error",
            403: "🚫 Access Denied",
            404: "🔍 Not Found",
            422: "❌ Validation Error",
            429: "⏱️ Too Many Requests",
            500: "❌ Server Error",
            502: "🔌 Bad Gateway",
            503: "🔧 Service Unavailable",
            504: "⏱️ Timeout",
        }
        return error_messages.get(status_code, f"❌ Error {status_code}")

    def _should_retry(self, method: str, status_code: Optional[int], exception: Optional[Exception]) -> bool:
        if exception is not None:
            return True  # connection issues/timeouts
        if status_code is None:
            return True
        if status_code in (502, 503, 504, 429, 500):
            return True
        return False

    def _sleep_backoff(self, attempt: int):
        delay = self.backoff_base * (2 ** attempt)
        time.sleep(min(delay, 5.0))

    def _request_once(self, method: str, url: str, inject_auth: bool, timeout: int, **kwargs) -> requests.Response:
        headers = kwargs.pop("headers", {}) or {}
        if inject_auth:
            headers = {**headers, **get_auth_headers()}
        return requests.request(method, url, headers=headers, timeout=timeout, **kwargs)

    def _make_request(self, method: str, endpoint: str, inject_auth: bool = True, **kwargs) -> APIResponse:
        url = self._build_url(endpoint)
        timeout = kwargs.pop("timeout", self.timeout)

        # Attempt with retries
        last_exception: Optional[Exception] = None
        for attempt in range(self.max_retries + 1):
            try:
                resp = self._request_once(method, url, inject_auth=inject_auth and not endpoint.startswith("/auth"), timeout=timeout, **kwargs)

                # Attempt token refresh on 401 once (no retry loop explosion)
                if resp.status_code == 401 and inject_auth and not endpoint.startswith("/auth"):
                    if refresh_tokens_if_needed():
                        # Retry the same request with fresh token (single immediate retry)
                        resp = self._request_once(method, url, inject_auth=True, timeout=timeout, **kwargs)
                    else:
                        # Logout user safely if refresh fails
                        logout()
                        return APIResponse(success=False, error="🔐 Session expired. Please sign in again.", status_code=401)

                # Successful JSON response
                if 200 <= resp.status_code < 300:
                    try:
                        data = resp.json()
                    except ValueError:
                        data = None
                    return APIResponse(success=True, data=data, status_code=resp.status_code)

                # Non-success - possibly retry
                if self._should_retry(method, resp.status_code, None) and attempt < self.max_retries:
                    self._sleep_backoff(attempt)
                    continue

                # Return structured error
                return APIResponse(
                    success=False,
                    error=self._get_error_message(resp.status_code, resp.text),
                    status_code=resp.status_code
                )

            except requests.exceptions.Timeout as e:
                last_exception = e
                if attempt < self.max_retries:
                    self._sleep_backoff(attempt)
                    continue
                return APIResponse(success=False, error="⏱️ Timeout", status_code=504)
            except requests.exceptions.ConnectionError as e:
                last_exception = e
                if attempt < self.max_retries:
                    self._sleep_backoff(attempt)
                    continue
                return APIResponse(success=False, error="Backend offline", status_code=None)
            except Exception as e:
                last_exception = e
                break

        return APIResponse(success=False, error=f"❌ Unexpected Error: {str(last_exception) if last_exception else 'Unknown'}", status_code=None)

    # Convenience HTTP verbs
    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None, timeout: Optional[int] = None) -> APIResponse:
        kwargs: Dict[str, Any] = {}
        if params:
            kwargs["params"] = params
        if timeout is not None:
            kwargs["timeout"] = timeout
        return self._make_request("GET", endpoint, **kwargs)

    def post(self, endpoint: str, payload: Optional[Dict[str, Any]] = None, timeout: Optional[int] = None) -> APIResponse:
        kwargs: Dict[str, Any] = {}
        if payload is not None:
            kwargs["json"] = payload
        if timeout is not None:
            kwargs["timeout"] = timeout
        return self._make_request("POST", endpoint, **kwargs)

    def put(self, endpoint: str, payload: Optional[Dict[str, Any]] = None, timeout: Optional[int] = None) -> APIResponse:
        kwargs: Dict[str, Any] = {}
        if payload is not None:
            kwargs["json"] = payload
        if timeout is not None:
            kwargs["timeout"] = timeout
        return self._make_request("PUT", endpoint, **kwargs)

    def delete(self, endpoint: str, params: Optional[Dict[str, Any]] = None, timeout: Optional[int] = None) -> APIResponse:
        kwargs: Dict[str, Any] = {}
        if params:
            kwargs["params"] = params
        if timeout is not None:
            kwargs["timeout"] = timeout
        return self._make_request("DELETE", endpoint, **kwargs)

    # Domain helpers
    def analyze_decision(self, payload: Dict[str, Any]) -> APIResponse:
        return self.post("/api/v1/decision/analyze", payload)

    def submit_feedback(self, payload: Dict[str, Any]) -> APIResponse:
        return self.post("/api/v1/feedback", payload)

    def get_audit_entries(self, limit: int = 100, **filters) -> APIResponse:
        params = {"limit": limit, **filters}
        return self.get("/api/v1/audit/entries", params=params)

    def health_check(self) -> APIResponse:
        return self.get("/health")


def parseAgenticResponse(response: APIResponse) -> Tuple[str, Optional[Dict[str, Any]], Optional[str], Optional[str]]:
    if not response or not response.success or not response.data:
        return None, None, response.error if response else "Unknown error", None
    data = response.data if isinstance(response.data, dict) else {}
    status = data.get("status")
    results = data.get("results")
    error = data.get("error")
    timestamp = data.get("timestamp")
    if status not in ["completed", "timeout", "error"]:
        return None, None, f"Invalid status: {status}", timestamp
    return status, results, error, timestamp


def display_api_error(response: APIResponse):
    if response and response.error == "Backend offline":
        st.error("Backend offline")
        return
    st.error(response.error or "❌ Unknown error")

