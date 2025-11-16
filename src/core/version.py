"""
Unified Version Management

Single source of truth for version information.
"""

__version__ = "1.3.0-agentic-hardened"
__version_info__ = (1, 3, 0, "agentic-hardened")


def get_version() -> str:
    """
    Get current version string.
    
    Returns:
        Version string (e.g., "1.3.0-agentic-hardened")
    """
    return __version__


def get_version_info() -> tuple:
    """
    Get version info tuple.
    
    Returns:
        Tuple of (major, minor, patch, suffix)
    """
    return __version_info__


def get_major_version() -> int:
    """Get major version number"""
    return __version_info__[0]


def get_minor_version() -> int:
    """Get minor version number"""
    return __version_info__[1]


def get_patch_version() -> int:
    """Get patch version number"""
    return __version_info__[2]


def get_version_suffix() -> str:
    """Get version suffix"""
    return __version_info__[3] if len(__version_info__) > 3 else ""

