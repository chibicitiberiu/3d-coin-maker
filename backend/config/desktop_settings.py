"""
Desktop Settings Configuration

Provides desktop-optimized settings for standalone application deployment.
"""

from pydantic import Field

from config.settings import Settings


class DesktopSettings(Settings):
    """Desktop-optimized settings for standalone application."""

    # Override defaults for desktop mode
    debug: bool = Field(default=False, description="Disable debug mode for production desktop app")

    # Task queue - force APScheduler for desktop
    use_celery: bool = Field(default=False, description="Desktop mode uses APScheduler")

    # CORS - allow all for desktop (no security concern in local app)
    cors_origins: list[str] = Field(
        default=["*"],
        description="Allow all origins for desktop app"
    )

    # Rate limiting - disabled for desktop use
    max_generations_per_hour: int = Field(default=999999, description="Unlimited generations for desktop")
    max_concurrent_generations: int = Field(default=50, description="Higher concurrent limit for desktop")
    max_generations_burst: int = Field(default=999999, description="Unlimited burst for desktop")
    rate_limit_cleanup_interval_seconds: int = Field(default=3600, description="Less frequent cleanup for desktop")

    # File storage - use local temp directory
    temp_dir: str = Field(default="./temp", description="Local temp directory for desktop")
    max_file_size_mb: int = Field(default=100, description="Larger file limit for desktop")

    # Cleanup - less aggressive for desktop
    file_cleanup_interval_minutes: int = Field(default=60, description="Cleanup every hour")
    file_max_age_minutes: int = Field(default=480, description="Keep files for 8 hours")

    # Server - localhost only for desktop
    host: str = Field(default="127.0.0.1", description="Localhost only for desktop")
    port: int = Field(default=8000, description="Standard port for desktop")

    # Processing timeouts - longer for desktop (no user waiting)
    image_processing_timeout_seconds: int = Field(default=300, description="Longer timeout for desktop")
    stl_generation_timeout_seconds: int = Field(default=600, description="Longer timeout for desktop")

    def is_desktop_mode(self) -> bool:
        """Desktop settings are always in desktop mode."""
        return True
