"""
Configuration Factory Functions

Provides factory functions for creating different types of settings instances
based on deployment mode and environment detection.
"""

from config.settings import Settings

from .desktop_settings import DesktopSettings


def create_web_settings() -> Settings:
    """Create settings instance optimized for web deployment."""
    return Settings()


def create_desktop_settings() -> DesktopSettings:
    """Create settings instance optimized for desktop deployment."""
    return DesktopSettings()


def create_settings(desktop_mode: bool | None = None) -> Settings | DesktopSettings:
    """Create settings instance based on mode detection or explicit parameter."""

    # Auto-detect desktop mode if not specified
    if desktop_mode is None:
        # Create a temporary settings instance to check environment indicators
        temp_settings = Settings()
        desktop_mode = temp_settings.should_use_desktop_mode()

    if desktop_mode:
        return create_desktop_settings()
    else:
        return create_web_settings()


# Backward compatibility - global settings instance
settings = create_settings()


# Helper functions for backward compatibility
def get_temp_dir():
    """Get temporary directory path."""
    return settings.temp_path


def is_debug() -> bool:
    """Check if debug mode is enabled."""
    return settings.debug


def get_secret_key() -> str:
    """Get secret key."""
    return settings.secret_key
