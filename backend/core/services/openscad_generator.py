import subprocess
import tempfile
from pathlib import Path
from typing import Any

from django.conf import settings
from PIL import Image

from core.interfaces.stl_generator import ISTLGenerator


class OpenSCADGenerator(ISTLGenerator):
    """OpenSCAD implementation of ISTLGenerator."""

    def __init__(self):
        self.openscad_binary = settings.OPENSCAD_BINARY
        self.timeout = settings.OPENSCAD_TIMEOUT

    def generate_stl(
        self,
        heightmap_path: Path,
        coin_parameters: dict[str, Any],
        output_path: Path
    ) -> tuple[bool, str | None]:
        """Generate STL file from heightmap and coin parameters."""
        try:
            # Create OpenSCAD script
            scad_content = self._create_scad_script(heightmap_path, coin_parameters)

            # Write script to temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.scad', delete=False) as f:
                f.write(scad_content)
                scad_path = f.name

            try:
                # Save SCAD file for debugging next to the STL output
                debug_scad_path = output_path.parent / f"{output_path.stem}.scad"
                debug_scad_path.write_text(scad_content)

                # Run OpenSCAD with actual performance optimizations
                cmd = [
                    self.openscad_binary,
                    '-o', str(output_path),
                    '--enable=manifold',    # Use faster Manifold geometry engine
                    '--enable=fast-csg',    # Enable faster CSG operations
                    '--enable=roof',        # Better geometry processing
                    '-q',                   # Quiet mode - less output processing
                    scad_path
                ]

                result = subprocess.run(
                    cmd,
                    timeout=self.timeout,
                    capture_output=True,
                    text=True
                )

                return result.returncode == 0

            finally:
                # Clean up temporary script file
                Path(scad_path).unlink(missing_ok=True)

        except Exception as e:
            return False, f"OpenSCAD generation failed: {str(e)}"

    def validate_parameters(self, parameters: dict[str, Any]) -> bool:
        """Validate coin parameters."""
        required_params = ['shape', 'diameter', 'thickness', 'relief_depth']

        for param in required_params:
            if param not in parameters:
                return False

        # Validate numeric parameters
        try:
            diameter = float(parameters['diameter'])
            thickness = float(parameters['thickness'])
            relief_depth = float(parameters['relief_depth'])

            if diameter <= 0 or thickness <= 0 or relief_depth <= 0:
                return False

            if relief_depth >= thickness:
                return False

        except (ValueError, TypeError):
            return False

        # Validate shape
        valid_shapes = {'circle', 'square', 'hexagon', 'octagon'}
        if parameters['shape'] not in valid_shapes:
            return False

        return True, None

    def _create_scad_script(self, heightmap_path: Path, parameters: dict[str, Any]) -> str:
        """Create OpenSCAD script for coin generation using template substitution."""
        # Build variables map
        variables_map = self._build_variables_map(heightmap_path, parameters)

        # Load template
        template_path = Path(__file__).parent.parent / 'templates' / 'coin_template.scad'
        template_content = template_path.read_text()

        # Generate variables string from map
        variables_string = self._generate_variables_string(variables_map)

        # Replace $VARIABLES$ placeholder with generated variables
        script = template_content.replace('$VARIABLES$', variables_string)

        return script

    def _build_variables_map(self, heightmap_path: Path, parameters: dict[str, Any]) -> dict[str, Any]:
        """Build a map of all OpenSCAD variables and their values."""
        shape = parameters['shape']
        diameter = parameters['diameter']
        thickness = parameters['thickness']
        relief_depth = parameters['relief_depth']
        scale_percent = parameters.get('scale', 100)
        offset_x_percent = parameters.get('offset_x', 0)
        offset_y_percent = parameters.get('offset_y', 0)
        rotation = parameters.get('rotation', 0)

        # Keep heightmap at 512 for good quality
        max_heightmap_size = 512

        # Create optimized and cropped heightmap for OpenSCAD processing
        optimized_heightmap_path, crop_offset_x, crop_offset_y = self._create_optimized_heightmap(
            heightmap_path, diameter, max_heightmap_size, scale_percent, offset_x_percent, offset_y_percent
        )

        # Read optimized heightmap dimensions
        try:
            with Image.open(optimized_heightmap_path) as img:
                heightmap_width, heightmap_height = img.size
        except Exception:
            # Fallback to square assumption if image can't be read
            heightmap_width = heightmap_height = 128

        # Calculate actual values to match frontend exactly, accounting for cropping
        # Frontend: offsetXPixels = (offsetX / 100) * coinSize * pixelsPerMM
        # Since heightmap is already in mm scale, we convert percentage to mm directly
        base_offset_x_mm = (offset_x_percent / 100) * diameter
        base_offset_y_mm = -(offset_y_percent / 100) * diameter  # Invert Y for OpenSCAD coordinate system

        # Adjust offsets to account for cropping (crop_offset is in mm)
        offset_x_mm = base_offset_x_mm - crop_offset_x
        offset_y_mm = base_offset_y_mm - crop_offset_y

        # Image scale calculation:
        # 1. Normalize heightmap to coin size: diameter / heightmap_pixels
        # 2. Apply user scale percentage: * (scale_percent / 100)
        # Combined scaling factor for X and Y
        normalization_scale_x = diameter / heightmap_width
        normalization_scale_y = diameter / heightmap_height
        final_scale_x = normalization_scale_x * (scale_percent / 100.0)
        final_scale_y = normalization_scale_y * (scale_percent / 100.0)

        # Resolution doesn't affect surface() performance, remove it

        # Build the variables map
        variables_map = {
            # Basic coin parameters
            'shape': f'"{shape}"',
            'diameter': diameter,
            'thickness': thickness,
            'relief_depth': relief_depth,

            # Transform parameters
            'offset_x_mm': offset_x_mm,
            'offset_y_mm': offset_y_mm,
            'rotation': rotation,

            # Scaling parameters
            'final_scale_x': final_scale_x,
            'final_scale_y': final_scale_y,

            # File path (use optimized version)
            'heightmap_path': f'"{str(optimized_heightmap_path.absolute())}"',
        }

        return variables_map

    def _generate_variables_string(self, variables_map: dict[str, Any]) -> str:
        """Generate OpenSCAD variable declarations from the variables map."""
        variables_lines = []

        # Add comment header
        variables_lines.append('// Generated variables')

        # Generate variable assignments
        for var_name, var_value in variables_map.items():
            variables_lines.append(f'{var_name} = {var_value};')

        return '\n'.join(variables_lines)

    def _create_optimized_heightmap(self, original_path: Path, diameter: float, max_size: int = 256,
                                  scale_percent: float = 100, offset_x_percent: float = 0,
                                  offset_y_percent: float = 0) -> tuple[Path, float, float]:
        """Create an optimized and cropped heightmap for OpenSCAD processing.

        Returns:
            tuple: (optimized_path, crop_offset_x_mm, crop_offset_y_mm)
        """
        try:
            with Image.open(original_path) as img:
                # Convert to grayscale if not already
                if img.mode != 'L':
                    img = img.convert('L')

                original_width, original_height = img.size

                # Calculate the visible region based on scale and offset
                crop_box, crop_offset_x_mm, crop_offset_y_mm = self._calculate_visible_region(
                    original_width, original_height, diameter, scale_percent,
                    offset_x_percent, offset_y_percent
                )

                # Crop to visible region first
                cropped_img = img.crop(crop_box)

                # Then resize the cropped image for performance
                optimized_img = self._resize_for_performance(cropped_img, diameter, max_size)

                # Save optimized heightmap next to original
                optimized_path = original_path.parent / f"optimized_{original_path.name}"
                optimized_img.save(optimized_path)

                return optimized_path, crop_offset_x_mm, crop_offset_y_mm

        except Exception as e:
            # Log the error for debugging
            print(f"Error in heightmap optimization: {e}")
            # If optimization fails, return original path with zero offsets
            return original_path, 0.0, 0.0

    def _calculate_visible_region(self, img_width: int, img_height: int, diameter: float,
                                scale_percent: float, offset_x_percent: float,
                                offset_y_percent: float) -> tuple[tuple[int, int, int, int], float, float]:
        """Calculate the visible region of the heightmap that will appear on the coin.

        Returns:
            tuple: ((left, top, right, bottom), crop_offset_x_mm, crop_offset_y_mm)
        """
        # Calculate the coin's radius in "image coordinate system"
        coin_radius_mm = diameter / 2

        # Calculate how the image maps to real-world coordinates
        # When scale = 100%, the image should fit exactly within the coin diameter
        scale_factor = scale_percent / 100.0

        # Calculate the effective size of the image when scaled
        image_width_mm = diameter / scale_factor
        image_height_mm = diameter * (img_height / img_width) / scale_factor

        # Calculate offset in mm (note: frontend Y is inverted vs OpenSCAD)
        offset_x_mm = (offset_x_percent / 100) * diameter
        offset_y_mm = (offset_y_percent / 100) * diameter  # Don't invert here, we'll handle it later

        # Calculate the coin's boundaries in image coordinate system
        # Image center is at (image_width_mm/2, image_height_mm/2)
        image_center_x_mm = image_width_mm / 2
        image_center_y_mm = image_height_mm / 2

        # Coin center in image coordinates (with offset)
        coin_center_x_mm = image_center_x_mm + offset_x_mm
        coin_center_y_mm = image_center_y_mm + offset_y_mm

        # Calculate coin boundaries in image mm coordinates
        coin_left_mm = coin_center_x_mm - coin_radius_mm
        coin_right_mm = coin_center_x_mm + coin_radius_mm
        coin_top_mm = coin_center_y_mm - coin_radius_mm
        coin_bottom_mm = coin_center_y_mm + coin_radius_mm

        # Clamp to image boundaries
        crop_left_mm = max(0, coin_left_mm)
        crop_right_mm = min(image_width_mm, coin_right_mm)
        crop_top_mm = max(0, coin_top_mm)
        crop_bottom_mm = min(image_height_mm, coin_bottom_mm)

        # Convert mm coordinates to pixel coordinates
        pixels_per_mm_x = img_width / image_width_mm
        pixels_per_mm_y = img_height / image_height_mm

        crop_left_px = int(crop_left_mm * pixels_per_mm_x)
        crop_right_px = int(crop_right_mm * pixels_per_mm_x)
        crop_top_px = int(crop_top_mm * pixels_per_mm_y)
        crop_bottom_px = int(crop_bottom_mm * pixels_per_mm_y)

        # Ensure we have at least some pixels to work with
        crop_left_px = max(0, min(crop_left_px, img_width - 1))
        crop_right_px = max(crop_left_px + 1, min(crop_right_px, img_width))
        crop_top_px = max(0, min(crop_top_px, img_height - 1))
        crop_bottom_px = max(crop_top_px + 1, min(crop_bottom_px, img_height))

        # Calculate the offset introduced by cropping (in mm)
        crop_offset_x_mm = crop_left_mm
        crop_offset_y_mm = crop_top_mm

        return (crop_left_px, crop_top_px, crop_right_px, crop_bottom_px), crop_offset_x_mm, crop_offset_y_mm

    def _resize_for_performance(self, img: Image.Image, diameter: float, max_size: int) -> Image.Image:
        """Resize image for optimal OpenSCAD performance."""
        # Calculate optimal resolution based on coin size
        # Rule of thumb: ~3 pixels per mm for good detail without excessive computation
        target_pixels_per_mm = 3
        target_max_dimension = int(diameter * target_pixels_per_mm)

        # Use the smaller of user limit or calculated target
        max_dimension = min(target_max_dimension, max_size)
        max_dimension = max(max_dimension, 64)  # Minimum for decent quality

        # Calculate new size maintaining aspect ratio
        current_width, current_height = img.size
        aspect_ratio = current_width / current_height

        if aspect_ratio > 1:
            new_width = max_dimension
            new_height = int(max_dimension / aspect_ratio)
        else:
            new_height = max_dimension
            new_width = int(max_dimension * aspect_ratio)

        # Only resize if we're actually reducing the size
        if new_width < current_width or new_height < current_height:
            return img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        else:
            return img
