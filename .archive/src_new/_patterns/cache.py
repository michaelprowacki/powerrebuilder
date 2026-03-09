"""Caching System - Flexible caching for pipeline stages.

This module provides a unified caching system that can be used by all
pipeline stages to improve performance and avoid redundant processing.
"""

import hashlib
import json
import logging
import pickle
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Union

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Cache entry with metadata."""

    key: str
    value: Any
    timestamp: float
    ttl: Optional[float] = None
    hits: int = 0
    size: int = 0

    def is_expired(self) -> bool:
        """Check if entry has expired.

        Returns:
            True if expired
        """
        if self.ttl is None:
            return False
        return time.time() - self.timestamp > self.ttl


class CacheBackend(ABC):
    """Abstract cache backend."""

    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None
        """
        pass

    @abstractmethod
    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        """Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
        """
        pass

    @abstractmethod
    def delete(self, key: str) -> None:
        """Delete from cache.

        Args:
            key: Cache key
        """
        pass

    @abstractmethod
    def clear(self) -> None:
        """Clear all cache entries."""
        pass

    @abstractmethod
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics.

        Returns:
            Cache statistics
        """
        pass


class MemoryCache(CacheBackend):
    """In-memory cache backend."""

    def __init__(self, max_size: int = 1000):
        """Initialize memory cache.

        Args:
            max_size: Maximum number of entries
        """
        self.cache: Dict[str, CacheEntry] = {}
        self.max_size = max_size
        self.hits = 0
        self.misses = 0

    def get(self, key: str) -> Optional[Any]:
        """Get from memory cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None
        """
        entry = self.cache.get(key)

        if entry is None:
            self.misses += 1
            return None

        if entry.is_expired():
            del self.cache[key]
            self.misses += 1
            return None

        entry.hits += 1
        self.hits += 1
        return entry.value

    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        """Set in memory cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live
        """
        # Evict if at capacity
        if len(self.cache) >= self.max_size:
            self._evict_lru()

        # Calculate size
        try:
            size = len(pickle.dumps(value))
        except:
            size = 0

        self.cache[key] = CacheEntry(
            key=key,
            value=value,
            timestamp=time.time(),
            ttl=ttl,
            size=size,
        )

    def delete(self, key: str) -> None:
        """Delete from memory cache.

        Args:
            key: Cache key
        """
        self.cache.pop(key, None)

    def clear(self) -> None:
        """Clear memory cache."""
        self.cache.clear()
        self.hits = 0
        self.misses = 0

    def stats(self) -> Dict[str, Any]:
        """Get memory cache stats.

        Returns:
            Cache statistics
        """
        total_size = sum(e.size for e in self.cache.values())

        return {
            "entries": len(self.cache),
            "max_size": self.max_size,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": self.hits / (self.hits + self.misses)
            if (self.hits + self.misses) > 0
            else 0,
            "total_size_bytes": total_size,
        }

    def _evict_lru(self) -> None:
        """Evict least recently used entry."""
        if not self.cache:
            return

        # Find LRU entry
        lru_key = min(
            self.cache.keys(),
            key=lambda k: self.cache[k].timestamp + self.cache[k].hits * 60,
        )

        del self.cache[lru_key]


class DiskCache(CacheBackend):
    """Disk-based cache backend."""

    def __init__(self, cache_dir: Union[str, Path]):
        """Initialize disk cache.

        Args:
            cache_dir: Cache directory
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_file = self.cache_dir / ".cache_metadata.json"
        self.metadata = self._load_metadata()

    def get(self, key: str) -> Optional[Any]:
        """Get from disk cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None
        """
        file_path = self._get_cache_path(key)

        if not file_path.exists():
            return None

        # Check expiry
        meta = self.metadata.get(key, {})
        if meta.get("ttl"):
            if time.time() - meta["timestamp"] > meta["ttl"]:
                file_path.unlink()
                del self.metadata[key]
                self._save_metadata()
                return None

        # Load value
        try:
            with open(file_path, "rb") as f:
                return pickle.load(f)
        except Exception as e:
            logger.warning(f"Failed to load cache {key}: {e}")
            return None

    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        """Set in disk cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live
        """
        file_path = self._get_cache_path(key)

        try:
            with open(file_path, "wb") as f:
                pickle.dump(value, f)

            # Update metadata
            self.metadata[key] = {
                "timestamp": time.time(),
                "ttl": ttl,
                "size": file_path.stat().st_size,
            }
            self._save_metadata()

        except Exception as e:
            logger.warning(f"Failed to cache {key}: {e}")

    def delete(self, key: str) -> None:
        """Delete from disk cache.

        Args:
            key: Cache key
        """
        file_path = self._get_cache_path(key)

        if file_path.exists():
            file_path.unlink()

        self.metadata.pop(key, None)
        self._save_metadata()

    def clear(self) -> None:
        """Clear disk cache."""
        for file in self.cache_dir.glob("*.cache"):
            file.unlink()

        self.metadata.clear()
        self._save_metadata()

    def stats(self) -> Dict[str, Any]:
        """Get disk cache stats.

        Returns:
            Cache statistics
        """
        total_size = sum(m.get("size", 0) for m in self.metadata.values())

        return {
            "entries": len(self.metadata),
            "cache_dir": str(self.cache_dir),
            "total_size_bytes": total_size,
        }

    def _get_cache_path(self, key: str) -> Path:
        """Get cache file path for key.

        Args:
            key: Cache key

        Returns:
            Cache file path
        """
        # Hash key to avoid filesystem issues
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        return self.cache_dir / f"{key_hash}.cache"

    def _load_metadata(self) -> Dict[str, Dict]:
        """Load cache metadata.

        Returns:
            Metadata dictionary
        """
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file) as f:
                    return json.load(f)
            except:
                pass
        return {}

    def _save_metadata(self) -> None:
        """Save cache metadata."""
        try:
            with open(self.metadata_file, "w") as f:
                json.dump(self.metadata, f)
        except Exception as e:
            logger.warning(f"Failed to save metadata: {e}")


