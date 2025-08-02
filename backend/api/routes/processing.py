"""
Processing Route Handler

Handles image processing task initiation.
"""

from fastapi import APIRouter, HTTPException, status

from api.dependencies import ClientIPDep, TaskQueueDep
from api.models import ImageProcessingRequest, TaskResponse
from api.route_utils import enqueue_task_with_defaults, extract_generation_params
from core.interfaces.task_queue import TaskQueue

router = APIRouter()


@router.post("/process/", response_model=TaskResponse, status_code=202)
async def process_image(
    request: ImageProcessingRequest,
    task_queue: TaskQueue = TaskQueueDep,
    client_ip: str = ClientIPDep
):
    """Start image processing task."""
    generation_id, parameters = extract_generation_params(request)

    try:
        task_id = enqueue_task_with_defaults(
            task_queue,
            'process_image_task',
            generation_id,
            parameters
        )

        return TaskResponse(
            task_id=task_id,
            generation_id=generation_id,
            message="Image processing started"
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start image processing: {str(e)}"
        ) from e
