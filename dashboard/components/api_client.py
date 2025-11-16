"""
API Client
==========
Centralized API client with consistent error handling.
"""

import requests
import streamlit as st
from typing import Dict, Any, Optional, Tuple
from .constants import API_BASE_URL, API_TIMEOUT


class APIResponse:
    """Standardized API response wrapper"""
    
    def __init__(self, success: bool, data: Optional[Dict[str, Any]] = None, 
                 error: Optional[str] = None, status_code: Optional[int] = None):
        self.success = success
        self.data = data
        self.error = error
        self.status_code = status_code
    
    def __bool__(self):
        return self.success


class APIClient:
    """Centralized API client with consistent error handling"""
    
    def __init__(self, base_url: str = API_BASE_URL, timeout: int = API_TIMEOUT):
        self.base_url = base_url
        self.timeout = timeout
    
    def _get_error_message(self, status_code: int, response_text: str) -> str:
        """Get user-friendly error message based on status code"""
        error_messages = {
            400: "❌ **Invalid Request**: The information provided couldn't be processed. Please check all fields.",
            401: "🔐 **Authentication Error**: You need to be logged in to use this feature.",
            403: "🚫 **Access Denied**: You don't have permission to perform this action.",
            404: "🔍 **Not Found**: The requested resource doesn't exist.",
            422: "❌ **Validation Error**: Some of the information you provided is invalid. Please review your entries.",
            429: "⏱️ **Too Many Requests**: You're making requests too quickly. Please wait a moment and try again.",
            500: "❌ **Server Error**: Something went wrong on our end. Please try again in a moment.",
            502: "🔌 **Bad Gateway**: The server is having trouble connecting. Please try again.",
            503: "🔧 **Service Unavailable**: The service is temporarily down. Please try again later.",
            504: "⏱️ **Timeout**: The request took too long. Please try again.",
        }
        
        return error_messages.get(status_code, f"❌ **Error {status_code}**: An unexpected error occurred.")
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> APIResponse:
        """Make HTTP request with error handling"""
        url = f"{self.base_url}{endpoint}"
        
        # Use custom timeout if provided, otherwise use default
        timeout = kwargs.pop('timeout', self.timeout)
        
        try:
            response = requests.request(
                method,
                url,
                timeout=timeout,
                **kwargs
            )
            
            # Success
            if response.status_code == 200:
                try:
                    data = response.json()
                    return APIResponse(success=True, data=data, status_code=200)
                except ValueError:
                    return APIResponse(
                        success=False,
                        error="Server returned invalid JSON",
                        status_code=response.status_code
                    )
            
            # HTTP Error
            error_msg = self._get_error_message(response.status_code, response.text)
            return APIResponse(
                success=False,
                error=error_msg,
                status_code=response.status_code
            )
        
        except requests.exceptions.Timeout:
            return APIResponse(
                success=False,
                error="⏱️ **Timeout**: The AI is taking too long to respond. Please try again.",
                status_code=504
            )
        
        except requests.exceptions.ConnectionError:
            return APIResponse(
                success=False,
                error="🔌 **Connection Error**: Cannot connect to the backend. Is it running?\n\n💡 Start the backend with: `make start`",
                status_code=None
            )
        
        except Exception as e:
            return APIResponse(
                success=False,
                error=f"❌ **Unexpected Error**: {str(e)}",
                status_code=None
            )
    
    def analyze_decision(self, payload: Dict[str, Any]) -> APIResponse:
        """
        Call decision analysis endpoint
        
        Args:
            payload: Dictionary with 'entity' and 'task' keys
            
        Returns:
            APIResponse with analysis result or error
        """
        return self._make_request(
            "POST",
            "/api/v1/decision/analyze",
            json=payload
        )
    
    def submit_feedback(self, payload: Dict[str, Any]) -> APIResponse:
        """
        Submit feedback to API
        
        Args:
            payload: Feedback data dictionary
            
        Returns:
            APIResponse indicating success or failure
        """
        return self._make_request(
            "POST",
            "/api/v1/feedback",
            json=payload
        )
    
    def get_audit_entries(self, limit: int = 100, **filters) -> APIResponse:
        """
        Get audit trail entries
        
        Args:
            limit: Maximum number of entries
            **filters: Additional query parameters
            
        Returns:
            APIResponse with audit entries or error
        """
        params = {"limit": limit, **filters}
        return self._make_request(
            "GET",
            "/api/v1/audit",
            params=params
        )
    
    def health_check(self) -> APIResponse:
        """
        Check if backend is healthy
        
        Returns:
            APIResponse indicating backend health
        """
        return self._make_request("GET", "/health")

    def post(self, endpoint: str, payload: Dict[str, Any], timeout: Optional[int] = None) -> APIResponse:
        """
        Make a POST request to the API
        
        Args:
            endpoint: API endpoint (e.g., "/api/v1/agentic/analyze")
            payload: Request payload dictionary
            timeout: Optional timeout in seconds (overrides default)
            
        Returns:
            APIResponse with result or error
        """
        kwargs = {"json": payload}
        if timeout is not None:
            kwargs["timeout"] = timeout
        return self._make_request("POST", endpoint, **kwargs)
    
    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> APIResponse:
        """
        Make a GET request to the API
        
        Args:
            endpoint: API endpoint (e.g., "/api/v1/agentic/status")
            params: Optional query parameters
            
        Returns:
            APIResponse with result or error
        """
        return self._make_request("GET", endpoint, params=params or {})


