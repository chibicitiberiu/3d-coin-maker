"""
Manual Dependency Injection Container

Replaces the dependency-injector library with a simple manual container
that provides proper dependency injection for services.
"""

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from core.interfaces.task_queue import TaskQueue

from core.services.apscheduler_task_queue import APSchedulerTaskQueue
from core.services.celery_task_queue import CeleryTaskQueue
from core.services.coin_generation_service import CoinGenerationService
from core.services.file_storage import FileSystemStorage
from core.services.hmm_manifold_generator import HMMManifoldGenerator
from core.services.image_processor import PILImageProcessor
from core.services.path_resolver import PathResolver
from core.services.smart_rate_limiter import SmartRateLimiter


class ServiceContainer:
    """Manual dependency injection container."""

    def __init__(self, settings):
        """Initialize container with settings."""
        self.settings = settings
        self._services: dict[str, Any] = {}

    def get_file_storage(self) -> FileSystemStorage:
        """Get file storage service."""
        if 'file_storage' not in self._services:
            self._services['file_storage'] = FileSystemStorage(
                temp_dir=self.settings.temp_dir
            )
        return self._services['file_storage']

    def get_image_processor(self) -> PILImageProcessor:
        """Get image processor service."""
        if 'image_processor' not in self._services:
            self._services['image_processor'] = PILImageProcessor()
        return self._services['image_processor']

    def get_stl_generator(self) -> HMMManifoldGenerator:
        """Get STL generator service."""
        if 'stl_generator' not in self._services:
            self._services['stl_generator'] = HMMManifoldGenerator(
                timeout_seconds=self.settings.hmm_timeout_seconds
            )
        return self._services['stl_generator']

    def get_rate_limiter(self) -> SmartRateLimiter:
        """Get rate limiter service."""
        if 'rate_limiter' not in self._services:
            # Inject configuration from settings
            self._services['rate_limiter'] = SmartRateLimiter(
                use_redis=self.settings.use_celery,
                redis_url=self.settings.redis_url if self.settings.use_celery else "",
                max_generations_per_hour=self.settings.max_generations_per_hour,
                max_concurrent_generations=self.settings.max_concurrent_generations,
                max_generations_burst=self.settings.max_generations_burst,
                cleanup_interval_seconds=self.settings.rate_limit_cleanup_interval_seconds
            )
        return self._services['rate_limiter']

    def get_task_queue(self) -> 'TaskQueue':
        """Get task queue service."""
        if 'task_queue' not in self._services:
            if self.settings.use_celery:
                self._services['task_queue'] = CeleryTaskQueue()
            else:
                self._services['task_queue'] = APSchedulerTaskQueue()
        return self._services['task_queue']

    def get_path_resolver(self) -> PathResolver:
        """Get path resolver service."""
        if 'path_resolver' not in self._services:
            self._services['path_resolver'] = PathResolver(
                desktop_mode=self.settings.is_desktop_mode(),
                temp_dir_setting=self.settings.temp_dir
            )
        return self._services['path_resolver']

    def get_coin_service(self) -> CoinGenerationService:
        """Get coin generation service."""
        if 'coin_service' not in self._services:
            self._services['coin_service'] = CoinGenerationService(
                file_storage=self.get_file_storage(),
                image_processor=self.get_image_processor(),
                stl_generator=self.get_stl_generator(),
                rate_limiter=self.get_rate_limiter()
            )
        return self._services['coin_service']

    def initialize_task_queue(self):
        """Initialize the task queue and register task functions if using APScheduler."""
        if not self.settings.use_celery:
            task_queue = self.get_task_queue()

            # For APScheduler, register the task functions and start
            if hasattr(task_queue, 'register_task'):
                from core.services.task_functions import TASK_FUNCTIONS

                for task_name, task_func in TASK_FUNCTIONS.items():
                    task_queue.register_task(task_name, task_func)

                # Start the scheduler
                task_queue.start()

            return task_queue
        else:
            # For Celery mode, don't instantiate the task queue during startup
            return None
