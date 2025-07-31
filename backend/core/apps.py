from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
        """Initialize the DI container when Django starts."""
        from core.containers.application import container
        container.wire(packages=['core', 'apps'])
