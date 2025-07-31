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
    ) -> bool:
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

                # Run OpenSCAD
                cmd = [
                    self.openscad_binary,
                    '-o', str(output_path),
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

        except Exception:
            return False

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

        return True

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
        
        # Read heightmap image to get actual dimensions
        try:
            with Image.open(heightmap_path) as img:
                heightmap_width, heightmap_height = img.size
        except Exception:
            # Fallback to square assumption if image can't be read
            heightmap_width = heightmap_height = 512
        
        # Calculate actual values to match frontend exactly
        # Frontend: offsetXPixels = (offsetX / 100) * coinSize * pixelsPerMM
        # Since heightmap is already in mm scale, we convert percentage to mm directly
        offset_x_mm = (offset_x_percent / 100) * diameter
        # Invert Y offset to match coordinate system difference between canvas (Y down) and OpenSCAD (Y up)
        offset_y_mm = -(offset_y_percent / 100) * diameter
        
        # Image scale calculation:
        # 1. Normalize heightmap to coin size: diameter / heightmap_pixels
        # 2. Apply user scale percentage: * (scale_percent / 100)
        # Combined scaling factor for X and Y
        normalization_scale_x = diameter / heightmap_width
        normalization_scale_y = diameter / heightmap_height
        final_scale_x = normalization_scale_x * (scale_percent / 100.0)
        final_scale_y = normalization_scale_y * (scale_percent / 100.0)
        
        # Balanced resolution for reasonable performance
        resolution = 64  # Good balance between quality and performance
        
        # Build the variables map
        variables_map = {
            # Basic coin parameters
            'shape': f'"{shape}"',
            'diameter': diameter,
            'thickness': thickness,
            'relief_depth': relief_depth,
            'resolution': resolution,
            
            # Transform parameters
            'offset_x_mm': offset_x_mm,
            'offset_y_mm': offset_y_mm,
            'rotation': rotation,
            
            # Scaling parameters
            'final_scale_x': final_scale_x,
            'final_scale_y': final_scale_y,
            
            # File path
            'heightmap_path': f'"{str(heightmap_path.absolute())}"',
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
