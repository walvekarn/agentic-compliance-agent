"""Main FastAPI application entry point"""

import sys
import traceback
import json

try:
    import os
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
except Exception as e:
    print(f"❌ STARTUP ERROR: Failed to import dependencies")
    print(f"Error: {e}")
    traceback.print_exc()
    sys.exit(1)


def validate_environment():
    """Validate required environment variables with helpful messages."""
    errors = []
    
    # Check OpenAI API Key
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        errors.append("OPENAI_API_KEY is missing")
    elif openai_key == "your-openai-api-key-here":
        errors.append("OPENAI_API_KEY is still set to placeholder value")
    elif not openai_key.startswith("sk-"):
        errors.append("OPENAI_API_KEY appears invalid (should start with 'sk-')")
    
    # Check Secret Key
    secret_key = os.getenv("SECRET_KEY")
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
        print(f"Database URL: {os.getenv('DATABASE_URL', 'sqlite:///./compliance.db')}")
        Base.metadata.create_all(bind=engine)
        print("✅ Database initialized successfully")
    except Exception as e:
        print(f"❌ DATABASE ERROR: {e}")
        traceback.print_exc()
        raise
    yield
    # Shutdown: Clean up resources
    print("Shutting down application...")


# Initialize FastAPI app
app = FastAPI(
    title="Agentic Compliance Agent",
    description="AI-powered compliance agent using OpenAI GPT-4o-mini via LangChain",
    version="0.1.0",
    lifespan=lifespan,
)

# Configure CORS - SECURITY FIX: Using json.loads instead of eval
cors_origins_str = os.getenv("CORS_ORIGINS", '["http://localhost:3000", "http://localhost:8501", "http://127.0.0.1:8501", "http://0.0.0.0:8501"]')
try:
    allow_origins_list = json.loads(cors_origins_str) if isinstance(cors_origins_str, str) else cors_origins_str
except json.JSONDecodeError:
    # Fallback to safe default if JSON parsing fails
    allow_origins_list = ["http://localhost:8501"]
    print(f"⚠️ Warning: Could not parse CORS_ORIGINS, using default: {allow_origins_list}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api/v1")
app.include_router(decision_router, prefix="/api/v1")
app.include_router(audit_router, prefix="/api/v1")
app.include_router(entity_analysis_router, prefix="/api/v1")
app.include_router(feedback_router, prefix="/api/v1")
app.include_router(agentic_router, prefix="/api/v1/agentic")


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
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    debug = os.getenv("DEBUG", "True").lower() == "true"
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=debug,
    )