class HybridCache(CacheBackend):
    """Hybrid cache using memory and disk."""

    def __init__(self, cache_dir: Union[str, Path], memory_size: int = 100):
        """Initialize hybrid cache.

        Args:
            cache_dir: Disk cache directory
            memory_size: Memory cache size
        """
        self.memory = MemoryCache(memory_size)
        self.disk = DiskCache(cache_dir)

    def get(self, key: str) -> Optional[Any]:
        """Get from hybrid cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None
        """
        # Try memory first
        value = self.memory.get(key)
        if value is not None:
            return value

        # Try disk
        value = self.disk.get(key)
        if value is not None:
            # Promote to memory
            self.memory.set(key, value)

        return value

    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        """Set in hybrid cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live
        """
        # Set in both
        self.memory.set(key, value, ttl)
        self.disk.set(key, value, ttl)

    def delete(self, key: str) -> None:
        """Delete from hybrid cache.

        Args:
            key: Cache key
        """
        self.memory.delete(key)
        self.disk.delete(key)

    def clear(self) -> None:
        """Clear hybrid cache."""
        self.memory.clear()
        self.disk.clear()

    def stats(self) -> Dict[str, Any]:
        """Get hybrid cache stats.

        Returns:
            Cache statistics
        """
        return {
            "memory": self.memory.stats(),
            "disk": self.disk.stats(),
        }


class Cache:
    """High-level cache interface."""

    def __init__(self, backend: Optional[CacheBackend] = None):
        """Initialize cache.

        Args:
            backend: Cache backend to use
        """
        self.backend = backend or MemoryCache()
        self.enabled = True

    def get(self, key: str) -> Optional[Any]:
        """Get from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None
        """
        if not self.enabled:
            return None

        return self.backend.get(key)

    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        """Set in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
        """
        if not self.enabled:
            return

        self.backend.set(key, value, ttl)

    def delete(self, key: str) -> None:
        """Delete from cache.

        Args:
            key: Cache key
        """
        self.backend.delete(key)

    def clear(self) -> None:
        """Clear cache."""
        self.backend.clear()

    def stats(self) -> Dict[str, Any]:
        """Get cache statistics.

        Returns:
            Cache statistics
        """
        return self.backend.stats()

    def cache_key(self, *args, **kwargs) -> str:
        """Generate cache key from arguments.

        Args:
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Cache key
        """
        # Create unique key from arguments
        key_data = {
            "args": args,
            "kwargs": kwargs,
        }

        key_str = json.dumps(key_data, sort_keys=True, default=str)
        return hashlib.sha256(key_str.encode()).hexdigest()

    def cached(self, ttl: Optional[float] = None):
        """Decorator for caching function results.

        Args:
            ttl: Time to live in seconds

        Returns:
            Decorator function
        """

        def decorator(func):
            def wrapper(*args, **kwargs):
                # Generate cache key
                key = f"{func.__module__}.{func.__name__}:{self.cache_key(*args, **kwargs)}"

                # Try cache
                result = self.get(key)
                if result is not None:
                    logger.debug(f"Cache hit for {func.__name__}")
                    return result

                # Call function
                logger.debug(f"Cache miss for {func.__name__}")
                result = func(*args, **kwargs)

                # Cache result
                self.set(key, result, ttl)

                return result

            return wrapper

        return decorator

    def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate cache entries matching pattern.

        Args:
            pattern: Pattern to match (supports wildcards)

        Returns:
            Number of entries invalidated
        """
        count = 0

        if isinstance(self.backend, MemoryCache):
            import fnmatch

            keys_to_delete = [
                k for k in self.backend.cache.keys() if fnmatch.fnmatch(k, pattern)
            ]

            for key in keys_to_delete:
                self.delete(key)
                count += 1

        return count


# Global cache instance
_global_cache: Optional[Cache] = None


def get_cache() -> Cache:
    """Get global cache instance.

    Returns:
        Global cache
    """
    global _global_cache

    if _global_cache is None:
        _global_cache = Cache()

    return _global_cache


def set_cache(cache: Cache) -> None:
    """Set global cache instance.

    Args:
        cache: Cache to use globally
    """
    global _global_cache
    _global_cache = cache
