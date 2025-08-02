import time
from collections import defaultdict, deque
from threading import Lock

from core.interfaces.rate_limiter import IRateLimiter


class MemoryRateLimiter(IRateLimiter):
    """In-memory implementation of IRateLimiter for APScheduler mode."""

    def __init__(self, max_generations_per_hour: int = 20, max_concurrent_generations: int = 10,
                 max_generations_burst: int = 100, cleanup_interval_seconds: int = 300):
        """Initialize memory-based rate limiter with configuration injection.

        Args:
            max_generations_per_hour: Maximum generations per IP per hour
            max_concurrent_generations: Maximum concurrent generations per IP
            max_generations_burst: Burst limit for rate limiting
            cleanup_interval_seconds: Cleanup interval in seconds
        """
        self._hourly_data: dict[str, deque[float]] = defaultdict(deque)
        self._concurrent_data: dict[str, int] = defaultdict(int)
        self._lock = Lock()
        self.max_generations_per_hour = max_generations_per_hour
        self.max_concurrent_generations = max_concurrent_generations
        self.max_generations_burst = max_generations_burst
        self.cleanup_interval_seconds = cleanup_interval_seconds

    def is_allowed(self, ip_address: str, operation_type: str) -> bool:
        """Check if operation is allowed for the IP address."""
        # Get limits from injected configuration
        if operation_type == 'generation':
            hourly_limit = self.max_generations_per_hour
            concurrent_limit = self.max_concurrent_generations
        else:
            # Default limits for other operations
            hourly_limit = self.max_generations_burst
            concurrent_limit = self.max_concurrent_generations

        with self._lock:
            # Check hourly limit
            if not self._check_hourly_limit(ip_address, operation_type, hourly_limit):
                return False

            # Check concurrent limit
            if not self._check_concurrent_limit(ip_address, operation_type, concurrent_limit):
                return False

        return True

    def record_operation(self, ip_address: str, operation_type: str) -> None:
        """Record an operation for rate limiting."""
        current_time = time.time()

        with self._lock:
            # Record for hourly tracking
            hourly_key = f"{ip_address}:{operation_type}:hourly"
            self._hourly_data[hourly_key].append(current_time)

            # Record for concurrent tracking
            concurrent_key = f"{ip_address}:{operation_type}:concurrent"
            self._concurrent_data[concurrent_key] += 1

    def get_remaining_quota(self, ip_address: str, operation_type: str) -> int:
        """Get remaining quota for IP address and operation type."""
        if operation_type == 'generation':
            hourly_limit = self.max_generations_per_hour
        else:
            hourly_limit = self.max_generations_burst

        with self._lock:
            current_count = self._get_hourly_count(ip_address, operation_type)
            return max(0, hourly_limit - current_count)

    def _check_hourly_limit(self, ip_address: str, operation_type: str, hourly_limit: int) -> bool:
        """Check if hourly limit is exceeded."""
        current_count = self._get_hourly_count(ip_address, operation_type)
        return current_count < hourly_limit

    def _get_hourly_count(self, ip_address: str, operation_type: str) -> int:
        """Get count of operations in the last hour."""
        current_time = time.time()
        one_hour_ago = current_time - 3600  # 1 hour in seconds

        hourly_key = f"{ip_address}:{operation_type}:hourly"
        timestamps = self._hourly_data[hourly_key]

        # Remove old entries
        while timestamps and timestamps[0] < one_hour_ago:
            timestamps.popleft()

        return len(timestamps)

    def _check_concurrent_limit(self, ip_address: str, operation_type: str, concurrent_limit: int) -> bool:
        """Check if concurrent limit is exceeded."""
        concurrent_key = f"{ip_address}:{operation_type}:concurrent"
        current_count = self._concurrent_data[concurrent_key]
        return current_count < concurrent_limit

    def release_operation(self, ip_address: str, operation_type: str) -> None:
        """Release a concurrent operation (for when operation completes)."""
        with self._lock:
            concurrent_key = f"{ip_address}:{operation_type}:concurrent"
            if self._concurrent_data[concurrent_key] > 0:
                self._concurrent_data[concurrent_key] -= 1
