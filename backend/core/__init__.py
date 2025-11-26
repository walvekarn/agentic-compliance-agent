"""
Core Module

Provides core utilities including version management.
"""

from .version import get_version, get_version_info, __version__

__all__ = [
    "get_version",
    "get_version_info",
    "__version__",
]
