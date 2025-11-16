"""Main FastAPI application entry point"""

import sys
import traceback
import json

try:
    from dotenv import load_dotenv
    
    # Load environment variables FIRST before any imports that might need them
    load_dotenv()
    
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    from contextlib import asynccontextmanager
    import uvicorn

    from src.api.routes import router as api_router
    from src.api.decision_routes import router as decision_router
    from src.api.audit_routes import router as audit_router
    from src.api.entity_analysis_routes import router as entity_analysis_router
    from src.api.feedback_routes import router as feedback_router
    from src.api.agentic_routes import router as agentic_router
    from src.db.base import engine, Base
    from src.auth.auth_router import router as auth_router
    from src.auth.security import get_current_user
    from src.config import settings
    from src.api.error_handlers import register_exception_handlers
    from src.api.rate_limit import limiter, rate_limit_handler
    from slowapi.middleware import SlowAPIMiddleware
    from slowapi.errors import RateLimitExceeded
    import jwt
    import logging
    import os
    from pathlib import Path
    import uuid
except Exception as e:
    print(f"❌ STARTUP ERROR: Failed to import dependencies")
    print(f"Error: {e}")
    traceback.print_exc()
    sys.exit(1)


def validate_environment():
    """Validate required environment variables with helpful messages."""
    errors = []
    
    # Check OpenAI API Key
    openai_key = settings.OPENAI_API_KEY
    if not openai_key:
        errors.append("OPENAI_API_KEY is missing")
    elif not str(openai_key).startswith("sk-"):
        errors.append("OPENAI_API_KEY appears invalid (should start with 'sk-')")
    
    # Check Secret Key
    secret_key = settings.SECRET_KEY
    if not secret_key:
        errors.append("SECRET_KEY is missing")
    elif len(secret_key) < 32:
        errors.append("SECRET_KEY is too short (should be at least 32 characters)")
    
    if errors:
        print("\n" + "="*70)
        print("❌ ENVIRONMENT CONFIGURATION ERROR")
        print("="*70)
        for error in errors:
            print(f"  • {error}")
        print("\n💡 To fix:")
        print("  1. Copy .env.example to .env:")
        print("     cp .env.example .env")
        print("  2. Edit .env and add your actual values")
        print("  3. Get OpenAI key from: https://platform.openai.com/api-keys")
        print("="*70 + "\n")
        sys.exit(1)
    
    print("✅ Environment configuration validated")


# Validate environment before creating app
validate_environment()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events"""
    # Startup: Create database tables
    try:
        print("Starting up application...")
        print(f"Database URL: {settings.DATABASE_URL}")
        Base.metadata.create_all(bind=engine)
        print("✅ Database initialized successfully")
    except Exception as e:
        print(f"❌ DATABASE ERROR: {e}")
        traceback.print_exc()
        raise
    yield
    # Shutdown: Clean up resources
    print("Shutting down application...")


# Initialize FastAPI app (disable docs in production)
docs_kwargs = {}
if not settings.DEBUG:
    docs_kwargs = {"docs_url": None, "redoc_url": None, "openapi_url": None}
app = FastAPI(
    title="Agentic Compliance Agent",
    description="AI-powered compliance agent using OpenAI GPT-4o-mini via LangChain",
    version="0.1.0",
    lifespan=lifespan,
    **docs_kwargs,
)

# -----------------------------------------------------------------------------
# Logging configuration
# -----------------------------------------------------------------------------
logs_dir = Path("logs")
logs_dir.mkdir(parents=True, exist_ok=True)
log_file = logs_dir / "backend.log"

logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ],
)
logger = logging.getLogger("backend")
logger.info("Logging initialized")

# -----------------------------------------------------------------------------
# Request ID middleware for traceability
# -----------------------------------------------------------------------------
@app.middleware("http")
async def add_request_id(request, call_next):
    request.state.request_id = str(uuid.uuid4())
    response = await call_next(request)
    # Attach request id to response headers for correlation
    response.headers["X-Request-ID"] = request.state.request_id
    return response

# -----------------------------------------------------------------------------
# Rate limiting
# -----------------------------------------------------------------------------
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_handler)
app.add_middleware(SlowAPIMiddleware)

# Configure CORS from settings
allow_origins_list = settings.BACKEND_CORS_ORIGINS

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Auth routes
app.include_router(auth_router, prefix="/auth")

# Include API routes (protected)
from fastapi import Depends
app.include_router(api_router, prefix="/api/v1", dependencies=[Depends(get_current_user)])
app.include_router(decision_router, prefix="/api/v1", dependencies=[Depends(get_current_user)])
app.include_router(audit_router, prefix="/api/v1", dependencies=[Depends(get_current_user)])
app.include_router(entity_analysis_router, prefix="/api/v1", dependencies=[Depends(get_current_user)])
app.include_router(feedback_router, prefix="/api/v1", dependencies=[Depends(get_current_user)])
app.include_router(agentic_router, prefix="/api/v1/agentic", dependencies=[Depends(get_current_user)])

# Register global exception handlers
register_exception_handlers(app)

# JWT specific exception mapping to 401 JSON
from fastapi.responses import JSONResponse

@app.exception_handler(jwt.ExpiredSignatureError)
async def expired_jwt_handler(request, exc):
    return JSONResponse(
        status_code=401,
        content={"success": False, "error": {"type": "JWTExpired", "message": "Token expired", "details": None}},
    )

@app.exception_handler(jwt.InvalidTokenError)
async def invalid_jwt_handler(request, exc):
    return JSONResponse(
        status_code=401,
        content={"success": False, "error": {"type": "JWTInvalid", "message": "Invalid token", "details": None}},
    )

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Agentic Compliance Agent API",
        "version": "0.1.0",
        "status": "running",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    from datetime import datetime
    return {
        "status": "healthy",
        "version": "0.1.0",
        "service": "AI Compliance Agent",
        "timestamp": datetime.now().isoformat()
    }


if __name__ == "__main__":
    host = settings.API_HOST
    port = int(settings.API_PORT)
    debug = bool(settings.DEBUG)
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=debug,
        server_header=False,
    )

