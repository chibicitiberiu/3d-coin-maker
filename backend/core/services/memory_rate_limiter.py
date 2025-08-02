import time
from collections import defaultdict, deque
from threading import Lock
from typing import Dict, Deque

from constants import RateLimitConstants
from core.interfaces.rate_limiter import IRateLimiter

# Import settings
from fastapi_settings import settings


class MemoryRateLimiter(IRateLimiter):
    """In-memory implementation of IRateLimiter for APScheduler mode."""

    def __init__(self):
        """Initialize memory-based rate limiter."""
        self._hourly_data: Dict[str, Deque[float]] = defaultdict(deque)
        self._concurrent_data: Dict[str, int] = defaultdict(int)
        self._lock = Lock()

    def is_allowed(self, ip_address: str, operation_type: str) -> bool:
        """Check if operation is allowed for the IP address."""
        # Get limits from settings
        if operation_type == 'generation':
            hourly_limit = settings.max_generations_per_hour
            concurrent_limit = RateLimitConstants.DEFAULT_MAX_GENERATIONS  # Fixed concurrent limit
        else:
            # Default limits for other operations
            hourly_limit = RateLimitConstants.DEFAULT_MAX_GENERATIONS_BURST
            concurrent_limit = RateLimitConstants.DEFAULT_MAX_GENERATIONS

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
            hourly_limit = settings.max_generations_per_hour
        else:
            hourly_limit = RateLimitConstants.DEFAULT_MAX_GENERATIONS_BURST

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