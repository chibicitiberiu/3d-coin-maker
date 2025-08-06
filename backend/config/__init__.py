"""
Configuration module for Coin Maker application.

This module provides settings management for different deployment modes
including web and desktop applications.
"""

from .factory import create_web_settings
from .settings import Settings

__all__ = [
    'Settings',
    'create_web_settings'
]
