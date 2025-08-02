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
    file: UploadFile,
    coin_service: CoinGenerationService = CoinServiceDep,
    client_ip: str = ClientIPDep
):
    """Upload and store an image file for processing."""
    # Validate file
    validate_image_file(file)

    # Generate unique ID
    generation_id = coin_service.generate_id()

    try:
        # Save original file
        coin_service.save_original_image(generation_id, file)

        return UploadResponse(
            generation_id=generation_id,
            message=f"Image uploaded successfully: {file.filename}"
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload image: {str(e)}"
        ) from e
