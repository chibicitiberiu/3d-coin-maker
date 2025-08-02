"""
Core Domain Models

Domain models representing business entities and value objects.
These models provide type safety and validation for the core business logic.
"""

from dataclasses import dataclass
from enum import Enum
from uuid import UUID


class TaskStatus(Enum):
    """Task execution status."""
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    RETRY = "RETRY"


class GrayscaleMethod(Enum):
    """Methods for converting images to grayscale."""
    AVERAGE = "average"
    LUMINANCE = "luminance"
    RED = "red"
    GREEN = "green"
    BLUE = "blue"


class CoinShape(Enum):
    """Supported coin shapes."""
    CIRCLE = "circle"
    SQUARE = "square"
    HEXAGON = "hexagon"
    OCTAGON = "octagon"


@dataclass(frozen=True)
class ImageProcessingParameters:
    """Parameters for image processing operations."""
    filename: str
    grayscale_method: GrayscaleMethod = GrayscaleMethod.LUMINANCE
    brightness: int = 0
    contrast: int = 200
    gamma: float = 1.0
    invert: bool = False

    def __post_init__(self):
        """Validate parameters after initialization."""
        if not (-100 <= self.brightness <= 100):
            raise ValueError("Brightness must be between -100 and 100")
        if not (0 <= self.contrast <= 300):
            raise ValueError("Contrast must be between 0 and 300")
        if not (0.1 <= self.gamma <= 5.0):
            raise ValueError("Gamma must be between 0.1 and 5.0")

    def to_dict(self) -> dict[str, str | int | float | bool]:
        """Convert to dictionary for backwards compatibility."""
        return {
            'filename': self.filename,
            'grayscale_method': self.grayscale_method.value,
            'brightness': self.brightness,
            'contrast': self.contrast,
            'gamma': self.gamma,
            'invert': self.invert
        }

    @classmethod
    def from_dict(cls, data: dict[str, str | int | float | bool]) -> 'ImageProcessingParameters':
        """Create from dictionary for backwards compatibility."""
        return cls(
            filename=str(data['filename']),
            grayscale_method=GrayscaleMethod(data.get('grayscale_method', 'luminance')),
            brightness=int(data.get('brightness', 0)),
            contrast=int(data.get('contrast', 200)),
            gamma=float(data.get('gamma', 1.0)),
            invert=bool(data.get('invert', False))
        )


@dataclass(frozen=True)
class CoinParameters:
    """Parameters for coin generation."""
    shape: CoinShape = CoinShape.CIRCLE
    diameter: float = 30.0
    thickness: float = 3.0
    relief_depth: float = 1.0
    scale: float = 100.0
    offset_x: float = 0.0
    offset_y: float = 0.0
    rotation: float = 0.0

    def __post_init__(self):
        """Validate parameters after initialization."""
        if self.diameter <= 0.01:
            raise ValueError("Diameter must be greater than 0.01mm")
        if self.thickness <= 0.01:
            raise ValueError("Thickness must be greater than 0.01mm")
        if self.relief_depth <= 0.01:
            raise ValueError("Relief depth must be greater than 0.01mm")
        if self.relief_depth >= self.thickness:
            raise ValueError("Relief depth must be less than coin thickness")
        if self.scale <= 0.00001:
            raise ValueError("Scale must be greater than 0.00001%")

    def to_dict(self) -> dict[str, str | float]:
        """Convert to dictionary for backwards compatibility."""
        return {
            'shape': self.shape.value,
            'diameter': self.diameter,
            'thickness': self.thickness,
            'relief_depth': self.relief_depth,
            'scale': self.scale,
            'offset_x': self.offset_x,
            'offset_y': self.offset_y,
            'rotation': self.rotation
        }

    @classmethod
    def from_dict(cls, data: dict[str, str | float]) -> 'CoinParameters':
        """Create from dictionary for backwards compatibility."""
        return cls(
            shape=CoinShape(data.get('shape', 'circle')),
            diameter=float(data.get('diameter', 30.0)),
            thickness=float(data.get('thickness', 3.0)),
            relief_depth=float(data.get('relief_depth', 1.0)),
            scale=float(data.get('scale', 100.0)),
            offset_x=float(data.get('offset_x', 0.0)),
            offset_y=float(data.get('offset_y', 0.0)),
            rotation=float(data.get('rotation', 0.0))
        )


