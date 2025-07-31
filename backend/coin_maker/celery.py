import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'coin_maker.settings')

app = Celery('coin_maker')
app.config_from_object('django.conf:settings', namespace='CELERY')

# Configure periodic tasks
app.conf.beat_schedule = {
    'cleanup-old-files': {
        'task': 'apps.processing.tasks.cleanup_old_files_task',
        'schedule': crontab(minute='*/5'),  # Every 5 minutes
    },
}
app.conf.timezone = 'UTC'

app.autodiscover_tasks()
