import os
import time
from typing import Optional

import redis

from constants import RateLimitConstants
from core.interfaces.rate_limiter import IRateLimiter
from core.services.memory_rate_limiter import MemoryRateLimiter
from core.services.redis_rate_limiter import RedisRateLimiter

# Import settings
from fastapi_settings import settings


class SmartRateLimiter(IRateLimiter):
    """Smart rate limiter that automatically chooses Redis or Memory based on environment and availability."""

    def __init__(self):
        """Initialize smart rate limiter with automatic fallback."""
        self._rate_limiter = None
        self._redis_available = False
        
        # Check if we should use Celery (which implies Redis availability)
        use_celery = getattr(settings, 'use_celery', os.getenv('USE_CELERY', 'true').lower() in ('true', '1', 'yes', 'on'))
        
        
        if use_celery:
            try:
                # Try to initialize Redis rate limiter
                redis_url = getattr(settings, 'redis_url', getattr(settings, 'CELERY_BROKER_URL', 'redis://localhost:6379/0'))
                redis_client = redis.from_url(redis_url)
                
                # Test Redis connection
                redis_client.ping()
                self._rate_limiter = RedisRateLimiter(redis_client)
                self._redis_available = True
            except (redis.ConnectionError, redis.TimeoutError, Exception) as e:
                self._rate_limiter = MemoryRateLimiter()
                self._redis_available = False
        else:
            self._rate_limiter = MemoryRateLimiter()
            self._redis_available = False

    def is_allowed(self, ip_address: str, operation_type: str) -> bool:
        """Check if operation is allowed for the IP address."""
        return self._rate_limiter.is_allowed(ip_address, operation_type)

    def record_operation(self, ip_address: str, operation_type: str) -> None:
        """Record an operation for rate limiting."""
        self._rate_limiter.record_operation(ip_address, operation_type)

    def get_remaining_quota(self, ip_address: str, operation_type: str) -> int:
        """Get remaining quota for IP address and operation type."""
        return self._rate_limiter.get_remaining_quota(ip_address, operation_type)

    @property
    def is_redis_available(self) -> bool:
        """Check if Redis is available."""
        return self._redis_available