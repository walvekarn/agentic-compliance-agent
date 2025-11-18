"""
Core Module

Provides core utilities including version management, caching, and profiling.
"""

from .version import get_version, get_version_info, __version__
from .cache import TTLCache

# Profiling functions may not be available, import conditionally
try:
    from .profiling import profile_function
    __all__ = [
        "get_version",
        "get_version_info",
        "__version__",
        "TTLCache",
        "profile_function",
    ]
except ImportError:
    __all__ = [
        "get_version",
        "get_version_info",
        "__version__",
        "TTLCache",
    ]

