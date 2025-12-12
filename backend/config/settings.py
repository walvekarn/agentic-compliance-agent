from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
import json
import warnings

# Suppress noisy .env parsing warnings from python-dotenv (malformed lines, etc.)
warnings.filterwarnings("ignore", category=UserWarning, module=r".*dotenv.*")


class Settings(BaseSettings):
    # Core secrets and API keys
    OPENAI_API_KEY: Optional[str] = None
    SECRET_KEY: str = "dev_secret_key_change_me"
    JWT_SECRET: str = "dev_jwt_secret_change_me"
    JWT_ALGORITHM: str = "HS256"

    # Auth/token durations
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Database
    DATABASE_URL: str = "sqlite:///./compliance.db"

    # CORS and server
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8501",
        "http://127.0.0.1:8501",
        "http://0.0.0.0:8501",
    ]
    DEBUG: bool = False
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000

    # Optional feature flags
    ENABLE_SIGNUP: bool = False

    # Caching Configuration
    CACHE_TTL_SECONDS: int = 300  # 5 minutes default
    CACHE_MAX_SIZE: int = 100  # Maximum cache entries
    
    # Local/demo bypass flag (dangerous outside dev)
    ALLOW_DEMO_USER: bool = False
    
    # ============================================================================
    # TIMEOUT CONFIGURATION
    # ============================================================================
    # All timeouts are in seconds. Frontend timeouts should be >= backend timeouts.
    # For agentic operations: Frontend >= Backend >= LLM call timeout
    # ============================================================================
    
    # Agentic Engine Timeouts (in seconds)
    # These values are tuned for LLM orchestration chains that require multiple API calls
    # Plan→Execute→Reflect loop typically needs 60-90 seconds total
    AGENTIC_OPERATION_TIMEOUT: int = 60  # Overall timeout for agentic operations
    AGENTIC_SECONDARY_TASK_TIMEOUT: int = 20  # Timeout for secondary tasks like reflection
    AGENTIC_LLM_CALL_TIMEOUT: int = 15  # Timeout for individual LLM calls in orchestrator (plan, execute, recommend)
    
    # API Client Timeouts
    API_DEFAULT_TIMEOUT: int = 30  # Default timeout for API calls
    API_LONG_OPERATION_TIMEOUT: int = 120  # For agentic/analysis operations
    
    # LLM Timeouts
    LLM_COMPLIANCE_TIMEOUT: int = 45  # For compliance analysis calls
    LLM_STANDARD_TIMEOUT: int = 30  # For standard LLM calls

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """
        Allow CORS origins to be provided as:
        - JSON array string
        - Comma-separated string
        - List[str]
        """
        if v is None:
            return []
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            v = v.strip()
            # Try JSON first
            if v.startswith("["):
                try:
                    parsed = json.loads(v)
                    if isinstance(parsed, list):
                        return parsed
                except json.JSONDecodeError:
                    pass
            # Fallback to comma separated
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",  # ignore unrelated env keys from other settings modules
    )


# Singleton settings instance
settings = Settings()

