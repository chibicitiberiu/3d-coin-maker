"""
Celery Worker Entry Point

Initializes services and configuration for Celery worker processes.
Workers are separate processes that need access to the same services.
"""

from apps.web_app import WebApp
from workers.celery_app import app as celery_app


def create_celery_worker_app():
    """Create and initialize app for Celery worker context."""
    # Create web app (Celery workers use same config as web)
    web_app = WebApp()
    web_app.initialize()

    # Get settings from the initialized app
    settings = web_app.settings

    # Configure Celery with settings from the service container
    # Note: broker_url and result_backend are already set in celery_app.py
    celery_app.conf.update(
        # Task retry settings from settings
        task_default_retry_delay=settings.task_retry_delay_seconds,
        task_max_retries=settings.max_task_retries,

        # Pass service container to task functions
        app_services=web_app.services
    )

    return web_app


# Initialize app when module is imported by Celery worker
worker_app = create_celery_worker_app()
