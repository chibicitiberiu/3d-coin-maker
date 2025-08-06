"""Unlimited rate limiter for desktop use - never limits anything."""

from core.interfaces.rate_limiter import IRateLimiter


class UnlimitedRateLimiter(IRateLimiter):
    """Rate limiter that never actually limits - for desktop use."""

    def is_allowed(self, ip_address: str, operation_type: str) -> bool:
        """Always allow operations in desktop mode."""
        return True

    def record_operation(self, ip_address: str, operation_type: str) -> None:
        """No-op - don't track operations in desktop mode."""
        pass

    def get_remaining_quota(self, ip_address: str, operation_type: str) -> int:
        """Always return unlimited quota."""
        return 999999