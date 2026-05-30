"""
Compatibility layer for existing ApplicationContainer usage.

This module provides backward compatibility while we transition to
the new manual dependency injection system.
"""

from config.factory import create_web_settings
from core.service_container import ServiceContainer

# Create a global service container with environment-appropriate settings
# This maintains compatibility for both web and desktop deployments
_container = ServiceContainer(create_web_settings())


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

    def inject_desktop_path_resolver(self, path_resolver):
        """Allow desktop module to inject its PathResolver for background tasks."""
        _container._services['path_resolver'] = path_resolver


# Global container instance for backward compatibility
container = CompatibilityContainer()


def initialize_task_queue():
    """Initialize the task queue - compatibility function."""
    return _container.initialize_task_queue()
