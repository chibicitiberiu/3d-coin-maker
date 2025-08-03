"""
Compatibility layer for existing ApplicationContainer usage.

This module provides backward compatibility while we transition to
the new manual dependency injection system.
"""

import os
from config.factory import create_settings
from core.service_container import ServiceContainer

# Detect deployment mode from environment or running context
def _detect_mode() -> bool:
    """Detect if we're running in desktop mode."""
    # Check environment variable first
    if 'COIN_MAKER_DESKTOP_MODE' in os.environ:
        return os.environ['COIN_MAKER_DESKTOP_MODE'].lower() in ('true', '1', 'yes')
    
    # Check if APScheduler is in use (desktop mode indicator)
    # This is a heuristic - if APScheduler classes are loaded, we're likely in desktop mode
    import sys
    return any('apscheduler' in name for name in sys.modules)

# Create a global service container with environment-appropriate settings
# This maintains compatibility for both web and desktop deployments
_is_desktop = _detect_mode()
_container = ServiceContainer(create_settings(desktop_mode=_is_desktop))


class CompatibilityContainer:
    """Compatibility wrapper that mimics the old ApplicationContainer interface."""

    def coin_generation_service(self):
        return _container.get_coin_service()

    def task_queue(self):
        return _container.get_task_queue()

    def file_storage(self):
        return _container.get_file_storage()

    def settings(self):
        return _container.settings


# Global container instance for backward compatibility
container = CompatibilityContainer()


def initialize_task_queue():
    """Initialize the task queue - compatibility function."""
    return _container.initialize_task_queue()
