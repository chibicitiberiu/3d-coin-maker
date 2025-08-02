"""
Upload Route Handler

Handles image file uploads for coin generation.
"""

from fastapi import APIRouter, HTTPException, UploadFile, status

from api.dependencies import ClientIPDep, CoinServiceDep
from api.models import UploadResponse, validate_image_file
from core.services.coin_generation_service import CoinGenerationService

router = APIRouter()


@router.post("/upload/", response_model=UploadResponse, status_code=201)
async def upload_image(
    image: UploadFile,
    coin_service: CoinGenerationService = CoinServiceDep,
    client_ip: str = ClientIPDep
):
    """Upload and store an image file for processing."""
    # Validate file
    validate_image_file(image)

    try:
        # Create generation session (handles validation, rate limiting, and file storage)
        generation_id = coin_service.create_generation(image, client_ip)

        return UploadResponse(
            generation_id=generation_id,
            message=f"Image uploaded successfully: {image.filename}"
        )

    except Exception as e:
        from core.models import ProcessingError, RateLimitError, ValidationError

        if isinstance(e, RateLimitError):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=str(e)
            ) from e
        elif isinstance(e, ValidationError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            ) from e
        elif isinstance(e, ProcessingError):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            ) from e
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload image: {str(e)}"
            ) from e
