import redis
from dependency_injector import containers, providers
from django.conf import settings

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
