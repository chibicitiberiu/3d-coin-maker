"""
Generation Route Handler

Handles STL generation task initiation.
"""

from fastapi import APIRouter, HTTPException, status

from api.dependencies import ClientIPDep, TaskQueueDep
from api.models import CoinParametersRequest, TaskResponse
from api.route_utils import enqueue_task_with_defaults, extract_generation_params
from core.interfaces.task_queue import TaskQueue

router = APIRouter()


@router.post("/generate/", response_model=TaskResponse, status_code=202)
async def generate_stl(
    request: CoinParametersRequest,
    task_queue: TaskQueue = TaskQueueDep,
    client_ip: str = ClientIPDep
):
    """Start STL generation task."""
    generation_id, parameters = extract_generation_params(request)

    try:
        task_id = enqueue_task_with_defaults(
            task_queue,
            'generate_stl_task',
            generation_id,
            parameters
        )

        return TaskResponse(
            task_id=task_id,
            generation_id=generation_id,
            message="STL generation started"
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start STL generation: {str(e)}"
        ) from e
