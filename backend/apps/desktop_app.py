"""
Desktop Application Implementation

Provides DesktopApp class for standalone desktop deployment mode.
This implementation is optimized for desktop use with APScheduler for
background tasks and desktop-specific configuration defaults.
"""

import logging

from config.factory import create_desktop_settings
from core.base_app import BaseApp
from core.service_container import ServiceContainer

logger = logging.getLogger(__name__)


class DesktopApp(BaseApp):
    """Desktop application implementation for standalone deployment."""

    def __init__(self, settings=None):
        """Initialize desktop application.

        Args:
            settings: Optional desktop settings instance. If not provided,
                     will create desktop-optimized settings during initialization.
        """
        super().__init__(settings)
        self._fastapi_app = None

    def load_config(self) -> None:
        """Load desktop-specific configuration."""
        if not self.settings:
            logger.info("Loading desktop application settings...")
            self.settings = create_desktop_settings()

        logger.info(f"Desktop app configured - Host: {self.settings.host}:{self.settings.port}")
        logger.info(f"APScheduler enabled (Celery disabled): {not self.settings.use_celery}")
        logger.info(f"Temp directory: {self.settings.temp_dir}")
        logger.info(f"File size limit: {self.settings.max_file_size_mb}MB")

    def initialize_services(self) -> None:
        """Initialize desktop-specific services."""
        if not self.settings:
            raise RuntimeError("Settings not loaded - call load_config() first")

        logger.info("Initializing desktop application services...")

        # Create service container with desktop settings
        self.services = ServiceContainer(self.settings)

        logger.info("Desktop application services initialized")

    def create_fastapi_app(self):
        """Create and configure FastAPI application for desktop mode."""
        if self._fastapi_app:
            return self._fastapi_app

        logger.info("Creating FastAPI application for desktop mode...")

        # Import here to avoid circular imports
        from app_factory import create_app

        # Create FastAPI app with desktop configuration and lifecycle integration
        self._fastapi_app = create_app(
            desktop_mode=True,
            base_app=self
        )

        logger.info("Desktop FastAPI application created")
        return self._fastapi_app

    def run(self) -> None:
        """Run the desktop application.

        Currently runs FastAPI server for the backend. In the future,
        this will integrate with Eel for the desktop GUI.
        """
        if not self.is_initialized:
            raise RuntimeError("Application not initialized - call initialize() first")

        logger.info("Starting desktop application...")
        self._running = True

        try:
            # Future: This is where Eel integration will go
            # For now, run FastAPI server for backend API
            self._run_backend_server()

        except KeyboardInterrupt:
            logger.info("Received shutdown signal")
        except Exception as e:
            logger.error(f"Error running desktop application: {e}")
            raise
        finally:
            self._running = False

    def _run_backend_server(self) -> None:
        """Run the backend FastAPI server."""
        import uvicorn

        # Create FastAPI app
        app = self.create_fastapi_app()

        logger.info(f"Starting desktop backend server on {self.settings.host}:{self.settings.port}")
        logger.info("Desktop app ready - access at http://localhost:8000")

        # Run Uvicorn server with desktop-optimized settings
        uvicorn.run(
            app,
            host=self.settings.host,
            port=self.settings.port,
            log_level="info" if self.settings.debug else "warning",
            access_log=self.settings.debug
        )

    def get_fastapi_app(self):
        """Get the FastAPI application instance.

        Useful for testing or when the app needs to be used by external
        ASGI servers.
        """
        if not self._fastapi_app:
            self._fastapi_app = self.create_fastapi_app()
        return self._fastapi_app

    def open_browser(self) -> None:
        """Open the default browser to the application URL.

        Useful for desktop mode to automatically open the app.
        """
        import time
        import webbrowser

        url = f"http://{self.settings.host}:{self.settings.port}"

        # Give the server a moment to start
        time.sleep(1)

        logger.info(f"Opening browser to {url}")
        webbrowser.open(url)
