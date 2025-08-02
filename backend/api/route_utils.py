"""
Route Utilities

Common utility functions used by API route handlers.
"""

import time
from uuid import UUID

from api.models import FileAvailabilityResponse, STLInfoResponse, TaskStatusResponse
from core.interfaces.task_queue import TaskQueue
from core.models import CoinParameters, ImageProcessingParameters
from core.services.coin_generation_service import CoinGenerationService


def extract_image_processing_params(request_data) -> tuple[UUID, ImageProcessingParameters]:
    """Extract generation ID and image processing parameters from request data."""
    generation_id = request_data.generation_id

    # Convert request data to domain model
    image_params = ImageProcessingParameters(
        filename=request_data.filename,
        grayscale_method=request_data.grayscale_method,
        brightness=request_data.brightness,
        contrast=request_data.contrast,
        gamma=request_data.gamma,
        invert=request_data.invert
    )

    return generation_id, image_params


def extract_coin_generation_params(request_data) -> tuple[UUID, CoinParameters]:
    """Extract generation ID and coin parameters from request data."""
    generation_id = request_data.generation_id

    # Convert request data to domain model
    coin_params = CoinParameters(
        shape=request_data.shape,
        diameter=request_data.diameter,
        thickness=request_data.thickness,
        relief_depth=request_data.relief_depth,
        scale=request_data.scale,
        offset_x=request_data.offset_x,
        offset_y=request_data.offset_y,
        rotation=request_data.rotation
    )

    return generation_id, coin_params


def extract_generation_params(request_data) -> tuple[UUID, dict]:
    """Generic function to extract generation parameters from request data.

    This is a compatibility function that works with both image processing
    and coin generation requests by converting the request to a dictionary.
    """
    generation_id = request_data.generation_id

    # Convert request to dict, excluding the generation_id
    params_dict = {}
    for field_name, field_value in request_data:
        if field_name != 'generation_id':
            params_dict[field_name] = field_value

    return generation_id, params_dict


def enqueue_image_processing_task(task_queue: TaskQueue, generation_id: UUID, image_params: ImageProcessingParameters) -> str:
    """Enqueue an image processing task with proper model."""
    return task_queue.enqueue(
        task_name='process_image_task',
        args=(str(generation_id), image_params.to_dict()),
        max_retries=3,
        retry_delay=60
    )


def enqueue_stl_generation_task(task_queue: TaskQueue, generation_id: UUID, coin_params: CoinParameters) -> str:
    """Enqueue an STL generation task with proper model."""
    return task_queue.enqueue(
        task_name='generate_stl_task',
        args=(str(generation_id), coin_params.to_dict()),
        max_retries=3,
        retry_delay=60
    )


def enqueue_task_with_defaults(task_queue: TaskQueue, task_name: str, generation_id: UUID, parameters: dict) -> str:
    """Generic function to enqueue a task with default retry settings.

    This is a compatibility function that provides standard retry behavior
    for all task types.
    """
    return task_queue.enqueue(
        task_name=task_name,
        args=(str(generation_id), parameters),
        max_retries=3,
        retry_delay=60
    )


async def get_task_status_info(task_queue: TaskQueue, task_id: str | None) -> TaskStatusResponse:
    """Get task status and info from task queue."""
    if not task_id:
        return TaskStatusResponse(status='UNKNOWN', error='No task ID provided')

    try:
        task_result = task_queue.get_result(task_id)
        if task_result:
            progress_info = task_result.progress if task_result.progress else None
            return TaskStatusResponse(
                status=task_result.status.value,
                progress=progress_info.progress if progress_info else 0,
                step=progress_info.step if progress_info else 'unknown',
                error=task_result.error
            )
        else:
            return TaskStatusResponse(status='UNKNOWN', error='Task not found')
    except Exception as e:
        return TaskStatusResponse(status='FAILURE', error=f'Error retrieving task status: {str(e)}')


async def check_file_availability(coin_service: CoinGenerationService, generation_id: str) -> FileAvailabilityResponse:
    """Check availability of generated files."""
    return FileAvailabilityResponse(
        has_original=coin_service.get_file_path(generation_id, 'original') is not None,
        has_processed=coin_service.get_file_path(generation_id, 'processed') is not None,
        has_heightmap=coin_service.get_file_path(generation_id, 'heightmap') is not None,
    )


async def get_stl_info(coin_service: CoinGenerationService, generation_id: str) -> STLInfoResponse:
    """Get STL file availability and timestamp."""
    stl_path = coin_service.get_file_path(generation_id, 'stl')
    has_stl = stl_path is not None and stl_path.exists()

    stl_timestamp = None
    if has_stl and stl_path is not None:
        try:
            stl_timestamp = int(stl_path.stat().st_mtime * 1000)  # milliseconds timestamp
        except (OSError, AttributeError):
            stl_timestamp = int(time.time() * 1000)

    return STLInfoResponse(has_stl=has_stl, stl_timestamp=stl_timestamp)
