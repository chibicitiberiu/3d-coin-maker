"""
Progress Callback Utilities

Centralized utilities for handling progress callbacks and updates
throughout the application.
"""

import logging
from typing import Protocol, runtime_checkable

from core.constants import ProcessingConstants
from core.interfaces.task_queue import ProgressCallbackProtocol

logger = logging.getLogger(__name__)


@runtime_checkable
class ProgressReporter(Protocol):
    """Protocol for progress reporting functionality."""

    def report_progress(self, progress: int, step: str, **kwargs) -> None:
        """Report progress with step description."""
        ...


class StandardProgressReporter:
    """Standard implementation of progress reporting."""

    def __init__(self, callback: ProgressCallbackProtocol | None = None, logger_name: str | None = None):
        self.callback = callback
        self.logger = logging.getLogger(logger_name) if logger_name else logger

    def report_progress(self, progress: int, step: str, **kwargs) -> None:
        """Report progress to callback and log."""
        if self.callback:
            self.callback.update(progress, step, kwargs if kwargs else None)

        self.logger.info(f"Progress: {progress}% - {step}")


class ProgressTracker:
    """Utility class for tracking progress through predefined stages."""

    def __init__(self,
                 callback: ProgressCallbackProtocol | None = None,
                 logger_name: str | None = None,
                 stages: dict[str, int] | None = None):
        """
        Initialize progress tracker.

        Args:
            callback: Optional progress callback
            logger_name: Optional logger name for this tracker
            stages: Custom stage definitions, defaults to processing constants
        """
        self.reporter = StandardProgressReporter(callback, logger_name)
        self.stages = stages or {
            'start': 0,
            'image_processing': ProcessingConstants.PROGRESS_IMAGE_START,
            'heightmap_generation': ProcessingConstants.PROGRESS_HEIGHTMAP,
            'mesh_creation': ProcessingConstants.PROGRESS_MESH_CREATION,
            'boolean_operations': ProcessingConstants.PROGRESS_BOOLEAN_OPS,
            'stl_export': ProcessingConstants.PROGRESS_STL_EXPORT,
            'complete': ProcessingConstants.PROGRESS_COMPLETE
        }

    def update_stage(self, stage_name: str, custom_message: str | None = None, **kwargs) -> None:
        """Update progress to a predefined stage."""
        if stage_name not in self.stages:
            logger.warning(f"Unknown progress stage: {stage_name}")
            return

        progress_value = self.stages[stage_name]
        message = custom_message or stage_name.replace('_', ' ').title()

        self.reporter.report_progress(progress_value, message, **kwargs)

    def update_custom(self, progress: int, step: str, **kwargs) -> None:
        """Update progress with custom values."""
        self.reporter.report_progress(progress, step, **kwargs)


def create_image_processing_tracker(callback: ProgressCallbackProtocol | None = None) -> ProgressTracker:
    """Create a progress tracker configured for image processing tasks."""
    stages = {
        'start': 0,
        'loading_image': 10,
        'applying_brightness': 30,
        'applying_contrast': 50,
        'applying_gamma': 70,
        'saving_result': 90,
        'complete': 100
    }
    return ProgressTracker(callback, 'image_processing', stages)


def create_stl_generation_tracker(callback: ProgressCallbackProtocol | None = None) -> ProgressTracker:
    """Create a progress tracker configured for STL generation tasks."""
    stages = {
        'start': 0,
        'loading_heightmap': ProcessingConstants.PROGRESS_IMAGE_START,
        'generating_relief': ProcessingConstants.PROGRESS_HEIGHTMAP,
        'creating_base': ProcessingConstants.PROGRESS_MESH_CREATION,
        'boolean_operations': ProcessingConstants.PROGRESS_BOOLEAN_OPS,
        'exporting_stl': ProcessingConstants.PROGRESS_STL_EXPORT,
        'complete': ProcessingConstants.PROGRESS_COMPLETE
    }
    return ProgressTracker(callback, 'stl_generation', stages)


def safe_progress_update(callback: ProgressCallbackProtocol | None,
                        progress: int,
                        step: str,
                        **kwargs) -> None:
    """
    Safely update progress with error handling.

    This function provides a simple way to update progress that won't
    raise exceptions if the callback fails.
    """
    if not callback:
        return

    try:
        callback.update(progress, step, kwargs if kwargs else None)
    except Exception as e:
        logger.warning(f"Progress callback failed: {e}")


def batch_progress_updates(callback: ProgressCallbackProtocol | None,
                          updates: list[tuple[int, str]]) -> None:
    """
    Perform multiple progress updates in sequence.

    Args:
        callback: Progress callback to use
        updates: List of (progress, step) tuples to execute
    """
    if not callback:
        return

    for progress, step in updates:
        safe_progress_update(callback, progress, step)
