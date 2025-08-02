"""
APScheduler Task Queue Implementation

Provides an APScheduler-based implementation of the TaskQueue interface.
This is designed for desktop deployment where we don't want the complexity
of Celery and Redis, but still need background task processing.
"""

import logging
import threading
import uuid
from collections.abc import Callable
from datetime import datetime, timedelta
from typing import Any

from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.schedulers.background import BackgroundScheduler

from core.interfaces.task_queue import ProgressCallback, TaskQueue, TaskResult, TaskStatus
from core.models import TaskProgress

logger = logging.getLogger(__name__)


class APSchedulerTaskQueue(TaskQueue):
    """
    APScheduler implementation of the TaskQueue interface.

    This implementation uses APScheduler for task scheduling and execution,
    with in-memory storage for results and progress tracking. It's designed
    for single-machine desktop deployment where simplicity is preferred
    over distributed processing capabilities.
    """

    def __init__(self, max_workers: int = 4):
        """
        Initialize the APScheduler task queue.

        Args:
            max_workers: Maximum number of concurrent task threads
        """
        self.max_workers = max_workers
        self._results: dict[str, TaskResult] = {}
        self._results_lock = threading.RLock()
        self._task_registry: dict[str, Callable] = {}

        # Configure APScheduler
        jobstores = {
            'default': MemoryJobStore()
        }
        executors = {
            'default': ThreadPoolExecutor(max_workers=max_workers)
        }
        job_defaults = {
            'coalesce': False,
            'max_instances': 1,
            'misfire_grace_time': 30
        }

        self.scheduler = BackgroundScheduler(
            jobstores=jobstores,
            executors=executors,
            job_defaults=job_defaults,
            timezone='UTC'
        )

        self._is_running = False
        logger.info(f"Initialized APScheduler task queue with {max_workers} workers")

    def register_task(self, task_name: str, task_func: Callable) -> None:
        """
        Register a task function for execution.

        Args:
            task_name: Unique name for the task
            task_func: Function to execute for this task
        """
        self._task_registry[task_name] = task_func
        logger.debug(f"Registered task: {task_name}")

    def enqueue(
        self,
        task_name: str,
        args: tuple = (),
        kwargs: dict[str, str | int | float | bool] | None = None,
        max_retries: int = 3,
        retry_delay: int = 60
    ) -> str:
        """
        Enqueue a task for background execution.

        Args:
            task_name: Name of the registered task function
            args: Positional arguments for the task
            kwargs: Keyword arguments for the task
            max_retries: Maximum number of retry attempts
            retry_delay: Base delay between retries in seconds

        Returns:
            Unique task ID
        """
        if kwargs is None:
            kwargs = {}

        task_id = str(uuid.uuid4())

        if task_name not in self._task_registry:
            error_msg = f"Task {task_name} is not registered"
            logger.error(error_msg)

            # Store failure result immediately
            with self._results_lock:
                self._results[task_id] = TaskResult(
                    task_id=task_id,
                    status=TaskStatus.FAILURE,
                    error=error_msg
                )
            return task_id

        # Initialize task result as PENDING
        with self._results_lock:
            self._results[task_id] = TaskResult(
                task_id=task_id,
                status=TaskStatus.PENDING
            )

        try:
            # Schedule the task for immediate execution
            self.scheduler.add_job(
                func=self._execute_task,
                args=(task_id, task_name, args, kwargs, max_retries, retry_delay, 0),
                id=task_id,
                name=f"{task_name}:{task_id}",
                replace_existing=True
            )

            logger.info(f"Enqueued APScheduler task {task_name} with ID {task_id}")
            return task_id

        except Exception as e:
            error_msg = f"Failed to enqueue task {task_name}: {str(e)}"
            logger.error(error_msg)

            # Update result with failure
            with self._results_lock:
                self._results[task_id] = TaskResult(
                    task_id=task_id,
                    status=TaskStatus.FAILURE,
                    error=error_msg
                )
            return task_id

    def _execute_task(
        self,
        task_id: str,
        task_name: str,
        args: tuple,
        kwargs: dict[str, Any],
        max_retries: int,
        retry_delay: int,
        retry_count: int
    ) -> None:
        """
        Execute a task with retry logic and progress tracking.

        Args:
            task_id: Unique task identifier
            task_name: Name of the task to execute
            args: Task arguments
            kwargs: Task keyword arguments
            max_retries: Maximum retry attempts
            retry_delay: Base retry delay in seconds
            retry_count: Current retry count
        """
        logger.info(f"Executing task {task_name} (ID: {task_id}, attempt: {retry_count + 1})")

        # Update status to PROCESSING
        with self._results_lock:
            if task_id in self._results:
                self._results[task_id] = TaskResult(
                    task_id=task_id,
                    status=TaskStatus.PROCESSING,
                    retry_count=retry_count
                )

        try:
            # Create progress callback
            progress_callback = ProgressCallback(
                task_id=task_id,
                update_func=self._update_task_progress
            )

            # Add progress callback to kwargs if the task supports it
            task_func = self._task_registry[task_name]

            # Execute the task
            if 'progress_callback' in task_func.__code__.co_varnames:
                kwargs['progress_callback'] = progress_callback

            result = task_func(*args, **kwargs)

            # Store successful result
            with self._results_lock:
                self._results[task_id] = TaskResult(
                    task_id=task_id,
                    status=TaskStatus.SUCCESS,
                    result=result,
                    retry_count=retry_count
                )

            logger.info(f"Task {task_name} (ID: {task_id}) completed successfully")

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Task {task_name} (ID: {task_id}) failed: {error_msg}")

            # Check if we should retry
            if retry_count < max_retries:
                # Schedule retry with exponential backoff
                retry_delay_actual = retry_delay * (2 ** retry_count)
                retry_time = datetime.utcnow() + timedelta(seconds=retry_delay_actual)

                logger.info(f"Scheduling retry {retry_count + 1}/{max_retries} for task {task_id} in {retry_delay_actual}s")

                # Update status to RETRY
                with self._results_lock:
                    self._results[task_id] = TaskResult(
                        task_id=task_id,
                        status=TaskStatus.RETRY,
                        error=error_msg,
                        retry_count=retry_count
                    )

                # Schedule retry
                self.scheduler.add_job(
                    func=self._execute_task,
                    args=(task_id, task_name, args, kwargs, max_retries, retry_delay, retry_count + 1),
                    run_date=retry_time,
                    id=f"{task_id}_retry_{retry_count + 1}",
                    name=f"{task_name}:{task_id}:retry:{retry_count + 1}",
                    replace_existing=True
                )
            else:
                # Max retries exceeded, mark as failed
                with self._results_lock:
                    self._results[task_id] = TaskResult(
                        task_id=task_id,
                        status=TaskStatus.FAILURE,
                        error=f"Task failed after {max_retries} retries: {error_msg}",
                        retry_count=retry_count
                    )

    def _update_task_progress(self, task_id: str, status: TaskStatus, progress_data: TaskProgress) -> None:
        """Update task progress information."""
        with self._results_lock:
            if task_id in self._results:
                current_result = self._results[task_id]
                self._results[task_id] = TaskResult(
                    task_id=task_id,
                    status=status,
                    result=current_result.result,
                    error=current_result.error,
                    progress=progress_data,
                    retry_count=current_result.retry_count
                )

    def get_result(self, task_id: str) -> TaskResult | None:
        """
        Get task result.

        Args:
            task_id: Task identifier

        Returns:
            TaskResult object or None if not found
        """
        with self._results_lock:
            return self._results.get(task_id)

    def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a task.

        Args:
            task_id: Task identifier

        Returns:
            True if task was cancelled
        """
        try:
            # Try to remove the job from scheduler
            try:
                self.scheduler.remove_job(task_id)
                cancelled_from_scheduler = True
            except Exception as e:
                logger.debug(f"Could not remove job {task_id} from scheduler: {e}")
                cancelled_from_scheduler = False

            # Update result status
            with self._results_lock:
                if task_id in self._results:
                    current_result = self._results[task_id]
                    if current_result.status in [TaskStatus.PENDING, TaskStatus.PROCESSING, TaskStatus.RETRY]:
                        self._results[task_id] = TaskResult(
                            task_id=task_id,
                            status=TaskStatus.FAILURE,
                            error="Task was cancelled",
                            retry_count=current_result.retry_count
                        )
                        logger.info(f"Cancelled task {task_id}")
                        return True

            return cancelled_from_scheduler

        except Exception as e:
            logger.error(f"Failed to cancel task {task_id}: {str(e)}")
            return False

    def start(self) -> None:
        """Start the APScheduler task queue."""
        if not self._is_running:
            self.scheduler.start()
            self._is_running = True
            logger.info("Started APScheduler task queue")

    def stop(self) -> None:
        """Stop the APScheduler task queue."""
        if self._is_running:
            self.scheduler.shutdown(wait=True)
            self._is_running = False
            logger.info("Stopped APScheduler task queue")

    def is_running(self) -> bool:
        """Check if the task queue is running."""
        return self._is_running and self.scheduler.running

    def get_queue_stats(self) -> dict[str, int | str]:
        """Get queue statistics."""
        try:
            with self._results_lock:
                total_tasks = len(self._results)
                pending_tasks = sum(1 for r in self._results.values() if r.status == TaskStatus.PENDING)
                processing_tasks = sum(1 for r in self._results.values() if r.status == TaskStatus.PROCESSING)
                completed_tasks = sum(1 for r in self._results.values() if r.status == TaskStatus.SUCCESS)
                failed_tasks = sum(1 for r in self._results.values() if r.status == TaskStatus.FAILURE)
                retry_tasks = sum(1 for r in self._results.values() if r.status == TaskStatus.RETRY)

            # Get scheduler job count
            scheduled_jobs = len(self.scheduler.get_jobs())

            return {
                'queue_type': 'apscheduler',
                'is_running': self.is_running(),
                'max_workers': self.max_workers,
                'scheduled_jobs': scheduled_jobs,
                'total_tasks': total_tasks,
                'pending_tasks': pending_tasks,
                'running_tasks': processing_tasks,
                'completed_tasks': completed_tasks,
                'failed_tasks': failed_tasks,
                'retry_tasks': retry_tasks,
                'registered_tasks': len(self._task_registry)
            }

        except Exception as e:
            logger.error(f"Failed to get APScheduler queue stats: {str(e)}")
            return {
                'queue_type': 'apscheduler',
                'error': str(e),
                'is_running': self.is_running()
            }

    def cleanup_old_results(self, max_age_hours: int = 24) -> int:
        """
        Clean up old task results to prevent memory buildup.

        Args:
            max_age_hours: Maximum age of results to keep in hours

        Returns:
            Number of results cleaned up
        """
        if not hasattr(self, '_result_timestamps'):
            self._result_timestamps: dict[str, datetime] = {}

        current_time = datetime.utcnow()
        max_age = timedelta(hours=max_age_hours)

        with self._results_lock:
            to_remove = []
            for task_id, result in self._results.items():
                # Use stored timestamp or current time for new results
                timestamp = self._result_timestamps.get(task_id, current_time)

                # Only clean up completed tasks (success or failure)
                if result.status in [TaskStatus.SUCCESS, TaskStatus.FAILURE]:
                    if current_time - timestamp > max_age:
                        to_remove.append(task_id)

            # Remove old results
            for task_id in to_remove:
                del self._results[task_id]
                self._result_timestamps.pop(task_id, None)

            logger.info(f"Cleaned up {len(to_remove)} old task results")
            return len(to_remove)
