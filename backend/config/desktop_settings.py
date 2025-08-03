"""
Desktop Settings Configuration

Provides desktop-optimized settings for standalone application deployment.
"""

from pydantic import Field
try:
    from platformdirs import user_data_dir
except ImportError:
    # Fallback implementation if platformdirs is not available
    import os
    import platform
    
    def user_data_dir(appname: str, appauthor: str = None) -> str:
        """Simple fallback for platform-specific data directories."""
        system = platform.system()
        home = os.path.expanduser("~")
        
        if system == "Windows":
            # Windows: %APPDATA%\appname
            appdata = os.environ.get("APPDATA", os.path.join(home, "AppData", "Roaming"))
            return os.path.join(appdata, appname)
        elif system == "Darwin":
            # macOS: ~/Library/Application Support/appname
            return os.path.join(home, "Library", "Application Support", appname)
        else:
            # Linux/Unix: ~/.local/share/appname
            return os.path.join(home, ".local", "share", appname)

from config.settings import Settings


class DesktopSettings(Settings):
    """Desktop-optimized settings for standalone application."""

    # Override defaults for desktop mode
    debug: bool = Field(default=True, description="Enable debug mode for desktop development")

    # Task queue - force APScheduler for desktop
    use_celery: bool = Field(default=False, description="Desktop mode uses APScheduler")

    # CORS - allow localhost origins for dual-server desktop architecture
    cors_origins: list[str] = Field(
        default=[
            "http://localhost:5173",  # SvelteKit dev server
            "http://localhost:5174",  # Alternative SvelteKit port
            "http://127.0.0.1:5173",  # IPv4 localhost
            "http://127.0.0.1:5174",  # Alternative IPv4 localhost
            "http://localhost:*",     # Any localhost port (for dynamic allocation)
            "http://127.0.0.1:*",     # Any 127.0.0.1 port (for dynamic allocation)
        ],
        description="Allow localhost origins for dual-server desktop architecture"
    )

    # Rate limiting - disabled for desktop use
    max_generations_per_hour: int = Field(default=999999, description="Unlimited generations for desktop")
    max_concurrent_generations: int = Field(default=50, description="Higher concurrent limit for desktop")
    max_generations_burst: int = Field(default=999999, description="Unlimited burst for desktop")
    rate_limit_cleanup_interval_seconds: int = Field(default=3600, description="Less frequent cleanup for desktop")

    # File storage - use platform-specific user data directory
    app_data_dir: str = Field(
        default_factory=lambda: user_data_dir("coin-maker", "coin-maker"),
        description="Platform-specific app data directory for desktop (Windows: %APPDATA%/coin-maker, macOS: ~/Library/Application Support/coin-maker, Linux: ~/.local/share/coin-maker)"
    )
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
