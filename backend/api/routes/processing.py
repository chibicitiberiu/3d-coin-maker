"""
Processing Route Handler

Handles image processing task initiation.
"""

from fastapi import APIRouter, HTTPException, status

from api.dependencies import ClientIPDep, CoinServiceDep
from api.models import ImageProcessingRequest, TaskResponse
from api.route_utils import extract_image_processing_params
from core.services.coin_generation_service import CoinGenerationService

router = APIRouter()


@router.post("/process/", response_model=TaskResponse, status_code=202)
async def process_image(
    request: ImageProcessingRequest,
    coin_service: CoinGenerationService = CoinServiceDep,
    client_ip: str = ClientIPDep
):
    """Start image processing task."""
    generation_id, parameters = extract_image_processing_params(request)

    try:
        task_id = coin_service.start_image_processing(str(generation_id), parameters)

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
