"""
Compatibility layer for existing ApplicationContainer usage.

This module provides backward compatibility while we transition to
the new manual dependency injection system.
"""

from config.factory import settings
from core.service_container import ServiceContainer

# Create a global service container with current settings
# This maintains backward compatibility during the transition
_container = ServiceContainer(settings)


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
