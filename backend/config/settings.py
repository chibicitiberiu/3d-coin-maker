"""
Base Settings Configuration

Provides the base Settings class with common configuration for the
Coin Maker application.
"""

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings using Pydantic."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Basic application settings
    debug: bool = Field(default=True, description="Enable debug mode")
    secret_key: str = Field(default="dev-secret-key-change-in-production", description="Secret key for security - must be set in environment")

    # Server settings
    host: str = Field(default="127.0.0.1", description="Server host")
    port: int = Field(default=8001, description="Server port")

    # CORS settings
    cors_origins: list[str] = Field(
        default=[
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ],
        description="Allowed CORS origins"
    )

    # File storage settings
    app_data_dir: str = Field(default="../data", description="Application data directory (contains settings, logs, generations, etc.)")
    max_file_size_mb: int = Field(default=50, description="Maximum upload file size in MB")
    file_cleanup_interval_minutes: int = Field(default=5, description="File cleanup interval in minutes")
    file_max_age_minutes: int = Field(default=30, description="Maximum age of temporary files in minutes")

    # Desktop mode detection settings
    desktop_mode: bool = Field(default=False, description="Desktop mode flag (enables PyWebView GUI and APScheduler)")

    # Rate limiting settings
    max_generations_per_hour: int = Field(default=20, description="Maximum generations per IP per hour")
    max_concurrent_generations: int = Field(default=10, description="Maximum concurrent generations")
    max_generations_burst: int = Field(default=100, description="Burst limit for rate limiting")
    rate_limit_window_hours: int = Field(default=1, description="Rate limit window in hours")
    rate_limit_cleanup_interval_seconds: int = Field(default=300, description="Rate limit cleanup interval in seconds")

    # Processing timeout settings (deployment-specific configuration)
    image_processing_timeout_seconds: int = Field(default=120, description="Image processing timeout")
    stl_generation_timeout_seconds: int = Field(default=300, description="STL generation timeout")

    # Task queue settings
    use_celery: bool = Field(default=True, description="Use Celery for task queue (False for APScheduler)")
    redis_url: str = Field(default="redis://localhost:6379/0", description="Redis connection URL")
    celery_broker_url: str | None = Field(default=None, description="Celery broker URL (defaults to redis_url)")
    celery_result_backend: str | None = Field(default=None, description="Celery result backend URL (defaults to redis_url)")

    # Background task settings
    max_task_retries: int = Field(default=3, description="Maximum task retry attempts")
    task_retry_delay_seconds: int = Field(default=60, description="Delay between task retries in seconds")

    # HMM settings
    hmm_timeout_seconds: int = Field(default=60, description="HMM operation timeout")
    hmm_binary_path: str | None = Field(default=None, description="Path to HMM binary (if not provided, will auto-detect)")

    @property
    def app_data_path(self) -> Path:
        """Get application data directory as Path object."""
        return Path(self.app_data_dir)

    @property
    def generations_path(self) -> Path:
        """Get generations subdirectory for file storage."""
        return self.app_data_path / "generations"

    @property
    def logs_path(self) -> Path:
        """Get logs subdirectory."""
        return self.app_data_path / "logs"

    @property
    def settings_path(self) -> Path:
        """Get settings subdirectory."""
        return self.app_data_path / "settings"

    @property
    def max_file_size_bytes(self) -> int:
        """Get max file size in bytes."""
        return self.max_file_size_mb * 1024 * 1024

    def is_desktop_mode(self) -> bool:
        """Check if running in desktop mode (APScheduler instead of Celery)."""
        return not self.use_celery

    def should_use_desktop_mode(self) -> bool:
        """Determine if desktop mode should be used based on environment indicators."""
        return self.desktop_mode or not self.use_celery

    def __init__(self, **kwargs):
        """Initialize settings with environment-specific defaults."""
        super().__init__(**kwargs)

        # Set Celery URLs if not specified
        if self.celery_broker_url is None:
            self.celery_broker_url = self.redis_url
        if self.celery_result_backend is None:
            self.celery_result_backend = self.redis_url