def parseAgenticResponse(response: APIResponse) -> Tuple[str, Optional[Dict[str, Any]], Optional[str], Optional[str]]:
    """
    Parse standardized agentic API response format.
    
    Handles response format: {status, results, error, timestamp}
    Supports status values: "completed", "timeout", "error"
    
    Args:
        response: APIResponse from agentic endpoint
        
    Returns:
        Tuple of (status, results, error, timestamp):
        - status: "completed", "timeout", "error", or None
        - results: Results dict if available, None otherwise
        - error: Error message if available, None otherwise
        - timestamp: Timestamp string if available, None otherwise
    """
    if not response or not response.success or not response.data:
        return None, None, response.error if response else "Unknown error", None
    
    data = response.data
    
    # Check if response follows standardized format
    if not isinstance(data, dict):
        return None, None, "Invalid response format", None
    
    # Extract standardized fields
    status = data.get("status")  # "completed", "timeout", "error"
    results = data.get("results")  # Results dict or None
    error = data.get("error")  # Error message or None
    timestamp = data.get("timestamp")  # ISO timestamp string or None
    
    # Validate status
    if status not in ["completed", "timeout", "error"]:
        return None, None, f"Invalid status: {status}", timestamp
    
    return status, results, error, timestamp


def display_api_error(response: APIResponse):
    """Display standardized error message to user"""
    st.error(response.error)
    
    if response.status_code in [400, 422]:
        st.markdown("### What to do:")
        st.markdown("1. 👀 **Review your entries** - Check all required fields marked with *")
        st.markdown("2. 🔄 **Try again** - Click the submit button to resubmit")
        st.info("💡 **Good news**: Your information has been saved - you won't need to re-enter it.")
    
    elif response.status_code == 504 or (response.error and "Timeout" in response.error):
        st.markdown("### What to do:")
        st.markdown("1. ⏱️ **Wait a moment** - The AI might be busy")
        st.markdown("2. 🔄 **Try again** - Click the submit button to retry")
        st.markdown("3. ✂️ **Simplify** - Try with a shorter task description")
    
    elif response.status_code is None and "Connection Error" in response.error:
        st.markdown("### What to do:")
        st.markdown("1. 🖥️ **Start the backend** - Run `make start` in your terminal")
        st.markdown("2. ⏳ **Wait 10 seconds** - Let it fully start")
        st.markdown("3. 🔄 **Refresh this page** - Press F5 or reload your browser")
    
    else:
        st.markdown("### What to do:")
        st.markdown("1. 🔄 **Try submitting again**")
        st.markdown("2. 🌐 **Refresh if needed** - Press F5")
        st.markdown("3. 📞 **Contact support** - If the issue persists")

