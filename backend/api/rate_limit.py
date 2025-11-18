from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request
from fastapi.responses import JSONResponse
from typing import Dict, Any

# Global limiter instance
limiter = Limiter(key_func=get_remote_address, default_limits=[])

# Limit definitions
PUBLIC_RATE = "50/minute"
AUTH_RATE = "200/minute"


def _error_payload(message: str, details: Any = None) -> Dict[str, Any]:
    return {
        "success": False,
        "error": {
            "type": "RateLimitExceeded",
            "message": message,
            "details": details
        }
    }


async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content=_error_payload("Rate limit exceeded", {"limit": str(exc.detail)}),
        headers={"Retry-After": str(exc.retry_after) if hasattr(exc, "retry_after") else "60"},
    )


