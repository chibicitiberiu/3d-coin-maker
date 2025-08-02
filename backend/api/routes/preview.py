"""
Preview Route Handler

Handles preview image requests for generated content.
"""

from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse

from api.dependencies import CoinServiceDep
from core.services.coin_generation_service import CoinGenerationService

router = APIRouter()


@router.get("/preview/{generation_id}")
async def get_preview(
    generation_id: UUID,
    coin_service: CoinGenerationService = CoinServiceDep
):
    """Get processed heightmap image for preview."""
    generation_id_str = str(generation_id)
    heightmap_path = coin_service.get_file_path(generation_id_str, 'heightmap')

    if not heightmap_path or not heightmap_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Preview image not found"
        )

    return FileResponse(
        path=heightmap_path,
        media_type="image/png"
    )
