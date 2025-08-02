from abc import ABC, abstractmethod

from PIL import Image

from core.models import ImageProcessingParameters


class IImageProcessor(ABC):
    """Interface for image processing operations."""

    @abstractmethod
    def validate_image(self, image_path: str) -> bool:
        """Validate that the file is a valid image."""
        pass

    @abstractmethod
    def process_image(self, image_path: str, parameters: ImageProcessingParameters) -> Image.Image:
        """Process image with given parameters and return PIL Image."""
        pass

    @abstractmethod
    def create_heightmap(self, processed_image: Image.Image) -> Image.Image:
        """Convert processed image to heightmap format."""
        pass
