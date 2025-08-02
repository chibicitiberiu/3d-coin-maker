"""
Pydantic Models for FastAPI

These models replace Django serializers and provide automatic validation,
serialization, and API documentation for the FastAPI endpoints.
"""

from uuid import UUID

from fastapi import UploadFile
from pydantic import BaseModel, Field, validator

from constants import ValidationConstants


class ImageProcessingRequest(BaseModel):
    """Request model for image processing parameters."""
    generation_id: UUID
    filename: str = Field(..., max_length=ValidationConstants.MAX_FILENAME_LENGTH)

    # Image processing parameters (matching frontend API)
    grayscale_method: str = Field(default='luminance', pattern='^(average|luminance|red|green|blue)$')
    brightness: int = Field(default=0, ge=ValidationConstants.BRIGHTNESS_MIN, le=ValidationConstants.BRIGHTNESS_MAX)
    contrast: int = Field(default=ValidationConstants.CONTRAST_MAX, ge=ValidationConstants.CONTRAST_MIN, le=ValidationConstants.CONTRAST_MAX)
    gamma: float = Field(default=1.0, ge=0.1, le=5.0)
    invert: bool = Field(default=False)


class CoinParametersRequest(BaseModel):
    """Request model for coin generation parameters."""
    generation_id: UUID

    # Coin parameters
    shape: str = Field(default='circle', pattern='^(circle|square|hexagon|octagon)$')
    diameter: float = Field(default=ValidationConstants.DEFAULT_DIAMETER, gt=0.01)  # Minimum 0.01mm
    thickness: float = Field(default=ValidationConstants.DEFAULT_THICKNESS, gt=0.01)  # Minimum 0.01mm
    relief_depth: float = Field(default=ValidationConstants.DEFAULT_RELIEF_DEPTH, gt=0.01)  # Minimum 0.01mm

    # Heightmap positioning
    scale: float = Field(default=100.0, gt=0.00001)  # Minimum 0.00001%
    offset_x: float = Field(default=0.0)  # No limits
    offset_y: float = Field(default=0.0)  # No limits
    rotation: float = Field(default=0.0)  # No limits

    @validator('relief_depth')
    def relief_depth_must_be_less_than_thickness(cls, v, values):
        """Validate that relief depth is less than coin thickness."""
        if 'thickness' in values and v >= values['thickness']:
            raise ValueError('Relief depth must be less than coin thickness')
        return v


class UploadResponse(BaseModel):
    """Response model for image upload."""
    generation_id: UUID
    message: str


class TaskResponse(BaseModel):
    """Response model for task initiation."""
    task_id: str
    generation_id: UUID
    message: str


class GenerationStatusResponse(BaseModel):
    """Response model for generation status."""
    generation_id: UUID
    status: str
    progress: int
    step: str
    error: str | None = None

    # File availability flags
    has_original: bool
    has_processed: bool
    has_heightmap: bool
    has_stl: bool

    # Cache busting timestamp for STL file
    stl_timestamp: int | None = None


class HealthCheckResponse(BaseModel):
    """Response model for health check."""
    status: str
    services: dict
    timestamp: float


class ErrorResponse(BaseModel):
    """Standard error response model."""
    error: str
    detail: str | None = None


# Custom validation for image uploads
def validate_image_file(file: UploadFile) -> UploadFile:
    """
    Validate uploaded image file.

    Args:
        file: Uploaded file object

    Returns:
        Validated file object

    Raises:
        ValueError: If file validation fails
    """
    # Check file size (50MB limit)
    if hasattr(file, 'size') and file.size and file.size > ValidationConstants.MAX_FILE_SIZE_BYTES:
        raise ValueError("Image file too large. Maximum size is 50MB.")

    # Check content type
    if file.content_type:
        allowed_types = {
            'image/png', 'image/jpeg', 'image/jpg',
            'image/gif', 'image/bmp', 'image/tiff'
        }
        if file.content_type not in allowed_types:
            raise ValueError(f"Unsupported image format. Allowed formats: {', '.join(allowed_types)}")

    # Check file extension
    if file.filename:
        allowed_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.tif'}
        file_ext = '.' + file.filename.split('.')[-1].lower() if '.' in file.filename else ''
        if file_ext not in allowed_extensions:
            raise ValueError(f"Unsupported file extension. Allowed extensions: {', '.join(allowed_extensions)}")

    return file
