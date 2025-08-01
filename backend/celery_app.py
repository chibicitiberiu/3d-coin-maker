"""
Celery application configuration for FastAPI backend.

This module defines the Celery app instance and configures it for use with FastAPI,
replacing the Django-based Celery configuration.
"""

import os
from celery import Celery

# Import settings
from fastapi_settings import settings

# Create Celery app instance
app = Celery('coin_maker_fastapi')

# Configure Celery with settings from FastAPI
app.conf.update(
    broker_url=settings.celery_broker_url,
    result_backend=settings.celery_result_backend,
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_send_events=True,
    worker_send_task_events=True,
    
    # Task routing
    task_routes={
        'process_image_task': {'queue': 'celery'},
        'generate_stl_task': {'queue': 'celery'},
        'cleanup_old_files_task': {'queue': 'celery'},
    },
    
    # Task retry settings
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_default_retry_delay=settings.task_retry_delay_seconds,
    task_max_retries=settings.max_task_retries,
    
    # Task time limits
    task_soft_time_limit=300,  # 5 minutes
    task_time_limit=600,       # 10 minutes
    
    # Worker settings
    worker_disable_rate_limits=True,
    worker_pool_restarts=True,
)

# Import task functions and register them
from core.services.task_functions import (
    process_image_task_func,
    generate_stl_task_func,
    cleanup_old_files_task_func
)

@app.task(bind=True, name='process_image_task')
def process_image_task(self, generation_id: str, parameters: dict):
    """Process image task wrapper for Celery."""
    try:
        # Create progress callback using Celery's update_state
        class CeleryProgressCallback:
            def __init__(self, task):
                self.task = task
            
            def update(self, progress: int, step: str):
                self.task.update_state(
                    state='PROGRESS',
                    meta={'progress': progress, 'step': step}
                )
        
        progress_callback = CeleryProgressCallback(self)
        return process_image_task_func(generation_id, parameters, progress_callback)
    except Exception as exc:
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))

@app.task(bind=True, name='generate_stl_task')
def generate_stl_task(self, generation_id: str, coin_parameters: dict):
    """Generate STL task wrapper for Celery."""
    try:
        # Create progress callback using Celery's update_state
        class CeleryProgressCallback:
            def __init__(self, task):
                self.task = task
            
            def update(self, progress: int, step: str):
                self.task.update_state(
                    state='PROGRESS',
                    meta={'progress': progress, 'step': step}
                )
        
        progress_callback = CeleryProgressCallback(self)
        return generate_stl_task_func(generation_id, coin_parameters, progress_callback)
    except Exception as exc:
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))

@app.task(bind=True, name='cleanup_old_files_task')
def cleanup_old_files_task(self):
    """Cleanup old files task wrapper for Celery."""
    try:
        # Create progress callback using Celery's update_state
        class CeleryProgressCallback:
            def __init__(self, task):
                self.task = task
            
            def update(self, progress: int, step: str):
                self.task.update_state(
                    state='PROGRESS',
                    meta={'progress': progress, 'step': step}
                )
        
        progress_callback = CeleryProgressCallback(self)
        return cleanup_old_files_task_func(progress_callback)
    except Exception as exc:
        # Don't retry cleanup tasks too aggressively
        if self.request.retries < 2:
            raise self.retry(exc=exc, countdown=300)  # 5 minute delay
        return {'success': False, 'error': str(exc)}

if __name__ == '__main__':
    app.start()