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

from typing import Dict, Any, Optional, Tuple, Union, List
import time
import requests
import streamlit as st
from .constants import API_BASE_URL, API_TIMEOUT
from .auth_utils import get_auth_headers, refresh_tokens_if_needed, logout, is_authenticated


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

    def _parse_error_response(self, response_data: Any) -> str:
        """
        Parse error response from backend, handling both string and nested object formats.
        
        Backend can return:
        - String: "Error message"
        - Dict: {"error": {"type": "...", "message": "...", "details": {...}}}
        - Dict: {"error": "Error message"}
        """
        if isinstance(response_data, str):
            return response_data
        
        if isinstance(response_data, dict):
            # Check for nested error structure (standardized format)
            if "error" in response_data:
                error = response_data["error"]
                if isinstance(error, dict):
                    # Extract message from nested error object
                    message = error.get("message", str(error))
                    error_type = error.get("type", "")
                    if error_type:
                        return f"{message} ({error_type})"
                    return message
                # Error is a string
                return str(error)
            
            # Check for direct error message
            if "message" in response_data:
                return str(response_data["message"])
            
            # Fallback: stringify the dict
            return str(response_data)
        
        return str(response_data)

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
                        # Only logout if we're actually authenticated (prevents logout on Home page)
                        if is_authenticated():
                            logout()
                            return APIResponse(success=False, error="🔐 Session expired. Please sign in again.", status_code=401)
                        else:
                            # Not authenticated - return error without logging out
                            return APIResponse(success=False, error="🔐 Please sign in to access this resource.", status_code=401)

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

                # Try to parse error response from JSON
                error_msg = self._get_error_message(resp.status_code, resp.text)
                try:
                    error_data = resp.json()
                    parsed_error = self._parse_error_response(error_data)
                    if parsed_error:
                        error_msg = parsed_error
                except (ValueError, AttributeError):
                    # If JSON parsing fails, use default error message
                    pass
                
                print(f"❌ API Request Failed: {method} {endpoint} - {error_msg} (Status: {resp.status_code})", flush=True)
                if resp.status_code >= 500:
                    print(f"   Server error details: {resp.text[:200]}", flush=True)
                
                # Return structured error
                return APIResponse(
                    success=False,
                    error=error_msg,
                    status_code=resp.status_code
                )

            except requests.exceptions.Timeout as e:
                last_exception = e
                print(f"⏱️ API Request Timeout: {method} {endpoint} (attempt {attempt + 1}/{self.max_retries + 1})", flush=True)
                if attempt < self.max_retries:
                    self._sleep_backoff(attempt)
                    continue
                print(f"❌ API Request Failed: {method} {endpoint} - Timeout after {self.max_retries + 1} attempts", flush=True)
                return APIResponse(success=False, error="⏱️ Timeout", status_code=504)
            except requests.exceptions.ConnectionError as e:
                last_exception = e
                print(f"🔌 API Connection Error: {method} {endpoint} (attempt {attempt + 1}/{self.max_retries + 1}) - {str(e)[:100]}", flush=True)
                if attempt < self.max_retries:
                    self._sleep_backoff(attempt)
                    continue
                print(f"❌ API Request Failed: {method} {endpoint} - Backend offline after {self.max_retries + 1} attempts", flush=True)
                return APIResponse(success=False, error="Backend offline", status_code=None)
            except Exception as e:
                last_exception = e
                print(f"❌ API Request Exception: {method} {endpoint} - {type(e).__name__}: {str(e)[:200]}", flush=True)
                break

        error_msg = f"❌ Unexpected Error: {str(last_exception) if last_exception else 'Unknown'}"
        print(f"❌ API Request Failed: {method} {endpoint} - {error_msg}", flush=True)
        return APIResponse(success=False, error=error_msg, status_code=None)

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

    # Domain helpers - Decision Engine
    def analyze_decision(self, payload: Dict[str, Any]) -> APIResponse:
        """Analyze a compliance decision task"""
        return self.post("/api/v1/decision/analyze", payload)

    def quick_check(self, payload: Dict[str, Any]) -> APIResponse:
        """Quick risk check (lightweight analysis)"""
        return self.post("/api/v1/decision/quick-check", payload)
    
    def batch_analyze(self, payload: Dict[str, Any]) -> APIResponse:
        """Batch analyze multiple compliance tasks"""
        return self.post("/api/v1/decision/batch-analyze", payload)
    
    def what_if_analysis(self, payload: Dict[str, Any]) -> APIResponse:
        """Run what-if scenario analysis"""
        return self.post("/api/v1/decision/what-if", payload)
    
    def compare_scenarios(self, payload: Dict[str, Any]) -> APIResponse:
        """Compare multiple what-if scenarios"""
        return self.post("/api/v1/decision/what-if/compare", payload)
    
    def get_risk_levels(self) -> APIResponse:
        """Get risk level information"""
        return self.get("/api/v1/decision/risk-levels")
    
    # Domain helpers - Feedback
    def submit_feedback(self, payload: Dict[str, Any]) -> APIResponse:
        """Submit human feedback on AI decision"""
        return self.post("/api/v1/feedback", payload)

    def get_feedback(self, limit: int = 100, **filters) -> APIResponse:
        """Get feedback entries with optional filters"""
        params = {"limit": limit, **filters}
        return self.get("/api/v1/feedback", params=params)
    
    def get_feedback_stats(self) -> APIResponse:
        """Get feedback statistics"""
        return self.get("/api/v1/feedback/stats")
    
    def get_feedback_by_id(self, feedback_id: int) -> APIResponse:
        """Get specific feedback entry by ID"""
        return self.get(f"/api/v1/feedback/{feedback_id}")
    
    def get_feedback_overrides(self) -> APIResponse:
        """Get override tracking statistics"""
        return self.get("/api/v1/feedback/overrides")
    
    # Domain helpers - Audit Trail
    def get_audit_entries(self, limit: int = 100, **filters) -> APIResponse:
        """Get audit trail entries with optional filters"""
        params = {"limit": limit, **filters}
        return self.get("/api/v1/audit/entries", params=params)

    def get_audit_entry(self, audit_id: int) -> APIResponse:
        """Get specific audit entry by ID"""
        return self.get(f"/api/v1/audit/entries/{audit_id}")
    
    def get_audit_statistics(self) -> APIResponse:
        """Get audit trail statistics"""
        return self.get("/api/v1/audit/statistics")
    
    def export_audit_json(self, **filters) -> APIResponse:
        """Export audit trail as JSON"""
        return self.get("/api/v1/audit/export/json", params=filters)
    
    def get_audit_filters(self) -> APIResponse:
        """Get available audit filter options"""
        return self.get("/api/v1/audit/filters")
    
    def get_recent_audit_entries(self, limit: int = 10) -> APIResponse:
        """Get recent audit entries"""
        return self.get("/api/v1/audit/recent", params={"limit": limit})
    
    def get_audit_by_entity(self, entity_name: str) -> APIResponse:
        """Get audit entries for specific entity"""
        return self.get(f"/api/v1/audit/entity/{entity_name}")
    
    # Domain helpers - Entity Analysis
    def analyze_entity(self, payload: Dict[str, Any]) -> APIResponse:
        """Analyze entity and generate compliance calendar"""
        return self.post("/api/v1/entity/analyze", payload)
    
    def get_entity_history(self, entity_name: str) -> APIResponse:
        """Get entity compliance history"""
        return self.get(f"/api/v1/entity/history/{entity_name}")
    
    def get_audit_log(self, task_id: str) -> APIResponse:
        """Get audit log for specific task"""
        return self.get(f"/api/v1/audit_log/{task_id}")
    
    # Domain helpers - Agentic Engine
    def agentic_analyze(self, payload: Dict[str, Any], timeout: Optional[int] = 120) -> APIResponse:
        """Run advanced agentic analysis (plan-execute-reflect)"""
        return self.post("/api/v1/agentic/analyze", payload, timeout=timeout)
    
    def agentic_status(self) -> APIResponse:
        """Get agentic engine status and configuration"""
        return self.get("/api/v1/agentic/status")
    
    def agentic_health_check(self) -> APIResponse:
        """Get comprehensive agentic health check"""
        return self.get("/api/v1/agentic/health/full")
    
    def run_test_suite(self, payload: Dict[str, Any], timeout: Optional[int] = 120) -> APIResponse:
        """Run agentic test suite"""
        return self.post("/api/v1/agentic/testSuite", payload, timeout=timeout)
    
    def run_benchmarks(self, payload: Dict[str, Any], timeout: Optional[int] = 120) -> APIResponse:
        """Run agentic benchmark suite"""
        return self.post("/api/v1/agentic/benchmarks", payload, timeout=timeout)
    
    def simulate_recovery(self, payload: Dict[str, Any], timeout: Optional[int] = 120) -> APIResponse:
        """Simulate error recovery scenarios"""
        return self.post("/api/v1/agentic/recovery", payload, timeout=timeout)
    
    # Domain helpers - Query
    def process_query(self, query: str, chat_history: Optional[List[dict]] = None) -> APIResponse:
        """Process natural language compliance query"""
        payload = {"query": query}
        if chat_history:
            payload["chat_history"] = chat_history
        return self.post("/api/v1/query", payload)
    
    def get_queries(self, skip: int = 0, limit: int = 10) -> APIResponse:
        """Get query history"""
        return self.get("/api/v1/queries", params={"skip": skip, "limit": limit})
    
    # Domain helpers - Rules
    def create_rule(self, payload: Dict[str, Any]) -> APIResponse:
        """Create a new compliance rule"""
        return self.post("/api/v1/rules", payload)
    
    def get_rules(self, skip: int = 0, limit: int = 10, category: Optional[str] = None) -> APIResponse:
        """Get compliance rules"""
        params = {"skip": skip, "limit": limit}
        if category:
            params["category"] = category
        return self.get("/api/v1/rules", params=params)
    
    def get_rule(self, rule_id: int) -> APIResponse:
        """Get specific compliance rule by ID"""
        return self.get(f"/api/v1/rules/{rule_id}")
    
    # Domain helpers - System
    def health_check(self) -> APIResponse:
        """Check system health"""
        return self.get("/health")


