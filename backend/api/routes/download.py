"""
Download Route Handler

Handles file downloads for generated content.
"""

from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse

from api.dependencies import CoinServiceDep
from core.services.coin_generation_service import CoinGenerationService

router = APIRouter()


@router.get("/download/{generation_id}/stl")
async def download_stl(
    generation_id: UUID,
    coin_service: CoinGenerationService = CoinServiceDep
):
    """Download generated STL file."""
    generation_id_str = str(generation_id)
    stl_path = coin_service.get_file_path(generation_id_str, 'stl')

    if not stl_path or not stl_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="STL file not found"
        )

    return FileResponse(
        path=stl_path,
        filename=f"coin_{generation_id_str}.stl",
        media_type="application/sla"
    )
