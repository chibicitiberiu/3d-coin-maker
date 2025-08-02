"""
Health Check Route Handler

Handles application health monitoring.
"""

import time

from fastapi import APIRouter

from api.dependencies import TaskQueueDep
from api.models import HealthCheckResponse, ServiceStatus
from core.interfaces.task_queue import TaskQueue

router = APIRouter()


@router.get("/health/", response_model=HealthCheckResponse)
async def health_check(task_queue: TaskQueue = TaskQueueDep):
    """Health check endpoint."""
    try:
        # Check task queue health
        queue_health = task_queue.health_check()

        return HealthCheckResponse(
            status="healthy",
            services={
                "version": ServiceStatus(status="1.0.0"),
                "task_queue_status": ServiceStatus(status="healthy" if queue_health else "unhealthy")
            },
            timestamp=time.time()
        )
    except Exception as e:
        return HealthCheckResponse(
            status="unhealthy",
            services={
                "version": ServiceStatus(status="1.0.0"),
                "task_queue_status": ServiceStatus(status="error"),
                "error": ServiceStatus(status=str(e))
            },
            timestamp=time.time()
        )
