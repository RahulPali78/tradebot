"""Data caching utilities."""
from datetime import datetime, timedelta
from typing import Any, Optional, Dict, Tuple
import threading


class DataCache:
    """Thread-safe data cache with TTL."""
    
    def __init__(self, ttl_minutes: int = 5):
        """Initialize cache.
        
        Args:
            ttl_minutes: Cache TTL in minutes
        """
        self.ttl = timedelta(minutes=ttl_minutes)
        self._cache: Dict[str, Tuple[Any, datetime]] = {}
        self._lock = threading.RLock()
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if expired/missing
        """
        with self._lock:
            if key in self._cache:
                data, timestamp = self._cache[key]
                if datetime.now() - timestamp < self.ttl:
                    return data
                else:
                    del self._cache[key]
            return None
    
    def set(self, key: str, data: Any) -> None:
        """Set value in cache.
        
        Args:
            key: Cache key
            data: Value to cache
        """
        with self._lock:
            self._cache[key] = (data, datetime.now())
    
    def delete(self, key: str) -> bool:
        """Delete key from cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if key existed and was deleted
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
    
    def clear(self) -> None:
        """Clear all cached data."""
        with self._lock:
            self._cache.clear()
    
    def get_ttl_remaining(self, key: str) -> Optional[float]:
        """Get remaining TTL in seconds.
        
        Args:
            key: Cache key
            
        Returns:
            Remaining seconds or None if not cached
        """
        with self._lock:
            if key in self._cache:
                _, timestamp = self._cache[key]
                elapsed = datetime.now() - timestamp
                remaining = self.ttl - elapsed
                return max(0, remaining.total_seconds())
            return None
    
    def keys(self) -> list:
        """Get all cache keys."""
        with self._lock:
            return list(self._cache.keys())
    
    def __len__(self) -> int:
        """Get number of cached items."""
        with self._lock:
            return len(self._cache)
