import logging
import uuid
from collections.abc import Callable
from pathlib import Path
from uuid import UUID

from core.interfaces.image_processor import IImageProcessor
from core.interfaces.rate_limiter import IRateLimiter
from core.interfaces.stl_generator import ISTLGenerator
from core.interfaces.storage import IFileStorage
from core.models import (
    CoinParameters,
    ImageProcessingParameters,
    ProcessingError,
    RateLimitError,
    ValidationError,
)

logger = logging.getLogger(__name__)


class CoinGenerationService:
    """Service for managing coin generation workflow."""

    def __init__(
        self,
        file_storage: IFileStorage,
        image_processor: IImageProcessor,
        stl_generator: ISTLGenerator,
        rate_limiter: IRateLimiter,
    ):
        self.file_storage = file_storage
        self.image_processor = image_processor
        self.stl_generator = stl_generator
        self.rate_limiter = rate_limiter

    def create_generation(self, uploaded_file, ip_address: str) -> UUID:
        """
        Create a new generation session.

        Args:
            uploaded_file: The uploaded file object
            ip_address: Client IP address for rate limiting

        Returns:
            UUID of the created generation session

        Raises:
            RateLimitError: If rate limit is exceeded
            ValidationError: If uploaded file is invalid
            ProcessingError: If file storage fails
        """
        # Check rate limits
        if not self.rate_limiter.is_allowed(ip_address, 'generation'):
            raise RateLimitError("Rate limit exceeded. Please try again later.")

        # Generate unique ID
        generation_id = uuid.uuid4()

        try:
            # Save uploaded file as heightmap since frontend already processed it
            heightmap_filename = "heightmap.png"
            file_path = self.file_storage.save_file(uploaded_file, heightmap_filename, str(generation_id))

            # Validate image
            if not self.image_processor.validate_image(str(file_path)):
                self.file_storage.delete_file(heightmap_filename, str(generation_id))
                raise ValidationError("Invalid image format.")

            # Record the operation
            self.rate_limiter.record_operation(ip_address, 'generation')

            return generation_id

        except Exception as e:
            if isinstance(e, RateLimitError | ValidationError):
                raise
            raise ProcessingError(f"Error saving file: {str(e)}") from e

    def process_image(self, generation_id: str, parameters: ImageProcessingParameters) -> None:
        """
        Process image with given parameters.

        Args:
            generation_id: Unique identifier for the generation session
            parameters: Image processing parameters

        Raises:
            ValidationError: If original image not found or parameters invalid
            ProcessingError: If image processing fails
        """
        try:
            # Get original image path
            original_path = self.file_storage.get_file_path(f"original_{parameters.filename}", generation_id)
            if not original_path:
                raise ValidationError("Original image not found.")

            # Process image
            processed_image = self.image_processor.process_image(str(original_path), parameters)

            # Create heightmap
            heightmap = self.image_processor.create_heightmap(processed_image)

            # Save processed image and heightmap
            processed_filename = "processed.png"
            heightmap_filename = "heightmap.png"

            processed_path = self.file_storage.temp_dir / generation_id / processed_filename
            heightmap_path = self.file_storage.temp_dir / generation_id / heightmap_filename

            processed_image.save(processed_path)
            heightmap.save(heightmap_path)

        except Exception as e:
            if isinstance(e, ValidationError):
                raise
            raise ProcessingError(f"Error processing image: {str(e)}") from e

    def generate_stl(
        self,
        generation_id: str,
        coin_parameters: CoinParameters,
        progress_callback: Callable[[int, str], None] | None = None
    ) -> None:
        """
        Generate STL file from processed image.

        Args:
            generation_id: Unique identifier for the generation session
            coin_parameters: Coin generation parameters
            progress_callback: Optional callback for progress updates

        Raises:
            ValidationError: If parameters invalid or heightmap not found
            ProcessingError: If STL generation fails
        """
        try:
            # Validate parameters
            if not self.stl_generator.validate_parameters(coin_parameters):
                raise ValidationError("Invalid coin parameters.")

            # Get heightmap path
            heightmap_path = self.file_storage.get_file_path("heightmap.png", generation_id)
            if not heightmap_path:
                raise ValidationError("Heightmap not found. Please process image first.")

            # Generate STL
            stl_filename = "coin.stl"
            stl_path = self.file_storage.temp_dir / generation_id / stl_filename

            self.stl_generator.generate_stl(heightmap_path, coin_parameters, stl_path, progress_callback)

        except Exception as e:
            if isinstance(e, ValidationError | ProcessingError):
                raise
            raise ProcessingError(f"Error generating STL: {str(e)}") from e

    def get_file_path(self, generation_id: str, file_type: str) -> Path | None:
        """Get path to a generated file."""
        if file_type == 'original':
            # For original files, we need to find the actual filename
            generation_dir = self.file_storage.temp_dir / generation_id
            if generation_dir.exists():
                for file_path in generation_dir.iterdir():
                    if file_path.name.startswith('original_'):
                        return file_path
            return None

        filename_map = {
            'processed': 'processed.png',
            'heightmap': 'heightmap.png',
            'stl': 'coin.stl'
        }

        filename = filename_map.get(file_type)
        if not filename:
            return None

        return self.file_storage.get_file_path(filename, generation_id)

    def cleanup_generation(self, generation_id: str) -> bool:
        """Clean up all files for a generation."""
        try:
            files_to_delete = ['original_image', 'processed.png', 'heightmap.png', 'coin.stl']
            for filename in files_to_delete:
                self.file_storage.delete_file(filename, generation_id)
            return True
        except Exception as e:
            logger.error(f"Failed to cleanup files for generation {generation_id}: {e}")
            return False
