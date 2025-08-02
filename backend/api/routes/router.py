"""
API Router Configuration

Configures and combines all API route modules into a single router.
"""

from fastapi import APIRouter

from .download import router as download_router
from .generation import router as generation_router
from .health import router as health_router
from .preview import router as preview_router
from .processing import router as processing_router
from .status import router as status_router
from .upload import router as upload_router


def create_api_router(route_prefix: str = "") -> APIRouter:
    """Create configured API router with all routes.

    Args:
        route_prefix: Optional prefix for all routes (e.g., "/api")

    Returns:
        Configured APIRouter instance
    """
    api_router = APIRouter(prefix=route_prefix)

    # Include all route modules
    api_router.include_router(upload_router, tags=["upload"])
    api_router.include_router(processing_router, tags=["processing"])
    api_router.include_router(generation_router, tags=["generation"])
    api_router.include_router(status_router, tags=["status"])
    api_router.include_router(download_router, tags=["download"])
    api_router.include_router(preview_router, tags=["preview"])
    api_router.include_router(health_router, tags=["health"])

    return api_router
