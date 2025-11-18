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
    DEBUG: bool = True
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000

    # Optional feature flags
    ENABLE_SIGNUP: bool = False

    # Caching Configuration
    CACHE_TTL_SECONDS: int = 300  # 5 minutes default
    CACHE_MAX_SIZE: int = 100  # Maximum cache entries

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


