from typing import Any

from celery import shared_task

from core.interfaces.task_queue import ProgressCallback
from core.services.task_functions import (
    ProcessingError,
    RetryableError,
    cleanup_old_files_task_func,
    generate_stl_task_func,
    process_image_task_func,
)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def process_image_task(
    self,
    generation_id: str,
    parameters: dict[str, Any]
):
    """Celery task for processing uploaded images."""

    # Create a progress callback that updates Celery task state
    def celery_progress_callback(progress: int, step: str, extra_data: dict | None = None):
        self.update_state(
            state='PROCESSING',
            meta={'step': step, 'progress': progress, **(extra_data or {})}
        )

    # Create progress callback wrapper
    progress_callback = ProgressCallback(
        task_id=self.request.id,
        update_func=lambda task_id, status, progress_data: celery_progress_callback(
            progress_data.get('progress', 0),
            progress_data.get('step', 'processing'),
            progress_data
        )
    )

    try:
        # Call the pure function
        return process_image_task_func(generation_id, parameters, progress_callback)

    except ProcessingError:
        # Don't retry business logic errors, just re-raise
        raise
    except RetryableError as exc:
        # For retryable errors, use Celery's retry mechanism
        if self.request.retries < self.max_retries:
            raise self.retry(
                exc=exc,
                countdown=60 * (2 ** self.request.retries),
                max_retries=self.max_retries
            ) from exc
        else:
            # Max retries reached, convert to non-retryable error
            raise ProcessingError(f"Task failed after {self.max_retries} retries: {str(exc)}") from exc
    except Exception as exc:
        # Convert unexpected exceptions to retryable errors
        raise RetryableError(str(exc)) from exc


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def generate_stl_task(
    self,
    generation_id: str,
    coin_parameters: dict[str, Any]
):
    """Celery task for generating STL files."""

    # Create a progress callback that updates Celery task state
    def celery_progress_callback(progress: int, step: str, extra_data: dict | None = None):
        self.update_state(
            state='PROCESSING',
            meta={'step': step, 'progress': progress, **(extra_data or {})}
        )

    # Create progress callback wrapper
    progress_callback = ProgressCallback(
        task_id=self.request.id,
        update_func=lambda task_id, status, progress_data: celery_progress_callback(
            progress_data.get('progress', 0),
            progress_data.get('step', 'processing'),
            progress_data
        )
    )

    try:
        # Call the pure function
        return generate_stl_task_func(generation_id, coin_parameters, progress_callback)

    except ProcessingError:
        # Don't retry business logic errors, just re-raise
        raise
    except RetryableError as exc:
        # For retryable errors, use Celery's retry mechanism
        if self.request.retries < self.max_retries:
            raise self.retry(
                exc=exc,
                countdown=60 * (2 ** self.request.retries),
                max_retries=self.max_retries
            ) from exc
        else:
            # Max retries reached, convert to non-retryable error
            raise ProcessingError(f"Task failed after {self.max_retries} retries: {str(exc)}") from exc
    except Exception as exc:
        # Convert unexpected exceptions to retryable errors
        raise RetryableError(str(exc)) from exc


@shared_task(bind=True, max_retries=2, default_retry_delay=300)
def cleanup_old_files_task(self):
    """Periodic task to clean up old files."""

    # Create a progress callback that updates Celery task state
    def celery_progress_callback(progress: int, step: str, extra_data: dict | None = None):
        self.update_state(
            state='PROCESSING',
            meta={'step': step, 'progress': progress, **(extra_data or {})}
        )

    # Create progress callback wrapper
    progress_callback = ProgressCallback(
        task_id=self.request.id,
        update_func=lambda task_id, status, progress_data: celery_progress_callback(
            progress_data.get('progress', 0),
            progress_data.get('step', 'processing'),
            progress_data
        )
    )

    try:
        # Call the pure function
        result = cleanup_old_files_task_func(progress_callback)

        # For cleanup tasks, always return the result even if it indicates failure
        # This prevents the periodic task from being marked as permanently failed
        return result

    except Exception as exc:
        # For cleanup tasks, retry with longer delay, then return partial failure
        if self.request.retries < self.max_retries:
            raise self.retry(
                exc=exc,
                countdown=300 * (2 ** self.request.retries),
                max_retries=self.max_retries
            ) from exc
        else:
            # Max retries reached - return failure result but don't raise
            # This allows periodic cleanup to continue running
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Cleanup task failed after {self.max_retries} retries: {str(exc)}")
            return {
                'success': False,
                'deleted_files': 0,
                'error': f"Cleanup failed after retries: {str(exc)}",
                'retries_exhausted': True
            }
