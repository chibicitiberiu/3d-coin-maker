from typing import Any

from celery import shared_task


class ProcessingError(Exception):
    """Custom exception for processing errors that should not be retried."""
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class RetryableError(Exception):
    """Custom exception for errors that should trigger a retry."""
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def process_image_task(
    self,
    generation_id: str,
    parameters: dict[str, Any]
):
    """Celery task for processing uploaded images."""
    try:
        # Import container inside task to avoid circular imports
        from core.containers.application import container
        coin_service = container.coin_generation_service()

        # Update task state
        self.update_state(
            state='PROCESSING',
            meta={'step': 'image_processing', 'progress': 10}
        )

        # Process the image
        success, error_msg = coin_service.process_image(generation_id, parameters)

        if not success:
            # Raise a non-retryable error for business logic failures
            raise ProcessingError(error_msg)

        # Update progress
        self.update_state(
            state='PROCESSING',
            meta={'step': 'image_processed', 'progress': 100}
        )

        return {
            'success': True,
            'generation_id': generation_id,
            'step': 'image_processed'
        }

    except ProcessingError:
        # Don't retry business logic errors, just re-raise
        raise
    except Exception as exc:
        # For unexpected errors, retry with exponential backoff
        if self.request.retries < self.max_retries:
            raise self.retry(
                exc=exc,
                countdown=60 * (2 ** self.request.retries),
                max_retries=self.max_retries
            )
        else:
            # Max retries reached, raise the original exception
            raise ProcessingError(f"Task failed after {self.max_retries} retries: {str(exc)}")


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def generate_stl_task(
    self,
    generation_id: str,
    coin_parameters: dict[str, Any]
):
    """Celery task for generating STL files."""
    try:
        # Import container inside task to avoid circular imports
        from core.containers.application import container
        coin_service = container.coin_generation_service()

        # Update task state
        self.update_state(
            state='PROCESSING',
            meta={'step': 'stl_generation', 'progress': 10}
        )

        # Generate STL
        success, error_msg = coin_service.generate_stl(generation_id, coin_parameters)

        if not success:
            # Raise a non-retryable error for business logic failures
            raise ProcessingError(error_msg)

        # Update progress
        self.update_state(
            state='PROCESSING',
            meta={'step': 'stl_generated', 'progress': 100}
        )

        return {
            'success': True,
            'generation_id': generation_id,
            'step': 'stl_generated'
        }

    except ProcessingError:
        # Don't retry business logic errors, just re-raise
        raise
    except Exception as exc:
        # For unexpected errors, retry with exponential backoff
        if self.request.retries < self.max_retries:
            raise self.retry(
                exc=exc,
                countdown=60 * (2 ** self.request.retries),
                max_retries=self.max_retries
            )
        else:
            # Max retries reached, raise the original exception
            raise ProcessingError(f"Task failed after {self.max_retries} retries: {str(exc)}")


@shared_task(bind=True, max_retries=2, default_retry_delay=300)
def cleanup_old_files_task(self):
    """Periodic task to clean up old files."""
    from django.conf import settings

    try:
        # Import container inside task to avoid circular imports
        from core.containers.application import container
        file_storage = container.file_storage()

        deleted_count = file_storage.cleanup_old_files(settings.FILE_RETENTION)
        return {
            'success': True,
            'deleted_files': deleted_count,
            'message': f'Cleaned up {deleted_count} old files'
        }
    except Exception as exc:
        # For cleanup tasks, retry once with a longer delay, then log and continue
        if self.request.retries < self.max_retries:
            raise self.retry(
                exc=exc,
                countdown=300 * (2 ** self.request.retries),
                max_retries=self.max_retries
            )
        else:
            # For periodic tasks, we don't want to fail completely - just log the error
            # This prevents the periodic task from being marked as failed permanently
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Cleanup task failed after {self.max_retries} retries: {str(exc)}")
            return {
                'success': False,
                'error': f"Cleanup failed after retries: {str(exc)}",
                'retries_exhausted': True
            }
