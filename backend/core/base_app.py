"""
Base Application Class

Provides abstract base class for application lifecycle management.
This enables proper separation between web and desktop deployment modes
while maintaining consistent initialization and shutdown patterns.
"""

import logging
from abc import ABC, abstractmethod

from core.service_container import ServiceContainer

logger = logging.getLogger(__name__)


class BaseApp(ABC):
    """Base application class handling lifecycle management."""

    def __init__(self, settings=None):
        """Initialize base application.

        Args:
            settings: Optional settings instance. If not provided, will be loaded
                     during initialization based on app type.
        """
        self.settings = settings
        self.services: ServiceContainer | None = None
        self._initialized = False
        self._running = False

    @abstractmethod
    def load_config(self) -> None:
        """Load application configuration.

        Each app type (web/desktop) should implement this to load
        appropriate settings for their deployment mode.
        """
        pass

    @abstractmethod
    def initialize_services(self) -> None:
        """Initialize all application services.

        Creates the service container and initializes all services
        with proper dependency injection.
        """
        pass

    def initialize(self) -> None:
        """Initialize the application.

        Performs the complete initialization sequence:
        1. Load configuration
        2. Initialize services
        3. Initialize task queue
        4. Setup cleanup tasks
        """
        if self._initialized:
            logger.info("Application already initialized")
            return

        logger.info("Initializing application...")

        self.load_config()
        self.initialize_services()
        self._initialize_task_queue()
        self._setup_cleanup_tasks()

        self._initialized = True
        logger.info("Application initialization complete")

    @abstractmethod
    def run(self) -> None:
        """Run the application.

        Each app type should implement this to start their specific
        runtime (FastAPI server, Eel desktop app, etc.).
        """
        pass

    def shutdown(self) -> None:
        """Shutdown the application.

        Performs cleanup of all services and resources.
        """
        if not self._initialized:
            return

        logger.info("Shutting down application...")

        self._cleanup_services()
        self._shutdown_task_queue()

        self._running = False
        self._initialized = False

        logger.info("Application shutdown complete")

    def _initialize_task_queue(self) -> None:
        """Initialize task queue based on settings."""
        if not self.services:
            raise RuntimeError("Services not initialized")

        logger.info("Initializing task queue...")

        # Initialize task queue (this will start APScheduler if needed)
        task_queue = self.services.initialize_task_queue()

        if task_queue:
            logger.info(f"Task queue initialized: {type(task_queue).__name__}")
        else:
            logger.info("Task queue initialization skipped (Celery mode)")

    def _setup_cleanup_tasks(self) -> None:
        """Setup periodic cleanup tasks."""
        if not self.services:
            return

        logger.info("Setting up cleanup tasks...")

        # For APScheduler mode, cleanup tasks are registered during task queue init
        # For Celery mode, cleanup tasks are handled by Celery beat
        if self.settings and not self.settings.use_celery:
            logger.info("Cleanup tasks setup complete (APScheduler mode)")
        else:
            logger.info("Cleanup tasks managed by Celery beat")

    def _cleanup_services(self) -> None:
        """Cleanup all services."""
        if not self.services:
            return

        logger.info("Cleaning up services...")

        # Clean up individual services if they have cleanup methods
        for service_name, service in self.services._services.items():
            if hasattr(service, 'cleanup'):
                try:
                    service.cleanup()
                    logger.debug(f"Cleaned up service: {service_name}")
                except Exception as e:
                    logger.error(f"Error cleaning up service {service_name}: {e}")

    def _shutdown_task_queue(self) -> None:
        """Shutdown task queue."""
        if not self.services:
            return

        logger.info("Shutting down task queue...")

        try:
            task_queue = self.services.get_task_queue()
            if hasattr(task_queue, 'shutdown'):
                task_queue.shutdown()
                logger.info("Task queue shutdown complete")
        except Exception as e:
            logger.error(f"Error shutting down task queue: {e}")

    @property
    def is_initialized(self) -> bool:
        """Check if application is initialized."""
        return self._initialized

    @property
    def is_running(self) -> bool:
        """Check if application is running."""
        return self._running

    @property
    def is_desktop_mode(self) -> bool:
        """Check if running in desktop mode."""
        return bool(self.settings and self.settings.is_desktop_mode())