def parseAgenticResponse(response: APIResponse) -> Tuple[str, Optional[Dict[str, Any]], Optional[str], Optional[str]]:
    """
    Parse agentic API response, handling both standardized format and direct response format.
    
    Standardized format: {status, results, error, timestamp}
    Direct format: {status, plan, step_outputs, ...} (agentic endpoints)
    """
    if not response or not response.success:
        return None, None, response.error if response else "Unknown error", None
    
    if not response.data:
        return None, None, "No data in response", None
    
    data = response.data if isinstance(response.data, dict) else {}
    
    # Check for standardized format first
    if "results" in data:
        status = data.get("status")
        results = data.get("results")
        error = data.get("error")
        timestamp = data.get("timestamp")
        if status not in ["completed", "timeout", "error"]:
            return None, None, f"Invalid status: {status}", timestamp
        return status, results, error, timestamp
    
    # Handle direct agentic response format (has status but no results wrapper)
    status = data.get("status", "unknown")
    if status in ["completed", "timeout", "error", "partial"]:
        # For agentic endpoints, the entire data is the results
        timestamp = data.get("timestamp") or data.get("execution_metrics", {}).get("timestamp")
        error = data.get("error") if status == "error" else None
        return status, data, error, timestamp
    
    # Fallback: treat as completed if we have data
    if data:
        return "completed", data, None, None
    
    return None, None, "Invalid response format", None


def display_api_error(response: APIResponse):
    """
    Display API error to user, handling both string and nested error formats.
    
    Args:
        response: APIResponse object with error information
    """
    if not response:
        st.error("❌ Unknown error")
        return
    
    if response.error == "Backend offline":
        st.error("🔌 Backend offline - Please check if the server is running")
        return
    
    # Error is already parsed as string by _parse_error_response
    error_msg = response.error or "❌ Unknown error"
    st.error(error_msg)
    
    # Show additional details if available in response data
    if response.data and isinstance(response.data, dict):
        if "error" in response.data and isinstance(response.data["error"], dict):
            details = response.data["error"].get("details")
            if details:
                with st.expander("🔍 Error Details"):
                    st.json(details)

