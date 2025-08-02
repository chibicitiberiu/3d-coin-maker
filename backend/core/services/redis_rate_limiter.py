import time

import redis

from constants import RateLimitConstants
from core.interfaces.rate_limiter import IRateLimiter

# Import settings
from fastapi_settings import settings


class RedisRateLimiter(IRateLimiter):
    """Redis implementation of IRateLimiter."""

    def __init__(self, redis_client: redis.Redis | None = None):
        if redis_client is None:
            redis_url = settings.redis_url
            self.redis_client = redis.from_url(redis_url)
        else:
            self.redis_client = redis_client

    def is_allowed(self, ip_address: str, operation_type: str) -> bool:
        """Check if operation is allowed for the IP address."""
        # Rate limiting always enabled in FastAPI version

        # Get limits from settings
        if operation_type == 'generation':
            hourly_limit = settings.max_generations_per_hour
            concurrent_limit = RateLimitConstants.DEFAULT_MAX_GENERATIONS  # Fixed concurrent limit
        else:
            # Default limits for other operations
            hourly_limit = RateLimitConstants.DEFAULT_MAX_GENERATIONS_BURST
            concurrent_limit = RateLimitConstants.DEFAULT_MAX_GENERATIONS

        # Check hourly limit
        if not self._check_hourly_limit(ip_address, operation_type, hourly_limit):
            return False

        # Check concurrent limit
        if not self._check_concurrent_limit(ip_address, operation_type, concurrent_limit):
            return False

        return True

    def record_operation(self, ip_address: str, operation_type: str) -> None:
        """Record an operation for rate limiting."""
        # Rate limiting always enabled in FastAPI version

        current_time = int(time.time())
        prefix = 'rate_limit'

        # Record for hourly limit
        hourly_key = f"{prefix}:hourly:{ip_address}:{operation_type}"
        pipe = self.redis_client.pipeline()
        pipe.zadd(hourly_key, {str(current_time): current_time})
        pipe.expire(hourly_key, RateLimitConstants.RATE_LIMIT_WINDOW_SECONDS)  # Expire after 1 hour
        pipe.execute()

        # Record for concurrent limit
        concurrent_key = f"{prefix}:concurrent:{ip_address}:{operation_type}"
        self.redis_client.sadd(concurrent_key, str(current_time))
        self.redis_client.expire(concurrent_key, RateLimitConstants.CLEANUP_INTERVAL_SECONDS)  # Expire after 5 minutes

    def get_remaining_quota(self, ip_address: str, operation_type: str) -> int:
        """Get remaining quota for IP address and operation type."""
        if operation_type == 'generation':
            hourly_limit = settings.max_generations_per_hour
        else:
            hourly_limit = RateLimitConstants.DEFAULT_MAX_GENERATIONS_BURST

        hourly_key = f"rate_limit:hourly:{ip_address}:{operation_type}"
        current_hour_start = int(time.time()) - RateLimitConstants.RATE_LIMIT_WINDOW_SECONDS

        # Count operations in the last hour
        operation_count = self.redis_client.zcount(
            hourly_key,
            current_hour_start,
            int(time.time())
        )
        current_count = int(operation_count) if isinstance(operation_count, int | str) else 0

        return max(0, hourly_limit - current_count)

    def _check_hourly_limit(self, ip_address: str, operation_type: str, limit: int) -> bool:
        """Check if IP is within hourly limit."""
        hourly_key = f"rate_limit:hourly:{ip_address}:{operation_type}"
        current_hour_start = int(time.time()) - RateLimitConstants.RATE_LIMIT_WINDOW_SECONDS

        # Remove old entries
        self.redis_client.zremrangebyscore(hourly_key, 0, current_hour_start)

        # Count current operations
        key_count = self.redis_client.zcard(hourly_key)
        current_count = int(key_count) if isinstance(key_count, int | str) else 0

        return current_count < limit

    def _check_concurrent_limit(self, ip_address: str, operation_type: str, limit: int) -> bool:
        """Check if IP is within concurrent limit."""
        concurrent_key = f"rate_limit:concurrent:{ip_address}:{operation_type}"
        scard_result = self.redis_client.scard(concurrent_key)
        current_count = int(scard_result) if isinstance(scard_result, int | str) else 0

        return current_count < limit