@dataclass
class TaskProgress:
    """Task progress information."""
    progress: int  # 0-100
    step: str
    extra_data: dict[str, str | int | float | bool] | None = None

    def __post_init__(self):
        """Validate progress value."""
        if not (0 <= self.progress <= 100):
            raise ValueError("Progress must be between 0 and 100")

    def to_dict(self) -> dict[str, str | int | dict[str, str | int | float | bool] | None]:
        """Convert to dictionary."""
        result = {
            'progress': self.progress,
            'step': self.step
        }
        if self.extra_data:
            result.update(self.extra_data)
        return result


@dataclass
class TaskResult:
    """Result of a task execution."""
    task_id: str
    status: TaskStatus
    result: dict[str, str | int | float | bool] | None = None
    error: str | None = None
    progress: TaskProgress | None = None
    retry_count: int = 0

    def to_dict(self) -> dict[str, str | int | dict | None]:
        """Convert to dictionary for API responses."""
        return {
            'task_id': self.task_id,
            'status': self.status.value,
            'result': self.result,
            'error': self.error,
            'progress': self.progress.to_dict() if self.progress else None,
            'retry_count': self.retry_count
        }


@dataclass
class TaskResponse:
    """Standard response model for task functions."""
    success: bool
    generation_id: str
    step: str

    def to_dict(self) -> dict[str, str | bool]:
        """Convert to dictionary for backwards compatibility."""
        return {
            'success': self.success,
            'generation_id': self.generation_id,
            'step': self.step
        }


@dataclass
class CleanupResponse:
    """Response model for cleanup tasks."""
    success: bool
    deleted_files: int
    message: str
    error: str | None = None

    def to_dict(self) -> dict[str, str | bool | int]:
        """Convert to dictionary for backwards compatibility."""
        result = {
            'success': self.success,
            'deleted_files': self.deleted_files,
            'message': self.message
        }
        if self.error:
            result['error'] = self.error
        return result


@dataclass
class GenerationSession:
    """A coin generation session."""
    generation_id: UUID
    ip_address: str
    created_at: float  # timestamp
    status: TaskStatus = TaskStatus.PENDING
    current_step: str = "initialized"
    progress: int = 0
    error: str | None = None

    def update_progress(self, progress: int, step: str, error: str | None = None) -> None:
        """Update session progress."""
        if not (0 <= progress <= 100):
            raise ValueError("Progress must be between 0 and 100")

        self.progress = progress
        self.current_step = step
        if error:
            self.error = error
            self.status = TaskStatus.FAILURE
        elif progress == 100:
            self.status = TaskStatus.SUCCESS
        else:
            self.status = TaskStatus.PROCESSING


class ProcessingError(Exception):
    """Custom exception for processing errors that should not be retried."""

    def __init__(self, message: str, details: str | None = None):
        self.message = message
        self.details = details
        super().__init__(message)


class RetryableError(Exception):
    """Custom exception for errors that should trigger a retry."""

    def __init__(self, message: str, details: str | None = None):
        self.message = message
        self.details = details
        super().__init__(message)


class ValidationError(Exception):
    """Custom exception for validation errors."""

    def __init__(self, message: str, field: str | None = None):
        self.message = message
        self.field = field
        super().__init__(message)


class RateLimitError(Exception):
    """Custom exception for rate limit exceeded."""

    def __init__(self, message: str, retry_after: int | None = None):
        self.message = message
        self.retry_after = retry_after
        super().__init__(message)
