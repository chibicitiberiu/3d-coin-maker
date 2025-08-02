
import redis

from core.interfaces.rate_limiter import IRateLimiter
from core.services.memory_rate_limiter import MemoryRateLimiter
from core.services.redis_rate_limiter import RedisRateLimiter


class SmartRateLimiter(IRateLimiter):
    """Smart rate limiter that automatically chooses Redis or Memory based on environment and availability."""

    def __init__(self, use_redis: bool = True, redis_url: str = "redis://localhost:6379/0",
                 max_generations_per_hour: int = 20, max_concurrent_generations: int = 10,
                 max_generations_burst: int = 100, cleanup_interval_seconds: int = 300):
        """Initialize smart rate limiter with configuration injection.

        Args:
            use_redis: Whether to use Redis or fall back to memory
            redis_url: Redis connection URL (if using Redis)
            max_generations_per_hour: Maximum generations per IP per hour
            max_concurrent_generations: Maximum concurrent generations per IP
            max_generations_burst: Burst limit for rate limiting
            cleanup_interval_seconds: Cleanup interval in seconds
        """
        self._rate_limiter: IRateLimiter
        self._redis_available = False
        self.max_generations_per_hour = max_generations_per_hour
        self.max_concurrent_generations = max_concurrent_generations
        self.max_generations_burst = max_generations_burst
        self.cleanup_interval_seconds = cleanup_interval_seconds

        if use_redis:
            try:
                # Try to initialize Redis rate limiter
                redis_client = redis.from_url(redis_url)

                # Test Redis connection
                redis_client.ping()
                self._rate_limiter = RedisRateLimiter(
                    redis_client=redis_client,
                    max_generations_per_hour=self.max_generations_per_hour,
                    max_concurrent_generations=self.max_concurrent_generations,
                    max_generations_burst=self.max_generations_burst,
                    cleanup_interval_seconds=self.cleanup_interval_seconds
                )
                self._redis_available = True
            except (redis.ConnectionError, redis.TimeoutError, Exception):
                self._rate_limiter = MemoryRateLimiter(
                    max_generations_per_hour=self.max_generations_per_hour,
                    max_concurrent_generations=self.max_concurrent_generations,
                    max_generations_burst=self.max_generations_burst,
                    cleanup_interval_seconds=self.cleanup_interval_seconds
                )
                self._redis_available = False
        else:
            # Fall back to memory rate limiter when not using Redis
            self._rate_limiter = MemoryRateLimiter(
                max_generations_per_hour=self.max_generations_per_hour,
                max_concurrent_generations=self.max_concurrent_generations,
                max_generations_burst=self.max_generations_burst,
                cleanup_interval_seconds=self.cleanup_interval_seconds
            )
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
