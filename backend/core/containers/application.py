import os

import redis
from dependency_injector import containers, providers
from django.conf import settings

from core.services.apscheduler_task_queue import APSchedulerTaskQueue
from core.services.celery_task_queue import CeleryTaskQueue
from core.services.coin_generation_service import CoinGenerationService
from core.services.file_storage import FileSystemStorage
from core.services.hmm_manifold_generator import HMMManifoldGenerator
from core.services.image_processor import PILImageProcessor
from core.services.redis_rate_limiter import RedisRateLimiter


class ApplicationContainer(containers.DeclarativeContainer):
    """Application dependency injection container."""

    # Configuration
    config = providers.Configuration()

    # External resources
    redis_client = providers.Singleton(
        redis.from_url,
        url=settings.CELERY_BROKER_URL
    )

    # Core services
    file_storage = providers.Singleton(
        FileSystemStorage
    )

    image_processor = providers.Singleton(
        PILImageProcessor
    )

    # STL Generator - using HMM + Manifold3D for superior performance
    stl_generator = providers.Factory(
        HMMManifoldGenerator
    )

    rate_limiter = providers.Singleton(
        RedisRateLimiter,
        redis_client=redis_client
    )

    # Task Queue - conditionally provide Celery or APScheduler based on environment
    task_queue = providers.Singleton(
        CeleryTaskQueue if os.getenv('USE_CELERY', 'true').lower() in ('true', '1', 'yes', 'on')
        else APSchedulerTaskQueue
    )

    # High-level services
    coin_generation_service = providers.Singleton(
        CoinGenerationService,
        file_storage=file_storage,
        image_processor=image_processor,
        stl_generator=stl_generator,
        rate_limiter=rate_limiter
    )


# Global container instance
container = ApplicationContainer()


def initialize_task_queue():
    """Initialize the task queue and register task functions if using APScheduler."""
    # Only initialize APScheduler if we're not using Celery
    if os.getenv('USE_CELERY', 'true').lower() not in ('true', '1', 'yes', 'on'):
        task_queue = container.task_queue()
        
        # For APScheduler, register the task functions and start
        if isinstance(task_queue, APSchedulerTaskQueue):
            from core.services.task_functions import TASK_FUNCTIONS

            for task_name, task_func in TASK_FUNCTIONS.items():
                task_queue.register_task(task_name, task_func)

            # Start the scheduler
            task_queue.start()
        
        return task_queue
    else:
        # For Celery mode, don't instantiate the task queue during startup
        # Let it be lazily initialized when first used in API views
        return None
