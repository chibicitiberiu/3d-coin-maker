from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
        """Initialize the DI container when Django starts."""
        from core.containers.application import container, initialize_task_queue

        # Wire the dependency injection
        container.wire(packages=['core', 'apps'])

        # Initialize the task queue (registers tasks if using APScheduler)
        try:
            initialize_task_queue()
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to initialize task queue: {str(e)}")
            # Don't raise - allow Django to start even if task queue fails
