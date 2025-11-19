"""
Main FastAPI Application
========================
Entry point for the Agentic Compliance API backend.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Handles startup and shutdown events.
    """
    # Startup: Initialize database
    logger.info("Starting up application...")
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
    
    # Check OpenAI API key (optional)
    openai_key = settings.OPENAI_API_KEY
    if openai_key:
        health_status["components"]["openai"] = {
            "status": "configured",
            "key_present": True
        }
    else:
        health_status["components"]["openai"] = {
            "status": "not_configured",
            "key_present": False,
            "note": "Agentic features will use mock mode"
        }
    
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
