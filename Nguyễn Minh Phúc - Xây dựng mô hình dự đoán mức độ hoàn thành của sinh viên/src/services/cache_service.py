"""Caching service using Redis"""

import json
import redis
from typing import Any, Optional
from functools import wraps
import hashlib

class CacheService:
    """Redis-based caching service"""
    
    def __init__(self, host='localhost', port=6379, db=0, decode_responses=True):
        try:
            self.redis_client = redis.Redis(
                host=host, 
                port=port, 
                db=db, 
                decode_responses=decode_responses,
                socket_connect_timeout=1,
                socket_timeout=1
            )
            # Test connection
            self.redis_client.ping()
            self.enabled = True
            print("✅ Redis cache connected successfully")
        except (redis.ConnectionError, redis.TimeoutError):
            print("⚠️ Redis not available, caching disabled")
            self.redis_client = None
            self.enabled = False
    
    def _make_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate cache key from arguments"""
        key_data = f"{prefix}:{str(args)}:{str(sorted(kwargs.items()))}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self.enabled:
            return None
        
        try:
            value = self.redis_client.get(key)
            if value:
                return json.loads(value)
        except Exception as e:
            print(f"Cache get error: {e}")
        return None
    
    def set(self, key: str, value: Any, timeout: int = 300) -> bool:
        """Set value in cache with timeout (default 5 minutes)"""
        if not self.enabled:
            return False
        
        try:
            serialized = json.dumps(value, default=str)
            return self.redis_client.setex(key, timeout, serialized)
        except Exception as e:
            print(f"Cache set error: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if not self.enabled:
            return False
        
        try:
            return bool(self.redis_client.delete(key))
        except Exception as e:
            print(f"Cache delete error: {e}")
            return False
    
    def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching pattern"""
        if not self.enabled:
            return 0
        
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                return self.redis_client.delete(*keys)
        except Exception as e:
            print(f"Cache clear error: {e}")
        return 0
    
    def cache_result(self, prefix: str, timeout: int = 300):
        """Decorator to cache function results"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                if not self.enabled:
                    return func(*args, **kwargs)
                
                # Generate cache key
                cache_key = self._make_key(prefix, *args, **kwargs)
                
                # Try to get from cache
                cached_result = self.get(cache_key)
                if cached_result is not None:
                    return cached_result
                
                # Execute function and cache result
                result = func(*args, **kwargs)
                self.set(cache_key, result, timeout)
                return result
            
            return wrapper
        return decorator

# Global cache instance
cache = CacheService()

def cached_analytics(timeout: int = 300):
    """Decorator for caching analytics results"""
    return cache.cache_result("analytics", timeout)

def cached_student_data(timeout: int = 600):
    """Decorator for caching student data"""
    return cache.cache_result("student", timeout)

def cached_teacher_stats(timeout: int = 180):
    """Decorator for caching teacher statistics"""
    return cache.cache_result("teacher_stats", timeout)