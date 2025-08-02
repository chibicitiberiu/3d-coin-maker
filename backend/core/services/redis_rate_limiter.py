import time

import redis

from core.interfaces.rate_limiter import IRateLimiter


class RedisRateLimiter(IRateLimiter):
    """Redis implementation of IRateLimiter."""

    def __init__(self, redis_client: redis.Redis, max_generations_per_hour: int = 20,
                 max_concurrent_generations: int = 10, max_generations_burst: int = 100,
                 cleanup_interval_seconds: int = 300):
        """Initialize Redis-based rate limiter with configuration injection.

        Args:
            redis_client: Redis client instance
            max_generations_per_hour: Maximum generations per IP per hour
            max_concurrent_generations: Maximum concurrent generations per IP
            max_generations_burst: Burst limit for rate limiting
            cleanup_interval_seconds: Cleanup interval in seconds
        """
        self.redis_client = redis_client
        self.max_generations_per_hour = max_generations_per_hour
        self.max_concurrent_generations = max_concurrent_generations
        self.max_generations_burst = max_generations_burst
        self.cleanup_interval_seconds = cleanup_interval_seconds

    def is_allowed(self, ip_address: str, operation_type: str) -> bool:
        """Check if operation is allowed for the IP address."""
        # Rate limiting always enabled in FastAPI version

        # Get limits from injected configuration
        if operation_type == 'generation':
            hourly_limit = self.max_generations_per_hour
            concurrent_limit = self.max_concurrent_generations
        else:
            # Default limits for other operations
            hourly_limit = self.max_generations_burst
            concurrent_limit = self.max_concurrent_generations

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
        pipe.expire(hourly_key, 3600)  # Expire after 1 hour
        pipe.execute()

        # Record for concurrent limit
        concurrent_key = f"{prefix}:concurrent:{ip_address}:{operation_type}"
        self.redis_client.sadd(concurrent_key, str(current_time))
        self.redis_client.expire(concurrent_key, self.cleanup_interval_seconds)  # Expire after cleanup interval

    def get_remaining_quota(self, ip_address: str, operation_type: str) -> int:
        """Get remaining quota for IP address and operation type."""
        if operation_type == 'generation':
            hourly_limit = self.max_generations_per_hour
        else:
            hourly_limit = self.max_generations_burst

        hourly_key = f"rate_limit:hourly:{ip_address}:{operation_type}"
        current_hour_start = int(time.time()) - 3600  # 1 hour in seconds

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
        current_hour_start = int(time.time()) - 3600  # 1 hour in seconds

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
