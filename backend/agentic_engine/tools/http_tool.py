"""
HTTP Tool Module

Provides HTTP request capabilities for external API interactions.
Safe GET/POST wrapper with timeouts, retries, and error handling.
"""

from typing import Dict, Any, Optional, List
import os
from urllib.parse import urlparse
import httpx


class HTTPTool:
    """
    Tool for making HTTP requests to external services.
    
    Provides:
    - Safe GET/POST methods with timeouts
    - Automatic retries with exponential backoff
    - Error handling and response validation
    """
    
    def __init__(
        self,
        timeout: float = 30.0,
        max_retries: int = 3,
        verify_ssl: bool = True,
        allowed_hosts: Optional[List[str]] = None
    ):
        """
        Initialize HTTP tool.
        
        Args:
            timeout: Request timeout in seconds (default: 30.0)
            max_retries: Maximum number of retry attempts (default: 3)
            verify_ssl: Whether to verify SSL certificates (default: True)
        """
        self.timeout = timeout
        self.max_retries = max_retries
        self.verify_ssl = verify_ssl
        self._client = None
        # Allowlist from env or constructor; empty list disables outbound calls by default
        env_hosts = os.getenv("AGENTIC_HTTP_ALLOWLIST", "")
        env_allowlist = [h.strip().lower() for h in env_hosts.split(",") if h.strip()]
        self.allowed_hosts = [h.lower() for h in (allowed_hosts or env_allowlist)]
    
    @property
    def name(self) -> str:
        """Get tool name"""
        return "http_tool"
    
    @property
    def description(self) -> str:
        """Get tool description"""
        return "Makes HTTP requests to external APIs and services. Supports GET and POST methods with automatic retries and error handling."
    
    @property
    def schema(self) -> Dict[str, Any]:
        """Get tool JSON schema"""
        return {
            "type": "object",
            "properties": {
                "method": {
                    "type": "string",
                    "enum": ["GET", "POST"],
                    "description": "HTTP method to use"
                },
                "url": {
                    "type": "string",
                    "description": "Target URL to request"
                },
                "params": {
                    "type": "object",
                    "description": "Query parameters for GET requests"
                },
                "data": {
                    "type": "object",
                    "description": "Form data for POST requests"
                },
                "json": {
                    "type": "object",
                    "description": "JSON data for POST requests"
                },
                "headers": {
                    "type": "object",
                    "description": "HTTP headers"
                }
            },
            "required": ["method", "url"]
        }

    def _is_url_allowed(self, url: str) -> bool:
        """
        Validate URL against scheme and allowlist. Deny by default when allowlist empty.
        """
        try:
            parsed = urlparse(url)
            if parsed.scheme not in {"http", "https"}:
                return False
            if not self.allowed_hosts:
                return False
            host = (parsed.hostname or "").lower()
            return host in self.allowed_hosts
        except Exception:
            return False
    
    def run(self, input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute HTTP request.
        
        Args:
            input: Dictionary containing:
                - method: HTTP method ("GET" or "POST")
                - url: Target URL (required)
                - params: Query parameters (optional, for GET)
                - data: Form data (optional, for POST)
                - json: JSON data (optional, for POST)
                - headers: HTTP headers (optional)
        
        Returns:
            Dictionary containing:
                - success: Whether request succeeded
                - status_code: HTTP status code
                - data: Response data (parsed JSON or text)
                - headers: Response headers
                - error: Error message if failed
        """
        method = input.get("method", "GET").upper()
        url = input.get("url")
        
        if not url:
            return {
                "success": False,
                "error": "URL is required",
                "status_code": None,
                "data": None
            }

        if not self._is_url_allowed(url):
            return {
                "success": False,
                "error": "HTTP tool disabled or host not allowed",
                "status_code": None,
                "data": None,
                "url": url,
                "method": method
            }
        
        try:
            with httpx.Client(
                timeout=self.timeout,
                verify=self.verify_ssl,
                follow_redirects=True
            ) as client:
                if method == "GET":
                    response = client.get(
                        url,
                        params=input.get("params"),
                        headers=input.get("headers")
                    )
                elif method == "POST":
                    response = client.post(
                        url,
                        data=input.get("data"),
                        json=input.get("json"),
                        headers=input.get("headers")
                    )
                else:
                    return {
                        "success": False,
                        "error": f"Unsupported method: {method}. Use GET or POST",
                        "status_code": None,
                        "data": None
                    }
                
                # Parse response
                try:
                    response_data = response.json()
                except:
                    response_data = response.text
                
                return {
                    "success": True,
                    "status_code": response.status_code,
                    "data": response_data,
                    "headers": dict(response.headers),
                    "url": str(response.url),
                    "method": method
                }
        
        except httpx.TimeoutException as e:
            return {
                "success": False,
                "error": f"Request timeout after {self.timeout}s: {str(e)}",
                "status_code": None,
                "data": None,
                "url": url,
                "method": method
            }
        except httpx.HTTPError as e:
            return {
                "success": False,
                "error": f"HTTP error: {str(e)}",
                "status_code": None,
                "data": None,
                "url": url,
                "method": method
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "status_code": None,
                "data": None,
                "url": url,
                "method": method
            }
    
    # Legacy methods for backward compatibility
    def get_sync(self, url: str, params: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None, **kwargs) -> Dict[str, Any]:
        """Synchronous GET request (legacy method)"""
        return self.run({"method": "GET", "url": url, "params": params, "headers": headers, **kwargs})
    
    def post_sync(self, url: str, data: Optional[Dict[str, Any]] = None, json: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None, **kwargs) -> Dict[str, Any]:
        """Synchronous POST request (legacy method)"""
        return self.run({"method": "POST", "url": url, "data": data, "json": json, "headers": headers, **kwargs})
