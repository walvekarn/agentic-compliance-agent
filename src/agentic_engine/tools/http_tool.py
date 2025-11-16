"""
HTTP Tool Module

Provides HTTP request capabilities for external API interactions.
Safe GET/POST wrapper with timeouts, retries, and error handling.
"""

from typing import Dict, Any, Optional
import httpx
import asyncio


class HTTPTool:
    """
    Tool for making HTTP requests to external services.
    
    Provides:
    - Safe GET/POST methods with timeouts
    - Automatic retries with exponential backoff
    - Error handling and response validation
    - Request/response logging
    """
    
    def __init__(
        self,
        timeout: float = 30.0,
        max_retries: int = 3,
        verify_ssl: bool = True
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
    
    def _get_client(self) -> httpx.AsyncClient:
        """Get or create async HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=self.timeout,
                verify=self.verify_ssl,
                follow_redirects=True
            )
        return self._client
    
    async def get(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Make a safe HTTP GET request with timeout and retries.
        
        Args:
            url: Target URL
            params: Query parameters
            headers: HTTP headers
            **kwargs: Additional httpx parameters
            
        Returns:
            Dictionary containing:
                - status_code: HTTP status code
                - data: Response data (parsed JSON or text)
                - headers: Response headers
                - success: Whether request succeeded
                - error: Error message if failed
        """
        return await self._request(
            method="GET",
            url=url,
            params=params,
            headers=headers,
            **kwargs
        )
    
    async def post(
        self,
        url: str,
        data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Make a safe HTTP POST request with timeout and retries.
        
        Args:
            url: Target URL
            data: Form data
            json: JSON data
            headers: HTTP headers
            **kwargs: Additional httpx parameters
            
        Returns:
            Dictionary containing:
                - status_code: HTTP status code
                - data: Response data (parsed JSON or text)
                - headers: Response headers
                - success: Whether request succeeded
                - error: Error message if failed
        """
        return await self._request(
            method="POST",
            url=url,
            data=data,
            json=json,
            headers=headers,
            **kwargs
        )
    
    async def _request(
        self,
        method: str,
        url: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Internal method to make HTTP requests with retries and error handling.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            url: Target URL
            **kwargs: Request parameters
            
        Returns:
            Response dictionary with status, data, and metadata
        """
        client = self._get_client()
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                # Make request
                response = await client.request(method, url, **kwargs)
                
                # Parse response
                try:
                    response_data = response.json()
                except:
                    response_data = response.text
                
                # Return success response
                return {
                    "success": True,
                    "status_code": response.status_code,
                    "data": response_data,
                    "headers": dict(response.headers),
                    "url": str(response.url),
                    "method": method,
                    "attempts": attempt + 1
                }
            
            except httpx.TimeoutException as e:
                last_error = f"Request timeout after {self.timeout}s: {str(e)}"
                if attempt < self.max_retries - 1:
                    # Exponential backoff
                    await asyncio.sleep(2 ** attempt)
                    continue
            
            except httpx.HTTPError as e:
                last_error = f"HTTP error: {str(e)}"
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
            
            except Exception as e:
                last_error = f"Unexpected error: {str(e)}"
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
        
        # All retries exhausted
        return {
            "success": False,
            "status_code": None,
            "data": None,
            "error": last_error,
            "url": url,
            "method": method,
            "attempts": self.max_retries
        }
    
    async def close(self):
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
    
    # Synchronous versions for convenience
    
    def get_sync(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Synchronous version of GET request.
        
        Args:
            url: Target URL
            params: Query parameters
            headers: HTTP headers
            **kwargs: Additional parameters
            
        Returns:
            Response dictionary
        """
        try:
            with httpx.Client(
                timeout=self.timeout,
                verify=self.verify_ssl,
                follow_redirects=True
            ) as client:
                response = client.get(url, params=params, headers=headers, **kwargs)
                
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
                    "method": "GET"
                }
        
        except Exception as e:
            return {
                "success": False,
                "status_code": None,
                "data": None,
                "error": str(e),
                "url": url,
                "method": "GET"
            }
    
    def post_sync(
        self,
        url: str,
        data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Synchronous version of POST request.
        
        Args:
            url: Target URL
            data: Form data
            json: JSON data
            headers: HTTP headers
            **kwargs: Additional parameters
            
        Returns:
            Response dictionary
        """
        try:
            with httpx.Client(
                timeout=self.timeout,
                verify=self.verify_ssl,
                follow_redirects=True
            ) as client:
                response = client.post(
                    url,
                    data=data,
                    json=json,
                    headers=headers,
                    **kwargs
                )
                
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
                    "method": "POST"
                }
        
        except Exception as e:
            return {
                "success": False,
                "status_code": None,
                "data": None,
                "error": str(e),
                "url": url,
                "method": "POST"
            }

