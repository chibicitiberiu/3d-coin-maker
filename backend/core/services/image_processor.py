import logging

from PIL import Image, ImageEnhance

from core.constants import ProcessingConstants
from core.interfaces.image_processor import IImageProcessor
from core.models import GrayscaleMethod, ImageProcessingParameters

logger = logging.getLogger(__name__)


class PILImageProcessor(IImageProcessor):
    """PIL implementation of IImageProcessor."""

    SUPPORTED_FORMATS = {'PNG', 'JPEG', 'GIF', 'BMP', 'TIFF'}

    def validate_image(self, image_path: str) -> bool:
        """Validate that the file is a valid image."""
        try:
            with Image.open(image_path) as img:
                return img.format in self.SUPPORTED_FORMATS
        except Exception as e:
            logger.debug(f"Could not validate image format for {image_path}: {e}")
            return False

    def process_image(self, image_path: str, parameters: ImageProcessingParameters) -> Image.Image:
        """Process image with given parameters and return PIL Image."""
        with Image.open(image_path) as img:
            # Convert to RGB if needed
            if img.mode != 'RGB':
                img = img.convert('RGB')

            # Apply grayscale conversion
            processed_img = self._apply_grayscale(img, parameters.grayscale_method)

            # Apply brightness adjustment
            if parameters.brightness != 0:
                processed_img = self._adjust_brightness(processed_img, parameters.brightness)

            # Apply contrast adjustment
            if parameters.contrast != ProcessingConstants.DEFAULT_CONTRAST_VALUE:
                processed_img = self._adjust_contrast(processed_img, parameters.contrast)

            # Apply gamma correction
            if parameters.gamma != 1.0:
                processed_img = self._apply_gamma(processed_img, parameters.gamma)

            # Apply inversion if requested
            if parameters.invert:
                processed_img = self._invert_colors(processed_img)

            return processed_img

    def create_heightmap(self, processed_image: Image.Image) -> Image.Image:
        """Convert processed image to heightmap format."""
        # Ensure grayscale
        if processed_image.mode != 'L':
            processed_image = processed_image.convert('L')

        return processed_image

    def _apply_grayscale(self, img: Image.Image, method: GrayscaleMethod) -> Image.Image:
        """Apply grayscale conversion based on method."""
        if method == GrayscaleMethod.AVERAGE:
            return img.convert('L')
        elif method == GrayscaleMethod.LUMINANCE:
            # Standard luminance formula
            return img.convert('L')
        elif method == GrayscaleMethod.RED:
            return img.getchannel('R').convert('L')
        elif method == GrayscaleMethod.GREEN:
            return img.getchannel('G').convert('L')
        elif method == GrayscaleMethod.BLUE:
            return img.getchannel('B').convert('L')
        else:
            return img.convert('L')

    def _adjust_brightness(self, img: Image.Image, brightness: int) -> Image.Image:
        """Adjust brightness (-100 to +100)."""
        factor = 1.0 + (brightness / ProcessingConstants.DEFAULT_BRIGHTNESS_FACTOR)
        enhancer = ImageEnhance.Brightness(img)
        return enhancer.enhance(factor)

    def _adjust_contrast(self, img: Image.Image, contrast: int) -> Image.Image:
        """Adjust contrast (0% to 300%)."""
        factor = contrast / ProcessingConstants.DEFAULT_BRIGHTNESS_FACTOR
        enhancer = ImageEnhance.Contrast(img)
        return enhancer.enhance(factor)

    def _apply_gamma(self, img: Image.Image, gamma: float) -> Image.Image:
        """Apply gamma correction."""
        # Create gamma correction lookup table
        lut = [int(ProcessingConstants.GAMMA_LUT_MAX_VALUE * ((i / ProcessingConstants.GAMMA_LUT_MAX_VALUE) ** (1.0 / gamma)))
               for i in range(ProcessingConstants.GAMMA_LUT_SIZE)]
        return img.point(lut)

    def _invert_colors(self, img: Image.Image) -> Image.Image:
        """Invert image colors."""
        if img.mode == 'L':
            lut = [ProcessingConstants.GAMMA_LUT_MAX_VALUE - i for i in range(ProcessingConstants.GAMMA_LUT_SIZE)]
            return img.point(lut)
        else:
            # For RGB images
            return Image.eval(img, lambda x: ProcessingConstants.GAMMA_LUT_MAX_VALUE - x)
