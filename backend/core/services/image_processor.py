from typing import Any

from PIL import Image, ImageEnhance

from core.interfaces.image_processor import IImageProcessor


class PILImageProcessor(IImageProcessor):
    """PIL implementation of IImageProcessor."""

    SUPPORTED_FORMATS = {'PNG', 'JPEG', 'GIF', 'BMP', 'TIFF'}

    def validate_image(self, image_path: str) -> bool:
        """Validate that the file is a valid image."""
        try:
            with Image.open(image_path) as img:
                return img.format in self.SUPPORTED_FORMATS
        except Exception:
            return False

    def process_image(self, image_path: str, parameters: dict[str, Any]) -> Image.Image:
        """Process image with given parameters and return PIL Image."""
        with Image.open(image_path) as img:
            # Convert to RGB if needed
            if img.mode != 'RGB':
                img = img.convert('RGB')

            # Apply grayscale conversion
            grayscale_method = parameters.get('grayscale_method', 'luminance')
            processed_img = self._apply_grayscale(img, grayscale_method)

            # Apply brightness adjustment
            brightness = parameters.get('brightness', 0)
            if brightness != 0:
                processed_img = self._adjust_brightness(processed_img, brightness)

            # Apply contrast adjustment
            contrast = parameters.get('contrast', 100)
            if contrast != 100:
                processed_img = self._adjust_contrast(processed_img, contrast)

            # Apply gamma correction
            gamma = parameters.get('gamma', 1.0)
            if gamma != 1.0:
                processed_img = self._apply_gamma(processed_img, gamma)

            # Apply inversion if requested
            if parameters.get('invert', False):
                processed_img = self._invert_colors(processed_img)

            return processed_img

    def create_heightmap(self, processed_image: Image.Image) -> Image.Image:
        """Convert processed image to heightmap format."""
        # Ensure grayscale
        if processed_image.mode != 'L':
            processed_image = processed_image.convert('L')

        return processed_image

    def _apply_grayscale(self, img: Image.Image, method: str) -> Image.Image:
        """Apply grayscale conversion based on method."""
        if method == 'average':
            return img.convert('L')
        elif method == 'luminance':
            # Standard luminance formula
            return img.convert('L')
        elif method == 'red':
            return img.getchannel('R').convert('L')
        elif method == 'green':
            return img.getchannel('G').convert('L')
        elif method == 'blue':
            return img.getchannel('B').convert('L')
        else:
            return img.convert('L')

    def _adjust_brightness(self, img: Image.Image, brightness: int) -> Image.Image:
        """Adjust brightness (-100 to +100)."""
        factor = 1.0 + (brightness / 100.0)
        enhancer = ImageEnhance.Brightness(img)
        return enhancer.enhance(factor)

    def _adjust_contrast(self, img: Image.Image, contrast: int) -> Image.Image:
        """Adjust contrast (0% to 300%)."""
        factor = contrast / 100.0
        enhancer = ImageEnhance.Contrast(img)
        return enhancer.enhance(factor)

    def _apply_gamma(self, img: Image.Image, gamma: float) -> Image.Image:
        """Apply gamma correction."""
        # Create gamma correction lookup table
        lut = [int(255 * ((i / 255.0) ** (1.0 / gamma))) for i in range(256)]
        return img.point(lut)

    def _invert_colors(self, img: Image.Image) -> Image.Image:
        """Invert image colors."""
        if img.mode == 'L':
            lut = [255 - i for i in range(256)]
            return img.point(lut)
        else:
            # For RGB images
            return Image.eval(img, lambda x: 255 - x)
