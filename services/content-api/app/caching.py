"""
Redis caching layer for performance optimization
"""
import json
import hashlib
from typing import Any, Optional, Dict, Callable
from functools import wraps
import redis.asyncio as redis
from datetime import timedelta
from app.config import settings
from app.logging_config import app_logger

class CacheManager:
    """Manages Redis cache operations"""
    
    def __init__(self):
        self.redis_client = None
        self.default_ttl = 3600  # 1 hour
        self.cache_stats = {
            "hits": 0,
            "misses": 0,
            "errors": 0
        }
    
    async def connect(self):
        """Connect to Redis"""
        try:
            self.redis_client = await redis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            await self.redis_client.ping()
            app_logger.logger.info("redis_connected", url=settings.redis_url)
        except Exception as e:
            app_logger.log_error("redis_connection_failed", str(e))
            self.redis_client = None
    
    async def disconnect(self):
        """Disconnect from Redis"""
        if self.redis_client:
            await self.redis_client.close()
    
    def _generate_cache_key(self, prefix: str, params: Dict[str, Any]) -> str:
        """Generate a unique cache key from parameters"""
        # Sort parameters for consistent key generation
        sorted_params = json.dumps(params, sort_keys=True)
        param_hash = hashlib.md5(sorted_params.encode()).hexdigest()
        return f"{prefix}:{param_hash}"
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self.redis_client:
            return None
        
        try:
            value = await self.redis_client.get(key)
            if value:
                self.cache_stats["hits"] += 1
                app_logger.logger.debug("cache_hit", key=key)
                return json.loads(value) if value else None
            else:
                self.cache_stats["misses"] += 1
                app_logger.logger.debug("cache_miss", key=key)
                return None
        except Exception as e:
            self.cache_stats["errors"] += 1
            app_logger.log_error("cache_get_error", str(e), key=key)
            return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """Set value in cache with TTL"""
        if not self.redis_client:
            return False
        
        try:
            ttl = ttl or self.default_ttl
            serialized = json.dumps(value)
            await self.redis_client.setex(key, ttl, serialized)
            app_logger.logger.debug("cache_set", key=key, ttl=ttl)
            return True
        except Exception as e:
            self.cache_stats["errors"] += 1
            app_logger.log_error("cache_set_error", str(e), key=key)
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete value from cache"""
        if not self.redis_client:
            return False
        
        try:
            result = await self.redis_client.delete(key)
            app_logger.logger.debug("cache_delete", key=key, deleted=result > 0)
            return result > 0
        except Exception as e:
            app_logger.log_error("cache_delete_error", str(e), key=key)
            return False
    
    async def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate all keys matching a pattern"""
        if not self.redis_client:
            return 0
        
        try:
            keys = await self.redis_client.keys(pattern)
            if keys:
                deleted = await self.redis_client.delete(*keys)
                app_logger.logger.info("cache_invalidated", pattern=pattern, count=deleted)
                return deleted
            return 0
        except Exception as e:
            app_logger.log_error("cache_invalidate_error", str(e), pattern=pattern)
            return 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total = self.cache_stats["hits"] + self.cache_stats["misses"]
        hit_rate = self.cache_stats["hits"] / max(total, 1)
        
        return {
            **self.cache_stats,
            "total_requests": total,
            "hit_rate": hit_rate
        }

# Global cache instance
cache_manager = CacheManager()

def cached(
    prefix: str = "cache",
    ttl: int = 3600,
    key_params: Optional[List[str]] = None
):
    """
    Decorator to cache function results
    
    Args:
        prefix: Cache key prefix
        ttl: Time to live in seconds
        key_params: List of parameter names to include in cache key
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            if key_params:
                cache_params = {k: v for k, v in kwargs.items() if k in key_params}
            else:
                # Use all kwargs for cache key
                cache_params = kwargs
            
            cache_key = cache_manager._generate_cache_key(prefix, cache_params)
            
            # Try to get from cache
            cached_result = await cache_manager.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Call the actual function
            result = await func(*args, **kwargs)
            
            # Cache the result
            await cache_manager.set(cache_key, result, ttl)
            
            return result
        
        return wrapper
    return decorator

class ContentCache:
    """Specialized cache for content generation"""
    
    def __init__(self):
        self.cache = cache_manager
        self.content_ttl = 3600  # 1 hour for generated content
        self.analytics_ttl = 300  # 5 minutes for analytics
    
    async def get_cached_content(
        self,
        product: str,
        persona: str,
        platform: str,
        tone: str
    ) -> Optional[Dict[str, Any]]:
        """Get cached generated content"""
        key = self.cache._generate_cache_key(
            "content",
            {
                "product": product,
                "persona": persona,
                "platform": platform,
                "tone": tone
            }
        )
        return await self.cache.get(key)
    
    async def cache_content(
        self,
        product: str,
        persona: str,
        platform: str,
        tone: str,
        content: Dict[str, Any]
    ):
        """Cache generated content"""
        key = self.cache._generate_cache_key(
            "content",
            {
                "product": product,
                "persona": persona,
                "platform": platform,
                "tone": tone
            }
        )
        await self.cache.set(key, content, self.content_ttl)
    
    async def get_cached_analytics(
        self,
        campaign_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get cached analytics data"""
        key = f"analytics:{campaign_id}"
        return await self.cache.get(key)
    
    async def cache_analytics(
        self,
        campaign_id: str,
        analytics_data: Dict[str, Any]
    ):
        """Cache analytics data"""
        key = f"analytics:{campaign_id}"
        await self.cache.set(key, analytics_data, self.analytics_ttl)
    
    async def invalidate_campaign(self, campaign_id: str):
        """Invalidate all cache entries for a campaign"""
        pattern = f"*{campaign_id}*"
        count = await self.cache.invalidate_pattern(pattern)
        app_logger.logger.info("campaign_cache_invalidated", campaign_id=campaign_id, count=count)

# Global content cache instance
content_cache = ContentCache()

class RateLimitCache:
    """Cache for rate limiting tracking"""
    
    def __init__(self):
        self.cache = cache_manager
    
    async def check_rate_limit(
        self,
        identifier: str,
        limit: int,
        window: int = 60
    ) -> Tuple[bool, int]:
        """
        Check if rate limit is exceeded
        Returns: (is_allowed, remaining_calls)
        """
        key = f"rate_limit:{identifier}"
        
        if not self.cache.redis_client:
            return True, limit  # Allow if Redis is down
        
        try:
            # Get current count
            current = await self.cache.redis_client.get(key)
            
            if current is None:
                # First request in window
                await self.cache.redis_client.setex(key, window, 1)
                return True, limit - 1
            
            current_count = int(current)
            
            if current_count >= limit:
                # Rate limit exceeded
                ttl = await self.cache.redis_client.ttl(key)
                return False, 0
            
            # Increment counter
            await self.cache.redis_client.incr(key)
            return True, limit - current_count - 1
            
        except Exception as e:
            app_logger.log_error("rate_limit_check_error", str(e))
            return True, limit  # Allow if error

# Global rate limit cache
rate_limit_cache = RateLimitCache()