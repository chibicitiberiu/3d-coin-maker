"""
Configuration module for Coin Maker application.

This module provides settings management for different deployment modes
including web and desktop applications.
"""

from .desktop_settings import DesktopSettings
from .factory import create_desktop_settings, create_web_settings
from .settings import Settings

__all__ = [
    'Settings',
    'DesktopSettings',
    'create_web_settings',
    'create_desktop_settings'
]
