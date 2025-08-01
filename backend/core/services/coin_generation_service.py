import uuid
from pathlib import Path
from typing import Any

from core.interfaces.image_processor import IImageProcessor
from core.interfaces.rate_limiter import IRateLimiter
from core.interfaces.stl_generator import ISTLGenerator
from core.interfaces.storage import IFileStorage


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

    def create_generation(self, uploaded_file, ip_address: str) -> tuple[bool, str, str | None]:
        """
        Create a new generation session.
        Returns: (success, generation_id_or_error, error_message)
        """
        # Check rate limits
        if not self.rate_limiter.is_allowed(ip_address, 'generation'):
            return False, "rate_limit_exceeded", "Rate limit exceeded. Please try again later."

        # Generate unique ID
        generation_id = str(uuid.uuid4())

        try:
            # Save uploaded file as heightmap since frontend already processed it
            heightmap_filename = "heightmap.png"
            file_path = self.file_storage.save_file(uploaded_file, heightmap_filename, generation_id)

            # Validate image
            if not self.image_processor.validate_image(str(file_path)):
                self.file_storage.delete_file(heightmap_filename, generation_id)
                return False, "invalid_image", "Invalid image format."

            # Record the operation
            self.rate_limiter.record_operation(ip_address, 'generation')

            return True, generation_id, None

        except Exception as e:
            return False, "storage_error", f"Error saving file: {str(e)}"

    def process_image(self, generation_id: str, parameters: dict[str, Any]) -> tuple[bool, str | None]:
        """
        Process image with given parameters.
        Returns: (success, error_message)
        """
        try:
            # Get original image path
            original_path = self.file_storage.get_file_path(f"original_{parameters.get('filename', 'image')}", generation_id)
            if not original_path:
                return False, "Original image not found."

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

            return True, None

        except Exception as e:
            return False, f"Error processing image: {str(e)}"

    def generate_stl(self, generation_id: str, coin_parameters: dict[str, Any], progress_callback=None) -> tuple[bool, str | None]:
        """
        Generate STL file from processed image.
        Returns: (success, error_message)
        """
        try:
            # Validate parameters
            if not self.stl_generator.validate_parameters(coin_parameters):
                return False, "Invalid coin parameters."

            # Get heightmap path
            heightmap_path = self.file_storage.get_file_path("heightmap.png", generation_id)
            if not heightmap_path:
                return False, "Heightmap not found. Please process image first."

            # Generate STL
            stl_filename = "coin.stl"
            stl_path = self.file_storage.temp_dir / generation_id / stl_filename

            success, error_message = self.stl_generator.generate_stl(heightmap_path, coin_parameters, stl_path, progress_callback)

            if not success:
                # Return the specific error message from the STL generator
                return False, error_message or "STL generation failed with unknown error"

            return True, None

        except Exception as e:
            return False, f"Error generating STL: {str(e)}"

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
        except Exception:
            return False
