"""
Task Queue Interface

Provides a unified interface for both Celery (web deployment) and APScheduler (desktop deployment)
task queue systems, allowing the application to switch between them based on deployment context.
"""

from abc import ABC, abstractmethod
from collections.abc import Callable
from enum import Enum
from typing import Any, Protocol


class TaskStatus(Enum):
    """Task execution status."""
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    RETRY = "RETRY"


class TaskResult:
    """Represents the result of a task execution."""

    def __init__(
        self,
        task_id: str,
        status: TaskStatus,
        result: dict[str, Any] | None = None,
        error: str | None = None,
        progress: dict[str, Any] | None = None,
        retry_count: int = 0
    ):
        self.task_id = task_id
        self.status = status
        self.result = result
        self.error = error
        self.progress = progress
        self.retry_count = retry_count

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary format for API responses."""
        return {
            'task_id': self.task_id,
            'status': self.status.value,
            'result': self.result,
            'error': self.error,
            'progress': self.progress,
            'retry_count': self.retry_count
        }


class ProgressCallbackProtocol(Protocol):
    """Protocol for progress callback implementations."""

    def update(self, progress: int, step: str, extra_data: dict[str, Any] | None = None) -> None:
        """Update task progress."""
        ...


class ProgressCallback:
    """Callback interface for task progress updates."""

    def __init__(self, task_id: str, update_func: Callable[[str, TaskStatus, dict[str, Any]], None]):
        self.task_id = task_id
        self.update_func = update_func

    def update(self, progress: int, step: str, extra_data: dict[str, Any] | None = None):
        """Update task progress."""
        progress_data = {
            'progress': progress,
            'step': step,
            **(extra_data or {})
        }
        self.update_func(self.task_id, TaskStatus.PROCESSING, progress_data)


class TaskQueue(ABC):
    """
    Abstract interface for task queue implementations.

    This interface provides a unified way to enqueue tasks, check their status,
    and manage the task queue lifecycle across different implementations
    (Celery for web deployment, APScheduler for desktop deployment).
    """

    @abstractmethod
    def enqueue(
        self,
        task_name: str,
        args: tuple = (),
        kwargs: dict[str, Any] | None = None,
        max_retries: int = 3,
        retry_delay: int = 60
    ) -> str:
        """
        Enqueue a task for background execution.

        Args:
            task_name: Name of the task function to execute
            args: Positional arguments for the task
            kwargs: Keyword arguments for the task
            max_retries: Maximum number of retry attempts
            retry_delay: Base delay between retries in seconds

        Returns:
            Unique task ID for tracking execution
        """
        pass

    @abstractmethod
    def get_result(self, task_id: str) -> TaskResult | None:
        """
        Get the current status and result of a task.

        Args:
            task_id: Unique task identifier

        Returns:
            TaskResult object with current status, or None if task not found
        """
        pass

    @abstractmethod
    def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a pending or running task.

        Args:
            task_id: Unique task identifier

        Returns:
            True if task was cancelled, False if not found or already completed
        """
        pass

    @abstractmethod
    def start(self) -> None:
        """
        Start the task queue system.

        This method should initialize any necessary resources and begin
        processing enqueued tasks.
        """
        pass

    @abstractmethod
    def stop(self) -> None:
        """
        Stop the task queue system.

        This method should gracefully shut down the task processing,
        allowing running tasks to complete if possible.
        """
        pass

    @abstractmethod
    def is_running(self) -> bool:
        """
        Check if the task queue is currently running.

        Returns:
            True if the task queue is active and processing tasks
        """
        pass

    @abstractmethod
    def get_queue_stats(self) -> dict[str, Any]:
        """
        Get statistics about the task queue.

        Returns:
            Dictionary containing queue statistics like:
            - pending_tasks: Number of tasks waiting to be processed
            - running_tasks: Number of currently executing tasks
            - completed_tasks: Number of successfully completed tasks
            - failed_tasks: Number of failed tasks
        """
        pass

    def health_check(self) -> dict[str, Any]:
        """
        Perform a health check on the task queue system.

        Returns:
            Dictionary with health status information
        """
        try:
            is_running = self.is_running()
            stats = self.get_queue_stats()

            return {
                'status': 'healthy' if is_running else 'unhealthy',
                'is_running': is_running,
                'stats': stats
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'is_running': False
            }
