"""
Status Route Handler

Handles generation status queries.
"""

from uuid import UUID

from fastapi import APIRouter, Query

from api.dependencies import CoinServiceDep, TaskQueueDep
from api.models import GenerationStatusResponse
from api.route_utils import check_file_availability, get_stl_info, get_task_status_info
from core.interfaces.task_queue import TaskQueue
from core.services.coin_generation_service import CoinGenerationService

router = APIRouter()


@router.get("/status/{generation_id}/", response_model=GenerationStatusResponse)
async def get_status(
    generation_id: UUID,
    task_id: str | None = Query(None),
    task_queue: TaskQueue = TaskQueueDep,
    coin_service: CoinGenerationService = CoinServiceDep
):
    """Get generation status and file availability."""
    generation_id_str = str(generation_id)

    # Get task status info - prefer provided task_id, fallback to service lookup
    if not task_id:
        task_id = coin_service.get_task_id(generation_id_str)
    task_status_response = await get_task_status_info(task_queue, task_id)

    # Check file availability
    file_availability = await check_file_availability(coin_service, generation_id_str)
    stl_info = await get_stl_info(coin_service, generation_id_str)

    return GenerationStatusResponse(
        generation_id=generation_id,
        status=task_status_response.status,
        progress=task_status_response.progress,
        step=task_status_response.step,
        error=task_status_response.error,
        has_original=file_availability.has_original,
        has_processed=file_availability.has_processed,
        has_heightmap=file_availability.has_heightmap,
        has_stl=stl_info.has_stl,
        stl_timestamp=stl_info.stl_timestamp
    )
