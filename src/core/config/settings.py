"""Configuration settings for the application"""

from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = True
    environment: str = "development"
    
    # OpenAI Configuration
    openai_api_key: str
    openai_model: str = "gpt-4o-mini"
    openai_max_tokens: int = 4096
    openai_temperature: float = 0.7
    
    # Database Configuration
    database_url: str = "sqlite:///./compliance.db"
    db_pool_size: int = 5
    db_max_overflow: int = 10
    db_pool_timeout: int = 30
    db_pool_recycle: int = 3600
    
    # Security
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # CORS Settings
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    
    # LangChain Settings
    langchain_tracing_v2: bool = False
    langchain_endpoint: str = "https://api.smith.langchain.com"
    langchain_api_key: str = ""
    langchain_project: str = "compliance-agent"
    
    # Caching Configuration
    cache_ttl_seconds: int = 300  # 5 minutes default
    cache_max_size: int = 100  # Maximum cache entries
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

