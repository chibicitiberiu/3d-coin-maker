"""
Web Application Implementation

Provides WebApp class for web server deployment mode using FastAPI + Celery.
This implementation is optimized for production web deployment with Redis
for task queuing and rate limiting.
"""

import logging

from config.factory import create_web_settings
from core.base_app import BaseApp
from core.service_container import ServiceContainer

logger = logging.getLogger(__name__)


class WebApp(BaseApp):
    """Web application implementation for server deployment."""

    def __init__(self, settings=None):
        """Initialize web application.

        Args:
            settings: Optional web settings instance. If not provided,
                     will create web-optimized settings during initialization.
        """
        super().__init__(settings)
        self._fastapi_app = None

    def load_config(self) -> None:
        """Load web-specific configuration."""
        if not self.settings:
            logger.info("Loading web application settings...")
            self.settings = create_web_settings()

        logger.info(f"Web app configured - Host: {self.settings.host}:{self.settings.port}")
        logger.info(f"Celery enabled: {self.settings.use_celery}")
        logger.info(f"Redis URL: {self.settings.redis_url}")

    def initialize_services(self) -> None:
        """Initialize web-specific services."""
        if not self.settings:
            raise RuntimeError("Settings not loaded - call load_config() first")

        logger.info("Initializing web application services...")

        # Create service container with web settings
        self.services = ServiceContainer(self.settings)

        logger.info("Web application services initialized")

    def create_fastapi_app(self):
        """Create and configure FastAPI application."""
        if self._fastapi_app:
            return self._fastapi_app

        logger.info("Creating FastAPI application...")

        # Import here to avoid circular imports
        from app_factory import create_app

        # Create FastAPI app with web configuration and lifecycle integration
        self._fastapi_app = create_app(
            desktop_mode=False,
            base_app=self
        )

        logger.info("FastAPI application created")
        return self._fastapi_app

    def run(self) -> None:
        """Run the web application using Uvicorn."""
        if not self.is_initialized:
            raise RuntimeError("Application not initialized - call initialize() first")

        logger.info("Starting web application...")
        self._running = True

        try:
            import uvicorn

            # Create FastAPI app
            app = self.create_fastapi_app()

            logger.info(f"Starting Uvicorn server on {self.settings.host}:{self.settings.port}")

            # Run Uvicorn server
            uvicorn.run(
                app,
                host=self.settings.host,
                port=self.settings.port,
                log_level="info" if self.settings.debug else "warning"
            )

        except KeyboardInterrupt:
            logger.info("Received shutdown signal")
        except Exception as e:
            logger.error(f"Error running web application: {e}")
            raise
        finally:
            self._running = False

    def get_fastapi_app(self):
        """Get the FastAPI application instance.

        Useful for testing or when the app needs to be used by external
        ASGI servers like Gunicorn.
        """
        if not self._fastapi_app:
            self._fastapi_app = self.create_fastapi_app()
        return self._fastapi_app
