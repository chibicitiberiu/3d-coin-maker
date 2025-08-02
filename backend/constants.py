"""Application-wide constants for Coin Maker backend."""


class ValidationConstants:
    """Constants for input validation."""

    # File size limits
    MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024  # 50MB
    MAX_FILENAME_LENGTH = 255

    # Image processing limits
    BRIGHTNESS_MIN = -100
    BRIGHTNESS_MAX = 100
    CONTRAST_MIN = 0
    CONTRAST_MAX = 300

    # Coin parameter defaults
    DEFAULT_DIAMETER = 30.0
    DEFAULT_THICKNESS = 3.0
    DEFAULT_RELIEF_DEPTH = 1.0


class RateLimitConstants:
    """Constants for rate limiting."""

    # Rate limiting defaults
    DEFAULT_MAX_GENERATIONS = 10
    DEFAULT_MAX_GENERATIONS_BURST = 100
    RATE_LIMIT_WINDOW_SECONDS = 3600  # 1 hour
    CLEANUP_INTERVAL_SECONDS = 300    # 5 minutes


class ProcessingConstants:
    """Constants for image and STL processing."""

    # Chunk sizes for file operations
    FILE_CHUNK_SIZE = 8192  # 8KB

    # Timeout values
    DEFAULT_TASK_TIMEOUT = 300  # 5 minutes
