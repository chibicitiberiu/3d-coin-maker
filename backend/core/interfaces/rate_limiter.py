from abc import ABC, abstractmethod


class IRateLimiter(ABC):
    """Interface for rate limiting operations."""

    @abstractmethod
    def is_allowed(self, ip_address: str, operation_type: str) -> bool:
        """Check if operation is allowed for the IP address."""
        pass

    @abstractmethod
    def record_operation(self, ip_address: str, operation_type: str) -> None:
        """Record an operation for rate limiting."""
        pass

    @abstractmethod
    def get_remaining_quota(self, ip_address: str, operation_type: str) -> int:
        """Get remaining quota for IP address and operation type."""
        pass
