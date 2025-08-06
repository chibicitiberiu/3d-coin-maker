"""
Desktop Configuration Factory

Provides factory functions for creating desktop settings instances
with proper INI configuration loading.
"""

from config.config_loader import ConfigLoader
from config.settings import Settings

from .desktop_settings import DesktopSettings


def create_desktop_settings() -> DesktopSettings:
    """Create settings instance optimized for desktop deployment with INI config loading."""
    # Load configuration from INI files
    config_loader = ConfigLoader()
    ini_config = config_loader.load_config()

    # Create desktop settings with INI config applied
    return DesktopSettings(**ini_config)


def create_web_settings() -> Settings:
    """Create settings instance for web deployment (fallback from desktop)."""
    return Settings()
