from typing import Any, Dict
import logging
import traceback
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi import HTTPException, FastAPI
from sqlalchemy.exc import IntegrityError


logger = logging.getLogger("backend")


def _error_payload(error_type: str, message: str, details: Any = None) -> Dict[str, Any]:
    return {
        "success": False,
        "error": {
            "type": error_type,
            "message": message,
            "details": details
        }
    }


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    request_id = getattr(request.state, "request_id", None)
    logger.warning(f"[{request_id}] Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content=_error_payload(
            "RequestValidationError",
            "Request validation failed",
            details=exc.errors()
        ),
    )


async def http_exception_handler(request: Request, exc: HTTPException):
    request_id = getattr(request.state, "request_id", None)
    logger.info(f"[{request_id}] HTTPException {exc.status_code}: {exc.detail}")
    message = str(exc.detail) if exc.detail else "HTTP error"
    payload = _error_payload(
        "HTTPException",
        message,
        details={"status_code": exc.status_code}
    )
    # Preserve a simple detail key for clients/tests that expect FastAPI's default structure
    payload["detail"] = message
    return JSONResponse(status_code=exc.status_code, content=payload)


async def integrity_error_handler(request: Request, exc: IntegrityError):
    request_id = getattr(request.state, "request_id", None)
    logger.error(f"[{request_id}] IntegrityError: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=409,
        content=_error_payload(
            "IntegrityError",
            "Database constraint violated",
            details=str(exc.orig) if getattr(exc, "orig", None) else str(exc)
        ),
    )


async def value_error_handler(request: Request, exc: ValueError):
    request_id = getattr(request.state, "request_id", None)
    logger.warning(f"[{request_id}] ValueError: {str(exc)}")
    return JSONResponse(
        status_code=400,
        content=_error_payload(
            "ValueError",
            str(exc) or "Invalid value",
            details=None
        ),
    )


async def generic_exception_handler(request: Request, exc: Exception):
    request_id = getattr(request.state, "request_id", None)
    logger.error(f"[{request_id}] Unhandled exception: {str(exc)}\n{traceback.format_exc()}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content=_error_payload(
            "InternalServerError",
            "An unexpected error occurred",
            details={"request_id": request_id}
        ),
    )


def register_exception_handlers(app: FastAPI):
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(IntegrityError, integrity_error_handler)
    app.add_exception_handler(ValueError, value_error_handler)
    app.add_exception_handler(Exception, generic_exception_handler)

