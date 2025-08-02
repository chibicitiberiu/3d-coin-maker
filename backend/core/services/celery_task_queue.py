"""
Celery Task Queue Implementation

Provides a wrapper around Celery to implement the TaskQueue interface.
This allows the existing Celery-based task system to work with the new
unified task queue abstraction.
"""

import logging
from typing import Any

from celery.exceptions import NotRegistered
from celery.result import AsyncResult

from core.interfaces.task_queue import TaskQueue, TaskResult, TaskStatus

logger = logging.getLogger(__name__)


class CeleryTaskQueue(TaskQueue):
    """
    Celery implementation of the TaskQueue interface.

    This class wraps existing Celery functionality to provide a unified
    interface for task execution, compatible with the desktop APScheduler
    implementation.
    """

    # Map simple task names to Celery task names from celery_app
    TASK_NAME_MAPPING = {
        'process_image_task': 'process_image_task',
        'generate_stl_task': 'generate_stl_task',
        'cleanup_old_files_task': 'cleanup_old_files_task',
    }

    def __init__(self):
        """Initialize the Celery task queue."""
        # Import the specific Celery app instance instead of using current_app
        from celery_app import app
        self.app = app
        logger.info("Initialized Celery task queue")

    def enqueue(
        self,
        task_name: str,
        args: tuple = (),
        kwargs: dict[str, Any] | None = None,
        max_retries: int = 3,
        retry_delay: int = 60
    ) -> str:
        """
        Enqueue a task using Celery.

        Args:
            task_name: Name of the Celery task (e.g., 'apps.processing.tasks.process_image_task')
            args: Positional arguments for the task
            kwargs: Keyword arguments for the task
            max_retries: Maximum retries (passed to task, but Celery tasks define their own)
            retry_delay: Retry delay (passed to task, but Celery tasks define their own)

        Returns:
            Celery task ID
        """
        if kwargs is None:
            kwargs = {}

        try:
            # Map simple task name to full Celery task name
            celery_task_name = self.TASK_NAME_MAPPING.get(task_name, task_name)
            print(f"DEBUG: Mapping {task_name} -> {celery_task_name}")

            # Get the task by name
            task = self.app.tasks.get(celery_task_name)
            print(f"DEBUG: Found task: {task}")
            if task is None:
                print(f"DEBUG: Available tasks: {list(self.app.tasks.keys())}")
                raise NotRegistered(f"Task {celery_task_name} is not registered")

            # Execute the task asynchronously
            result = task.delay(*args, **kwargs)

            logger.info(f"Enqueued Celery task {task_name} ({celery_task_name}) with ID {result.id}")
            return result.id

        except Exception as e:
            logger.error(f"Failed to enqueue Celery task {task_name}: {str(e)}")
            raise

    def get_result(self, task_id: str) -> TaskResult | None:
        """
        Get task result from Celery.

        Args:
            task_id: Celery task ID

        Returns:
            TaskResult object with current status and data
        """
        try:
            result = AsyncResult(task_id, app=self.app)

            # Map Celery states to our TaskStatus enum
            status_mapping = {
                'PENDING': TaskStatus.PENDING,
                'RECEIVED': TaskStatus.PENDING,
                'STARTED': TaskStatus.PROCESSING,
                'PROGRESS': TaskStatus.PROCESSING,
                'PROCESSING': TaskStatus.PROCESSING,  # Added missing PROCESSING state
                'SUCCESS': TaskStatus.SUCCESS,
                'FAILURE': TaskStatus.FAILURE,
                'REVOKED': TaskStatus.FAILURE,
                'RETRY': TaskStatus.RETRY,
            }

            celery_status = result.status
            task_status = status_mapping.get(celery_status, TaskStatus.PENDING)


            # Get result data
            task_result = None
            error_message = None
            progress_data = None

            if task_status == TaskStatus.SUCCESS:
                task_result = result.result
            elif task_status == TaskStatus.FAILURE:
                error_message = str(result.result) if result.result else "Task failed"
            elif task_status == TaskStatus.PROCESSING:
                # Celery stores progress in result.info for PROGRESS state
                if hasattr(result, 'info') and isinstance(result.info, dict):
                    progress_data = result.info

            # Get retry count if available
            retry_count = 0
            if hasattr(result, 'info') and isinstance(result.info, dict):
                retry_count = result.info.get('retries', 0)

            return TaskResult(
                task_id=task_id,
                status=task_status,
                result=task_result,
                error=error_message,
                progress=progress_data,
                retry_count=retry_count
            )

        except Exception as e:
            logger.error(f"Failed to get result for Celery task {task_id}: {str(e)}")
            return TaskResult(
                task_id=task_id,
                status=TaskStatus.FAILURE,
                error=f"Failed to retrieve task status: {str(e)}"
            )

    def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a Celery task.

        Args:
            task_id: Celery task ID

        Returns:
            True if task was revoked successfully
        """
        try:
            result = AsyncResult(task_id, app=self.app)
            result.revoke(terminate=True)
            logger.info(f"Cancelled Celery task {task_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to cancel Celery task {task_id}: {str(e)}")
            return False

    def start(self) -> None:
        """
        Start the Celery task queue.

        Note: For Celery, the worker processes are typically started externally,
        so this method just logs that the queue is ready to accept tasks.
        """
        logger.info("Celery task queue is ready (workers managed externally)")

    def stop(self) -> None:
        """
        Stop the Celery task queue.

        Note: For Celery, worker processes are typically managed externally,
        so this method just logs the stop request.
        """
        logger.info("Celery task queue stop requested (workers managed externally)")

    def is_running(self) -> bool:
        """
        Check if Celery workers are available.

        Returns:
            True if at least one worker is available
        """
        try:
            # Check if any workers are active
            inspect = self.app.control.inspect()
            active_workers = inspect.active()

            if active_workers is None:
                return False

            # Return True if any workers are found
            return len(active_workers) > 0

        except Exception as e:
            logger.error(f"Failed to check Celery worker status: {str(e)}")
            return False

    def get_queue_stats(self) -> dict[str, Any]:
        """
        Get Celery queue statistics.

        Returns:
            Dictionary with queue statistics
        """
        try:
            inspect = self.app.control.inspect()

            # Get active tasks across all workers
            active_tasks = inspect.active() or {}
            active_count = sum(len(tasks) for tasks in active_tasks.values())

            # Get scheduled tasks
            scheduled_tasks = inspect.scheduled() or {}
            scheduled_count = sum(len(tasks) for tasks in scheduled_tasks.values())

            # Get reserved tasks (queued but not started)
            reserved_tasks = inspect.reserved() or {}
            reserved_count = sum(len(tasks) for tasks in reserved_tasks.values())

            # Get worker stats
            stats = inspect.stats() or {}
            worker_count = len(stats)

            return {
                'worker_count': worker_count,
                'active_tasks': active_count,
                'scheduled_tasks': scheduled_count,
                'reserved_tasks': reserved_count,
                'pending_tasks': scheduled_count + reserved_count,
                'running_tasks': active_count,
                'queue_type': 'celery'
            }

        except Exception as e:
            logger.error(f"Failed to get Celery queue stats: {str(e)}")
            return {
                'worker_count': 0,
                'active_tasks': 0,
                'scheduled_tasks': 0,
                'reserved_tasks': 0,
                'pending_tasks': 0,
                'running_tasks': 0,
                'queue_type': 'celery',
                'error': str(e)
            }
