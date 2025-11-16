"""
Configuration Provider

Singleton accessor for application settings.
"""

from typing import Optional
from .settings import Settings

_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """
    Get or create settings singleton.
    
    Returns:
        Settings instance
    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reset_settings() -> None:
    """
    Reset settings (for testing).
    
    This allows tests to inject different settings.
    """
    global _settings
    _settings = None

