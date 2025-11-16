"""
Caching Layer

Provides LRU and TTL caching for entity lookups and frequently accessed data.
"""

from functools import lru_cache, wraps
from typing import Dict, Any, Optional, Callable, TypeVar
from datetime import datetime, timedelta
from threading import Lock
import time

from src.core.config.config_provider import get_settings

T = TypeVar('T')


class TTLCache:
    """
    Time-to-Live cache with thread-safe operations.
    """
    
    def __init__(self, ttl_seconds: int = 300, max_size: int = 100):
        """
        Initialize TTL cache.
        
        Args:
            ttl_seconds: Time to live in seconds (default: 5 minutes)
            max_size: Maximum number of entries (default: 100)
        """
        self.ttl_seconds = ttl_seconds
        self.max_size = max_size
        self._cache: Dict[str, tuple[Any, float]] = {}
        self._lock = Lock()
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache if not expired.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found/expired
        """
        with self._lock:
            if key not in self._cache:
                return None
            
            value, expiry = self._cache[key]
            if time.time() > expiry:
                # Expired, remove it
                del self._cache[key]
                return None
            
            return value
    
    def set(self, key: str, value: Any) -> None:
        """
        Set value in cache with TTL.
        
        Args:
            key: Cache key
            value: Value to cache
        """
        with self._lock:
            # Remove oldest if at max size
            if len(self._cache) >= self.max_size and key not in self._cache:
                # Remove oldest entry (simple FIFO)
                oldest_key = next(iter(self._cache))
                del self._cache[oldest_key]
            
            expiry = time.time() + self.ttl_seconds
            self._cache[key] = (value, expiry)
    
    def clear(self) -> None:
        """Clear all cache entries"""
        with self._lock:
            self._cache.clear()
    
    def invalidate(self, key: str) -> None:
        """
        Invalidate a specific cache key.
        
        Args:
            key: Cache key to invalidate
        """
        with self._lock:
            self._cache.pop(key, None)


# Global cache instances
_entity_cache: Optional[TTLCache] = None
_analysis_cache: Optional[TTLCache] = None


def get_entity_cache() -> TTLCache:
    """Get or create entity cache instance"""
    global _entity_cache
    if _entity_cache is None:
        settings = get_settings()
        ttl = getattr(settings, 'cache_ttl_seconds', 300)
        max_size = getattr(settings, 'cache_max_size', 100)
        _entity_cache = TTLCache(ttl_seconds=ttl, max_size=max_size)
    return _entity_cache


def get_analysis_cache() -> TTLCache:
    """Get or create analysis cache instance"""
    global _analysis_cache
    if _analysis_cache is None:
        settings = get_settings()
        ttl = getattr(settings, 'cache_ttl_seconds', 300)
        max_size = getattr(settings, 'cache_max_size', 100)
        _analysis_cache = TTLCache(ttl_seconds=ttl, max_size=max_size)
    return _analysis_cache


def cached_entity_lookup(ttl_seconds: int = 300):
    """
    Decorator for caching entity lookups.
    
    Args:
        ttl_seconds: Cache TTL in seconds
    """
    def decorator(func: Callable) -> Callable:
        cache = TTLCache(ttl_seconds=ttl_seconds)
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key from arguments
            cache_key = f"{func.__name__}:{str(args)}:{str(sorted(kwargs.items()))}"
            
            # Check cache
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # Call function and cache result
            result = func(*args, **kwargs)
            cache.set(cache_key, result)
            return result
        
        return wrapper
    return decorator

