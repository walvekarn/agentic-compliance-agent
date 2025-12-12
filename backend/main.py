"""
Main FastAPI Application
========================
Entry point for the Agentic Compliance API backend.
"""

import logging
from contextlib import asynccontextmanager
import uuid

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from backend.config import settings
from backend.core.version import get_version
from backend.db.base import Base, engine
from backend.api.error_handlers import register_exception_handlers
from backend.api.rate_limit import limiter, rate_limit_handler
from slowapi.errors import RateLimitExceeded

# Import models to ensure they're registered with Base.metadata
# This ensures all SQLAlchemy models are loaded before Base.metadata.create_all()
import backend.db.models  # noqa: F401
import backend.auth.auth_models  # noqa: F401

# Import routers
from backend.auth.auth_router import router as auth_router
from backend.api.routes import router as query_router
from backend.api.decision_routes import router as decision_router
from backend.api.entity_analysis_routes import router as entity_router
from backend.api.audit_routes import router as audit_router
from backend.api.feedback_routes import router as feedback_router
from backend.api.agentic_routes import router as agentic_router

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

logger = logging.getLogger(__name__)

# Environment verification
logger.info("=" * 60)
logger.info("ENVIRONMENT VERIFICATION")
logger.info("=" * 60)
logger.info(f"OPENAI_API_KEY: {'✅ Set' if settings.OPENAI_API_KEY else '❌ Not set (mock mode)'}")
if settings.OPENAI_API_KEY:
    logger.info(f"  Key length: {len(settings.OPENAI_API_KEY)} characters")
    logger.info(f"  Key prefix: {settings.OPENAI_API_KEY[:7]}...")
logger.info(f"DATABASE_URL: {settings.DATABASE_URL}")
logger.info(f"DEBUG: {settings.DEBUG}")
logger.info(f"ALLOW_DEMO_USER: {settings.ALLOW_DEMO_USER}")
logger.info("=" * 60)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Handles startup and shutdown events.
    """
    # Startup: Validate environment
    logger.info("Starting up application...")
    errors = []
    warnings = []
    
    # Check OpenAI API key
    if not settings.OPENAI_API_KEY or settings.OPENAI_API_KEY == "":
        errors.append("OPENAI_API_KEY is not set")
    elif not settings.OPENAI_API_KEY.startswith("sk-"):
        errors.append("OPENAI_API_KEY format looks invalid (should start with 'sk-')")
    else:
        logger.info("✓ OpenAI API key found")
    
    # Check secrets
    if settings.SECRET_KEY == "dev_secret_key_change_me":
        warnings.append("Using default SECRET_KEY - change in production!")
    
    if settings.JWT_SECRET == "dev_jwt_secret_change_me":
        warnings.append("Using default JWT_SECRET - change in production!")
    
    if warnings:
        logger.warning("⚠️  Environment warnings:")
        for warning in warnings:
            logger.warning(f"  • {warning}")
    
    if errors:
        logger.error("=" * 70)
        logger.error("CRITICAL: Environment validation failed!")
        logger.error("=" * 70)
        for error in errors:
            logger.error(f"  ✗ {error}")
        logger.error("=" * 70)
        logger.error("Fix: Create .env file with required variables")
        logger.error("See .env.example for template")
        logger.error("=" * 70)
        # Don't crash, but warn loudly
    else:
        logger.info("✓ Environment validation passed")
    
    # Initialize database
    try:
        # Create all database tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}", exc_info=True)
        raise
    
    logger.info(f"Application started successfully (version: {get_version()})")
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")


# Create FastAPI application
app = FastAPI(
    title="Agentic Compliance API",
    description="AI-powered compliance decision engine with agentic capabilities",
    version=get_version(),
    lifespan=lifespan,
)

# Register global exception handlers
register_exception_handlers(app)

# Register rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_handler)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS or ["http://localhost:8501"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request ID middleware for traceability
async def add_request_id_middleware(request, call_next):
    request.state.request_id = str(uuid.uuid4())
    response = await call_next(request)
    response.headers["X-Request-ID"] = request.state.request_id
    return response


app.add_middleware(BaseHTTPMiddleware, dispatch=add_request_id_middleware)


import os


@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    Returns application status, version, and component health.
    """
    from sqlalchemy import text
    from datetime import datetime
    
    health_status = {
        "status": "healthy",
        "version": get_version(),
        "timestamp": datetime.utcnow().isoformat(),
        "components": {}
    }
    
    # Check database connectivity
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            result.fetchone()
        health_status["components"]["database"] = {
            "status": "healthy",
            "type": "sqlite" if "sqlite" in str(engine.url) else "postgresql"
        }
    except Exception as e:
        health_status["status"] = "degraded"
        health_status["components"]["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    # Check LLM connectivity (optional fast path, default skipped to keep health fast/stable)
    skip_llm_health = os.getenv("SKIP_LLM_HEALTH", "1") == "1"
    if skip_llm_health:
        health_status["components"]["llm"] = {
            "status": "skipped",
            "key_present": bool(settings.OPENAI_API_KEY),
            "reason": "SKIP_LLM_HEALTH=1"
        }
    else:
        try:
            from backend.utils.llm_client import LLMClient
            llm_client = LLMClient()
            if not settings.OPENAI_API_KEY or str(settings.OPENAI_API_KEY).startswith("mock"):
                health_status["components"]["llm"] = {
                    "status": "not_configured",
                    "key_present": False
                }
            else:
                test_response = await llm_client.run_compliance_analysis_async(
                    prompt="health check",
                    use_json_schema=False,
                    timeout=5.0
                )
                test_dict = test_response.to_dict()
                if test_dict.get("status") == "completed":
                    health_status["components"]["llm"] = {
                        "status": "healthy",
                        "key_present": True,
                        "connectivity": "verified"
                    }
                else:
                    health_status["components"]["llm"] = {
                        "status": "degraded",
                        "key_present": True,
                        "connectivity": "failed",
                        "error": test_dict.get("error", "Unknown error")
                    }
                    health_status["status"] = "degraded"
        except Exception as e:
            health_status["components"]["llm"] = {
                "status": "unhealthy",
                "key_present": bool(settings.OPENAI_API_KEY),
                "error": str(e)
            }
            health_status["status"] = "degraded"
    
    # Check JWT configuration
    if settings.JWT_SECRET and settings.JWT_SECRET != "dev_jwt_secret_change_me":
        health_status["components"]["auth"] = {
            "status": "configured"
        }
    else:
        health_status["components"]["auth"] = {
            "status": "development_mode",
            "warning": "Using default JWT secret"
        }
    
    return health_status


@app.get("/")
def root():
    """Simple root endpoint for smoke checks"""
    return {"status": "running", "version": get_version()}


# Auth router (unversioned, used by frontend auth_client)
app.include_router(auth_router)

# Versioned API routers
app.include_router(query_router, prefix="/api/v1")  # /api/v1/query, /api/v1/queries, /api/v1/rules
app.include_router(decision_router, prefix="/api/v1")  # /api/v1/decision/*
app.include_router(entity_router, prefix="/api/v1")  # /api/v1/entity/*, /api/v1/audit_log/*
app.include_router(audit_router, prefix="/api/v1")  # /api/v1/audit/*
app.include_router(feedback_router, prefix="/api/v1")  # /api/v1/feedback/*
app.include_router(agentic_router, prefix="/api/v1")  # /api/v1/agentic/*

# Note: Route aliasing is handled directly in the router files using multiple decorators
# This provides better type safety and cleaner code organization


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
    )
