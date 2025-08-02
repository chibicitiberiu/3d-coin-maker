"""
Task Function Implementations

Pure functions that contain the actual business logic for background tasks.
These functions can be executed by either Celery or APScheduler through
the TaskQueue interface, allowing for flexible deployment options.
"""

import logging
from collections.abc import Callable

from core.interfaces.task_queue import ProgressCallbackProtocol
from core.models import (
    CleanupResponse,
    CoinParameters,
    ImageProcessingParameters,
    ProcessingError,
    RetryableError,
    TaskResponse,
)
from core.utils import create_image_processing_tracker, create_stl_generation_tracker

logger = logging.getLogger(__name__)


def process_image_task_func(
    generation_id: str,
    parameters: dict[str, str | int | float | bool],
    progress_callback: ProgressCallbackProtocol | None = None
) -> TaskResponse:
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
        from core.containers.compat import container
        coin_service = container.coin_generation_service()

        # Create progress tracker for this task
        progress = create_image_processing_tracker(progress_callback)
        progress.update_stage('start', 'Starting image processing')

        logger.info(f"Processing image for generation {generation_id}")

        # Convert dict to proper model
        image_params = ImageProcessingParameters.from_dict(parameters)

        progress.update_stage('loading_image', 'Loading and validating image')

        # Process the image
        coin_service.process_image(generation_id, image_params)

        progress.update_stage('complete', 'Image processing completed')

        logger.info(f"Successfully processed image for generation {generation_id}")

        return TaskResponse(
            success=True,
            generation_id=generation_id,
            step='image_processed'
        )

    except ProcessingError:
        # Don't wrap business logic errors
        raise
    except Exception as exc:
        # Wrap unexpected errors as retryable
        logger.error(f"Unexpected error processing image for {generation_id}: {str(exc)}")
        raise RetryableError(f"Image processing failed: {str(exc)}") from exc


def generate_stl_task_func(
    generation_id: str,
    coin_parameters: dict[str, str | float],
    progress_callback: ProgressCallbackProtocol | None = None
) -> TaskResponse:
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
        from core.containers.compat import container
        coin_service = container.coin_generation_service()

        # Create progress tracker for this task
        progress = create_stl_generation_tracker(progress_callback)
        progress.update_stage('start', 'Starting STL generation')

        logger.info(f"Generating STL for generation {generation_id}")

        # Convert dict to proper model
        coin_params = CoinParameters.from_dict(coin_parameters)

        progress.update_stage('loading_heightmap', 'Loading processed heightmap')

        # Create progress wrapper that works with the service
        def progress_wrapper(progress_val: int, step: str):
            progress.update_custom(progress_val, step)

        # Generate STL with progress callback
        coin_service.generate_stl(
            generation_id,
            coin_params,
            progress_wrapper
        )

        progress.update_stage('complete', 'STL generation completed')

        logger.info(f"Successfully generated STL for generation {generation_id}")

        return TaskResponse(
            success=True,
            generation_id=generation_id,
            step='stl_generated'
        )

    except ProcessingError:
        # Don't wrap business logic errors
        raise
    except Exception as exc:
        # Wrap unexpected errors as retryable
        logger.error(f"Unexpected error generating STL for {generation_id}: {str(exc)}")
        raise RetryableError(f"STL generation failed: {str(exc)}") from exc


def cleanup_old_files_task_func(
    progress_callback: ProgressCallbackProtocol | None = None
) -> CleanupResponse:
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
        # Import container inside function to avoid circular imports
        from core.containers.compat import container

        logger.info("Starting file cleanup task")

        # Update progress
        if progress_callback:
            progress_callback.update(10, 'cleanup_starting')

        # Get file storage service and settings from container
        file_storage = container.file_storage()
        settings = container.settings()

        # Perform cleanup
        if progress_callback:
            progress_callback.update(50, 'cleaning_files')

        deleted_count = file_storage.cleanup_old_files(settings.file_max_age_minutes * 60)

        if progress_callback:
            progress_callback.update(100, 'cleanup_completed')

        logger.info(f"File cleanup completed: {deleted_count} files deleted")

        return CleanupResponse(
            success=True,
            deleted_files=deleted_count,
            message=f'Cleaned up {deleted_count} old files'
        )

    except Exception as exc:
        # For cleanup tasks, we want to retry transient errors but not fail permanently
        # Most cleanup errors are transient (permission issues, disk full, etc.)
        logger.error(f"File cleanup failed: {str(exc)}")

        # Return partial success rather than raising - cleanup failures shouldn't break the system
        return CleanupResponse(
            success=False,
            deleted_files=0,
            error=f"Cleanup failed: {str(exc)}",
            message='File cleanup encountered errors but will retry later'
        )


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
