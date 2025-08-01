"""
Task Function Implementations

Pure functions that contain the actual business logic for background tasks.
These functions can be executed by either Celery or APScheduler through
the TaskQueue interface, allowing for flexible deployment options.
"""

import logging
from collections.abc import Callable
from typing import Any

from core.interfaces.task_queue import ProgressCallback

logger = logging.getLogger(__name__)


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


def process_image_task_func(
    generation_id: str,
    parameters: dict[str, Any],
    progress_callback: ProgressCallback | None = None
) -> dict[str, Any]:
    """
    Process an uploaded image with the given parameters.

    This is the pure function version of the Celery process_image_task,
    extracted to work with both Celery and APScheduler implementations.

    Args:
        generation_id: Unique identifier for the generation session
        parameters: Image processing parameters (brightness, contrast, etc.)
        progress_callback: Optional callback for progress updates

    Returns:
        Dictionary with success status and generation details

    Raises:
        ProcessingError: For business logic errors (non-retryable)
        RetryableError: For transient errors that should be retried
    """
    try:
        # Import container inside function to avoid circular imports
        from core.containers.application import container
        coin_service = container.coin_generation_service()

        # Update progress
        if progress_callback:
            progress_callback.update(10, 'image_processing')

        logger.info(f"Processing image for generation {generation_id}")

        # Process the image
        success, error_msg = coin_service.process_image(generation_id, parameters)

        if not success:
            # Business logic failure - don't retry
            error_message = error_msg or "Image processing failed"
            logger.error(f"Image processing failed for {generation_id}: {error_message}")
            raise ProcessingError(error_message)

        # Update progress to completion
        if progress_callback:
            progress_callback.update(100, 'image_processed')

        logger.info(f"Successfully processed image for generation {generation_id}")

        return {
            'success': True,
            'generation_id': generation_id,
            'step': 'image_processed'
        }

    except ProcessingError:
        # Don't wrap business logic errors
        raise
    except Exception as exc:
        # Wrap unexpected errors as retryable
        logger.error(f"Unexpected error processing image for {generation_id}: {str(exc)}")
        raise RetryableError(f"Image processing failed: {str(exc)}") from exc


def generate_stl_task_func(
    generation_id: str,
    coin_parameters: dict[str, Any],
    progress_callback: ProgressCallback | None = None
) -> dict[str, Any]:
    """
    Generate an STL file from processed image data.

    This is the pure function version of the Celery generate_stl_task,
    extracted to work with both Celery and APScheduler implementations.

    Args:
        generation_id: Unique identifier for the generation session
        coin_parameters: Coin generation parameters (size, thickness, etc.)
        progress_callback: Optional callback for progress updates

    Returns:
        Dictionary with success status and generation details

    Raises:
        ProcessingError: For business logic errors (non-retryable)
        RetryableError: For transient errors that should be retried
    """
    try:
        # Import container inside function to avoid circular imports
        from core.containers.application import container
        coin_service = container.coin_generation_service()

        logger.info(f"Generating STL for generation {generation_id}")

        # Create progress wrapper that works with both callback types
        def progress_wrapper(progress: int, step: str):
            if progress_callback:
                progress_callback.update(progress, step)

        # Initial progress
        progress_wrapper(10, 'stl_generation_starting')

        # Generate STL with progress callback
        success, error_msg = coin_service.generate_stl(
            generation_id,
            coin_parameters,
            progress_wrapper
        )

        if not success:
            # Business logic failure - don't retry
            error_message = error_msg or "STL generation failed"
            logger.error(f"STL generation failed for {generation_id}: {error_message}")
            raise ProcessingError(error_message)

        # Final progress
        progress_wrapper(100, 'stl_generated')

        logger.info(f"Successfully generated STL for generation {generation_id}")

        return {
            'success': True,
            'generation_id': generation_id,
            'step': 'stl_generated'
        }

    except ProcessingError:
        # Don't wrap business logic errors
        raise
    except Exception as exc:
        # Wrap unexpected errors as retryable
        logger.error(f"Unexpected error generating STL for {generation_id}: {str(exc)}")
        raise RetryableError(f"STL generation failed: {str(exc)}") from exc


def cleanup_old_files_task_func(
    progress_callback: ProgressCallback | None = None
) -> dict[str, Any]:
    """
    Clean up old temporary files.

    This is the pure function version of the Celery cleanup_old_files_task,
    extracted to work with both Celery and APScheduler implementations.

    Args:
        progress_callback: Optional callback for progress updates

    Returns:
        Dictionary with cleanup results

    Raises:
        ProcessingError: For persistent cleanup errors
        RetryableError: For transient errors that should be retried
    """
    try:
        from django.conf import settings

        from core.containers.application import container

        logger.info("Starting file cleanup task")

        # Update progress
        if progress_callback:
            progress_callback.update(10, 'cleanup_starting')

        # Get file storage service
        file_storage = container.file_storage()

        # Perform cleanup
        if progress_callback:
            progress_callback.update(50, 'cleaning_files')

        deleted_count = file_storage.cleanup_old_files(settings.FILE_RETENTION)

        if progress_callback:
            progress_callback.update(100, 'cleanup_completed')

        logger.info(f"File cleanup completed: {deleted_count} files deleted")

        return {
            'success': True,
            'deleted_files': deleted_count,
            'message': f'Cleaned up {deleted_count} old files'
        }

    except Exception as exc:
        # For cleanup tasks, we want to retry transient errors but not fail permanently
        # Most cleanup errors are transient (permission issues, disk full, etc.)
        logger.error(f"File cleanup failed: {str(exc)}")

        # Return partial success rather than raising - cleanup failures shouldn't break the system
        return {
            'success': False,
            'deleted_files': 0,
            'error': f"Cleanup failed: {str(exc)}",
            'message': 'File cleanup encountered errors but will retry later'
        }


# Task registry for easy lookup
TASK_FUNCTIONS = {
    'process_image_task': process_image_task_func,
    'generate_stl_task': generate_stl_task_func,
    'cleanup_old_files_task': cleanup_old_files_task_func,
}


def get_task_function(task_name: str) -> Callable | None:
    """
    Get a task function by name.

    Args:
        task_name: Name of the task function

    Returns:
        Task function or None if not found
    """
    return TASK_FUNCTIONS.get(task_name)
