"""
Desktop Service Container

Independent service container for desktop application that doesn't rely on
backend's compatibility layer. Creates its own services directly.
"""

import logging

logger = logging.getLogger(__name__)


class DesktopServiceContainer:
    """Desktop-specific service container with no backend dependencies."""

    def __init__(self, settings):
        """Initialize desktop service container with settings."""
        self.settings = settings
        self._services = {}
        self._task_queue = None

    def get_path_resolver(self):
        """Get path resolver service."""
        if 'path_resolver' not in self._services:
            # Import here to avoid circular imports
            from core.services.path_resolver import PathResolver
            self._services['path_resolver'] = PathResolver(desktop_mode=True, app_data_dir_setting=self.settings.app_data_dir)
        return self._services['path_resolver']

    def get_file_storage(self):
        """Get file storage service."""
        if 'file_storage' not in self._services:
            from core.services.file_storage import FileSystemStorage
            # Pass the desktop-mode PathResolver to FileStorage
            path_resolver = self.get_path_resolver()
            self._services['file_storage'] = FileSystemStorage(path_resolver_instance=path_resolver)
        return self._services['file_storage']

    def get_image_processor(self):
        """Get image processor service."""
        if 'image_processor' not in self._services:
            from core.services.image_processor import PILImageProcessor
            self._services['image_processor'] = PILImageProcessor()
        return self._services['image_processor']

    def get_hmm_manifold_generator(self):
        """Get HMM manifold generator service."""
        if 'hmm_generator' not in self._services:
            from core.services.hmm_manifold_generator import HMMManifoldGenerator
            self._services['hmm_generator'] = HMMManifoldGenerator(
                timeout_seconds=self.settings.hmm_timeout_seconds,
                hmm_binary_path=self.settings.hmm_binary_path
            )
        return self._services['hmm_generator']

    def get_coin_service(self):
        """Get coin generation service."""
        if 'coin_service' not in self._services:
            from core.services.coin_generation_service import CoinGenerationService
            # Create coin service with desktop-specific dependencies
            self._services['coin_service'] = CoinGenerationService(
                file_storage=self.get_file_storage(),
                image_processor=self.get_image_processor(),
                stl_generator=self.get_hmm_manifold_generator(),
                rate_limiter=self.get_rate_limiter(),
                task_queue=self.get_task_queue()
            )
        return self._services['coin_service']

    def get_rate_limiter(self):
        """Get rate limiter service - no limiting for desktop."""
        if 'rate_limiter' not in self._services:
            from .unlimited_rate_limiter import UnlimitedRateLimiter
            # Desktop has no rate limiting - allow unlimited generations
            self._services['rate_limiter'] = UnlimitedRateLimiter()
        return self._services['rate_limiter']

    def get_task_queue(self):
        """Get task queue service (APScheduler for desktop)."""
        if self._task_queue is None:
            from core.services.apscheduler_task_queue import APSchedulerTaskQueue
            self._task_queue = APSchedulerTaskQueue(max_workers=4)
        return self._task_queue

    def initialize_task_queue(self):
        """Initialize the task queue and register task functions."""
        logger.info("Initializing desktop task queue...")
        task_queue = self.get_task_queue()

        # Register the task functions for APScheduler
        if hasattr(task_queue, 'register_task'):
            from core.services.task_functions import TASK_FUNCTIONS
            
            for task_name, task_func in TASK_FUNCTIONS.items():
                task_queue.register_task(task_name, task_func)
                logger.debug(f"Registered task: {task_name}")

        # Start the scheduler
        if hasattr(task_queue, 'start'):
            task_queue.start()
            logger.info("Desktop task queue started with registered tasks")

        return task_queue

    def cleanup(self):
        """Clean up all services."""
        logger.info("Cleaning up desktop services...")

        # Clean up task queue
        if self._task_queue and hasattr(self._task_queue, 'shutdown'):
            self._task_queue.shutdown()

        # Clean up individual services if they have cleanup methods
        for service_name, service in self._services.items():
            if hasattr(service, 'cleanup'):
                try:
                    service.cleanup()
                    logger.debug(f"Cleaned up service: {service_name}")
                except Exception as e:
                    logger.error(f"Error cleaning up service {service_name}: {e}")
