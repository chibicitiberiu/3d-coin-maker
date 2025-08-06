"""
Web Configuration Factory

Provides factory functions for creating web settings instances.
Desktop-specific factories are in desktop/config/factory.py
"""

from config.config_loader import ConfigLoader
from config.settings import Settings


def create_web_settings() -> Settings:
    """Create settings instance optimized for web deployment with INI config loading."""

    # Load configuration from INI files
    config_loader = ConfigLoader()
    ini_config = config_loader.load_config()

    # Create web settings with INI config applied
    return Settings(**ini_config)


# Backward compatibility - global settings instance
settings = create_web_settings()


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
