import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

import manifold3d as m3d
import trimesh
from fastapi_settings import settings
from PIL import Image

from core.interfaces.stl_generator import ISTLGenerator


class HMMManifoldGenerator(ISTLGenerator):
    """HMM + Manifold3D implementation of ISTLGenerator for fast and reliable mesh generation."""

    def __init__(self):
        self.hmm_binary = 'hmm'
        self.timeout = settings.hmm_timeout_seconds

    def generate_stl(
        self,
        heightmap_path: Path,
        coin_parameters: dict[str, Any],
        output_path: Path,
        progress_callback=None
    ) -> tuple[bool, str | None]:
        """Generate STL file from heightmap and coin parameters using HMM + Manifold3D."""
        try:
            # Extract parameters
            shape = coin_parameters['shape']
            diameter = coin_parameters['diameter']
            thickness = coin_parameters['thickness']
            relief_depth = coin_parameters['relief_depth']
            scale_percent = coin_parameters.get('scale', 100)
            offset_x_percent = coin_parameters.get('offset_x', 0)
            offset_y_percent = coin_parameters.get('offset_y', 0)
            rotation = coin_parameters.get('rotation', 0)

            print(f"Generating {shape} coin: {diameter}mm diameter, {thickness}mm thick, {relief_depth}mm relief")

            # Report initial progress
            if progress_callback:
                progress_callback(20, 'relief_mesh_generation')

            # Step 1: Generate relief mesh from heightmap using HMM (this is the slow part!)
            relief_mesh = self._generate_relief_mesh_with_hmm(
                heightmap_path, relief_depth, scale_percent,
                offset_x_percent, offset_y_percent, rotation, diameter, progress_callback
            )

            if relief_mesh is None:
                error_msg = "Failed to generate relief mesh with HMM - check logs for detailed error information"
                print("Failed to generate relief mesh with HMM")
                print("This could be due to:")
                print("- HMM binary not found in PATH")
                print("- Invalid heightmap format")
                print("- Manifold3D mesh construction issues")
                print("- HMM execution errors")
                return False, error_msg

            # Step 2: Create coin shape primitives using Manifold
            if progress_callback:
                progress_callback(80, 'coin_shape_generation')

            base_height = thickness - relief_depth
            if base_height <= 0:
                error_msg = f"Invalid coin parameters: base height {base_height}mm (thickness: {thickness}mm, relief: {relief_depth}mm). Relief depth must be less than thickness."
                print(f"Invalid base height: {base_height}mm (thickness: {thickness}mm, relief: {relief_depth}mm)")
                return False, error_msg
            base_coin = self._create_coin_shape(shape, diameter, base_height)

            # Step 3: Boolean operations using Manifold
            if progress_callback:
                progress_callback(85, 'mesh_combination')

            final_mesh = self._combine_relief_with_base(
                relief_mesh, base_coin, shape, diameter, relief_depth, base_height
            )

            if final_mesh is None:
                error_msg = "Failed to combine relief with coin base using Manifold3D boolean operations"
                print("Failed to combine relief with base")
                return False, error_msg

            # Export final mesh to STL
            if progress_callback:
                progress_callback(90, 'stl_export')

            mesh_data = final_mesh.to_mesh()

            # Convert Manifold3D mesh to trimesh and export
            import numpy as np
            vertices = np.array(mesh_data.vert_properties)
            faces = np.array(mesh_data.tri_verts)

            # Create trimesh from the mesh data
            output_trimesh = trimesh.Trimesh(vertices=vertices, faces=faces)
            output_trimesh.export(str(output_path))
            print(f"Successfully exported STL to {output_path}")

            if progress_callback:
                progress_callback(95, 'stl_export_complete')

            return True, None

        except Exception as e:
            error_msg = f"STL generation failed with error: {str(e)}"
            print(f"Error in HMM+Manifold generation: {e}")
            print("Detailed error information:")
            import traceback
            traceback.print_exc()
            print("\nPossible causes:")
            print("- Missing HMM binary (install from https://github.com/hzeller/hmm)")
            print("- Incompatible Manifold3D version")
            print("- Invalid coin parameters")
            print("- Corrupted heightmap file")
            return False, error_msg

    def validate_parameters(self, parameters: dict[str, Any]) -> bool:
        """Validate coin parameters (same as OpenSCAD version)."""
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

    def _generate_relief_mesh_with_hmm(
        self,
        heightmap_path: Path,
        relief_depth: float,
        scale_percent: float,
        offset_x_percent: float,
        offset_y_percent: float,
        rotation: float,
        coin_diameter: float,
        progress_callback=None
    ) -> m3d.Manifold | None:
        """Generate relief mesh from heightmap using HMM."""

        # Check if HMM is available
        if not shutil.which(self.hmm_binary):
            print(f"HMM binary '{self.hmm_binary}' not found in PATH")
            return None

        try:
            # Preprocess heightmap if transformations are needed
            if progress_callback:
                progress_callback(25, 'heightmap_preprocessing')

            processed_heightmap = self._preprocess_heightmap(
                heightmap_path, scale_percent, offset_x_percent,
                offset_y_percent, rotation, coin_diameter
            )

            # Create temporary STL file for HMM output
            with tempfile.NamedTemporaryFile(suffix='.stl', delete=False) as temp_stl:
                temp_stl_path = Path(temp_stl.name)

            try:
                # Check heightmap file exists and get info
                if not processed_heightmap.exists():
                    print(f"Heightmap file does not exist: {processed_heightmap}")
                    return None

                # Get heightmap size for diagnostics
                try:
                    with Image.open(processed_heightmap) as img:
                        width, height = img.size
                        print(f"Processing heightmap: {width}x{height} pixels")
                except Exception as e:
                    print(f"Error reading heightmap info: {e}")

                # Run HMM to generate relief mesh
                # hmm heightmap.png relief.stl -z [relief_depth] -b [base_thickness]
                base_thickness = 0.1  # Small base thickness for the relief

                cmd = [
                    self.hmm_binary,
                    str(processed_heightmap),
                    str(temp_stl_path),
                    '-z', str(relief_depth),
                    '-b', str(base_thickness)
                ]

                print(f"Running HMM: {' '.join(cmd)}")
                if progress_callback:
                    progress_callback(30, 'hmm_mesh_generation')

                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout
                )

                if result.returncode != 0:
                    print(f"HMM failed with return code {result.returncode}")
                    print(f"stdout: {result.stdout}")
                    print(f"stderr: {result.stderr}")
                    return None

                # Load the generated STL into Manifold using trimesh
                if progress_callback:
                    progress_callback(60, 'mesh_loading')

                relief_manifold = self._load_stl_to_manifold(temp_stl_path)

                if relief_manifold is None:
                    print("Failed to load HMM-generated mesh")
                    return None

                # Check if the mesh was loaded successfully using correct API
                if relief_manifold.status() != m3d.Error.NoError:
                    print(f"Loaded mesh has issues: {relief_manifold.status()}")
                    # Try to fix with merge operation - but first check if batch_boolean exists
                    try:
                        # Simple check - if mesh has geometry, proceed anyway
                        if relief_manifold.num_vert() > 0 and relief_manifold.num_tri() > 0:
                            print(f"Proceeding despite status warning - mesh has {relief_manifold.num_vert()} vertices")
                        else:
                            print("Mesh has no geometry, cannot proceed")
                            return None
                    except Exception as e:
                        print(f"Failed to check mesh geometry: {e}")
                        return None

                print(f"Successfully generated relief mesh with {relief_manifold.num_vert()} vertices")

                # Transform relief mesh according to user parameters
                if progress_callback:
                    progress_callback(70, 'mesh_transformation')

                # Step 1: Scale relief so its width equals coin size
                relief_bounds = relief_manifold.bounding_box()
                relief_width = relief_bounds[3] - relief_bounds[0]  # max_x - min_x
                relief_height = relief_bounds[4] - relief_bounds[1]  # max_y - min_y

                base_scale_factor = coin_diameter / relief_width
                print(f"Relief mesh original size: {relief_width}x{relief_height}")
                print(f"Base scaling factor: {base_scale_factor} (to make width = {coin_diameter}mm)")

                # Step 2: Apply user scale percentage
                final_scale_factor = base_scale_factor * (scale_percent / 100.0)
                print(f"Final scaling factor: {final_scale_factor} (including {scale_percent}% user scale)")

                # Apply scaling
                scaled_relief = relief_manifold.scale([final_scale_factor, final_scale_factor, 1.0])

                # Step 3: Center at origin
                scaled_bounds = scaled_relief.bounding_box()
                center_x = (scaled_bounds[0] + scaled_bounds[3]) / 2
                center_y = (scaled_bounds[1] + scaled_bounds[4]) / 2
                centered_relief = scaled_relief.translate([-center_x, -center_y, 0])

                # Step 4: Apply rotation
                if rotation != 0:
                    print(f"Applying rotation: {rotation} degrees")
                    # Convert degrees to radians and rotate around Z axis
                    import math
                    rotation_radians = math.radians(rotation)
                    rotated_relief = centered_relief.rotate([0, 0, rotation_radians])
                else:
                    rotated_relief = centered_relief

                # Step 5: Apply offset (as percentage of coin size)
                offset_x_mm = (offset_x_percent / 100.0) * coin_diameter
                offset_y_mm = -(offset_y_percent / 100.0) * coin_diameter  # Flip Y axis
                if offset_x_mm != 0 or offset_y_mm != 0:
                    print(f"Applying offset: x={offset_x_mm}mm ({offset_x_percent}%), y={offset_y_mm}mm ({-offset_y_percent}%)")
                    final_relief = rotated_relief.translate([offset_x_mm, offset_y_mm, 0])
                else:
                    final_relief = rotated_relief

                print(f"Final transformed relief mesh has {final_relief.num_vert()} vertices")
                final_bounds = final_relief.bounding_box()
                print(f"Final relief bounds: ({final_bounds[0]:.1f}, {final_bounds[1]:.1f}, {final_bounds[2]:.1f}) to ({final_bounds[3]:.1f}, {final_bounds[4]:.1f}, {final_bounds[5]:.1f})")

                return final_relief

            finally:
                # Clean up temporary files
                if temp_stl_path.exists():
                    temp_stl_path.unlink()
                if processed_heightmap != heightmap_path and processed_heightmap.exists():
                    processed_heightmap.unlink()

        except Exception as e:
            print(f"Error generating relief mesh with HMM: {e}")
            return None

    def _preprocess_heightmap(
        self,
        heightmap_path: Path,
        scale_percent: float,
        offset_x_percent: float,
        offset_y_percent: float,
        rotation: float,
        coin_diameter: float
    ) -> Path:
        """Preprocess heightmap to apply transformations before HMM processing."""

        # Always preprocess to ensure optimal size for HMM
        # Note: Only apply image-level transformations that can't be done in 3D
        # Offset and final scaling are handled in 3D space for accuracy
        needs_transformation = (rotation != 0)

        # Check if we need to resize for performance even without transformations
        needs_resize = False
        original_size = None
        try:
            with Image.open(heightmap_path) as img:
                width, height = img.size
                original_size = (width, height)
                max_dimension = max(width, height)
                # Resize if larger than 2048px for HMM performance (increased from 512px)
                if max_dimension > 2048:
                    needs_resize = True
                    print(f"Heightmap {width}x{height} is very large, will resize for HMM performance")
        except Exception:
            pass

        # If no transformations and no resize needed, return original path
        if not needs_transformation and not needs_resize:
            return heightmap_path

        try:
            with Image.open(heightmap_path) as img:
                # Convert to grayscale if needed
                if img.mode != 'L':
                    img = img.convert('L')

                # Resize for HMM performance if needed
                if needs_resize and original_size:
                    max_dimension = max(original_size)
                    # Maintain aspect ratio while limiting to 2048px
                    if img.width > img.height:
                        new_width = 2048
                        new_height = int((2048 * img.height) / img.width)
                    else:
                        new_height = 2048
                        new_width = int((2048 * img.width) / img.height)
                    img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                    print(f"Resized heightmap to {new_width}x{new_height} for HMM performance")

                # Apply transformations that can't be done accurately in 3D
                if rotation != 0:
                    img = img.rotate(rotation, fillcolor=0, expand=True)

                # Note: Scale and offset are now handled in 3D space for better accuracy

                # Save processed image to temporary file
                with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_img:
                    img.save(temp_img.name)
                    return Path(temp_img.name)

        except Exception as e:
            print(f"Error preprocessing heightmap: {e}")
            return heightmap_path

    def _create_coin_shape(self, shape: str, diameter: float, height: float) -> m3d.Manifold:
        """Create coin base shape using Manifold3D."""
        radius = diameter / 2

        if shape == 'circle':
            return m3d.Manifold.cylinder(height, radius, radius, 128)
        elif shape == 'square':
            # Create square using CrossSection.square() and extrude
            try:
                # Create square cross-section centered at origin
                square_cross_section = m3d.CrossSection.square([diameter, diameter], center=True)

                # Extrude to create 3D shape
                extruded_square = square_cross_section.extrude(height)
                print(f"Created extruded square: {extruded_square.num_vert()} vertices, status: {extruded_square.status()}")
                try:
                    square_bounds = extruded_square.bounding_box()
                    print(f"Extruded square bounds: {square_bounds}")
                except Exception as e:
                    print(f"Error getting extruded square bounds: {e}")
                return extruded_square
            except Exception as e:
                print(f"CrossSection extrude approach failed: {e}, falling back to cube")
                # Fallback to cube approach
                cube = m3d.Manifold.cube([diameter, diameter, height])
                translated_cube = cube.translate([-diameter/2, -diameter/2, height / 2])
                return translated_cube
        elif shape == 'hexagon':
            return m3d.Manifold.cylinder(height, radius, radius, 6)
        elif shape == 'octagon':
            return m3d.Manifold.cylinder(height, radius, radius, 8)
        else:
            # Default to cylinder
            return m3d.Manifold.cylinder(height, radius, radius)

    def _combine_relief_with_base(
        self,
        relief_mesh: m3d.Manifold,
        base_coin: m3d.Manifold,
        shape: str,
        diameter: float,
        relief_depth: float,
        base_height: float
    ) -> m3d.Manifold | None:
        """Combine relief mesh with base coin using Manifold boolean operations."""

        try:
            # Create coin mask for clipping relief
            coin_mask = self._create_coin_shape(shape, diameter, relief_depth + 0.1)

            print(f"Relief mesh: {relief_mesh.num_vert()} vertices, status: {relief_mesh.status()}")
            try:
                relief_bounds = relief_mesh.bounding_box()
                print(f"Relief mesh bounds: {relief_bounds}")
            except Exception as e:
                print(f"Error getting relief bounds: {e}")

            print(f"Coin mask: {coin_mask.num_vert()} vertices, status: {coin_mask.status()}")
            try:
                mask_bounds = coin_mask.bounding_box()
                print(f"Coin mask bounds: {mask_bounds}")
            except Exception as e:
                print(f"Error getting mask bounds: {e}")

            print(f"Base coin: {base_coin.num_vert()} vertices, status: {base_coin.status()}")

            # Method A: Current approach (like OpenSCAD)
            # Step 1: Clip relief to coin boundaries (using XOR for intersection in Manifold3D)
            print("Attempting relief clipping with ^ operator...")
            clipped_relief = relief_mesh ^ coin_mask
            print(f"Clipped relief vertices: {clipped_relief.num_vert()}")

            # Check if clipping was successful
            if clipped_relief.status() != m3d.Error.NoError:
                print(f"Relief clipping has issues: {clipped_relief.status()}")
                if clipped_relief.num_vert() == 0:
                    print("Relief clipping produced empty mesh - trying alternative approach")
                    return self._alternative_intersection_approach(
                        relief_mesh, shape, diameter, base_height + relief_depth
                    )
                else:
                    print(f"Proceeding despite clipping warning - {clipped_relief.num_vert()} vertices")
            elif clipped_relief.num_vert() == 0:
                print("Relief clipping produced empty mesh - trying alternative approach")
                return self._alternative_intersection_approach(
                    relief_mesh, shape, diameter, base_height + relief_depth
                )

            print(f"Clipped relief: {clipped_relief.num_vert()} vertices")

            # Step 2: Position clipped relief at top of base coin
            # Relief should sit on top of the base, accounting for its own base thickness
            positioned_relief = clipped_relief.translate([0, 0, base_height])
            print(f"Positioned relief: {positioned_relief.num_vert()} vertices")

            # Step 3: Union with base using + operator
            print("Attempting union with base coin...")
            final_mesh = base_coin + positioned_relief
            print(f"Union result: {final_mesh.num_vert()} vertices, status: {final_mesh.status()}")

            # Check if union was successful
            if final_mesh.status() != m3d.Error.NoError:
                print(f"Union has issues: {final_mesh.status()}, trying alternative approach")
                # Method B: Alternative intersection approach
                return self._alternative_intersection_approach(
                    relief_mesh, shape, diameter, base_height + relief_depth
                )
            elif final_mesh.num_vert() <= base_coin.num_vert():
                print(f"Union didn't add relief vertices (final: {final_mesh.num_vert()}, base: {base_coin.num_vert()}), trying alternative approach")
                # Method B: Alternative intersection approach
                return self._alternative_intersection_approach(
                    relief_mesh, shape, diameter, base_height + relief_depth
                )

            print(f"Final mesh: {final_mesh.num_vert()} vertices")
            return final_mesh

        except Exception as e:
            print(f"Error combining relief with base: {e}")
            return None

    def _alternative_intersection_approach(
        self,
        relief_mesh: m3d.Manifold,
        shape: str,
        diameter: float,
        total_thickness: float
    ) -> m3d.Manifold | None:
        """Alternative approach: single intersection with full-height coin shape."""

        try:
            print("Using alternative intersection approach")

            # Create a base cuboid to extend relief to full height
            # Get relief bounds to create appropriate base
            bounds = relief_mesh.bounding_box()
            print(f"Relief bounds for alternative approach: {bounds}")

            # Make base large enough to encompass relief (with extra margin)
            relief_width = bounds[3] - bounds[0]  # max_x - min_x
            relief_height = bounds[4] - bounds[1]  # max_y - min_y
            base_size = max(diameter * 2, relief_width, relief_height) * 1.5  # Extra margin
            base_height = total_thickness

            print(f"Creating base cuboid: {base_size}x{base_size}x{base_height}")
            base_cuboid = m3d.Manifold.cube([base_size, base_size, base_height])
            base_cuboid = base_cuboid.translate([0, 0, base_height / 2])

            # Extend relief to full coin height using + operator
            extended_relief = relief_mesh + base_cuboid

            # Check if extension was successful
            if extended_relief.status() != m3d.Error.NoError:
                print(f"Extension has issues: {extended_relief.status()}")
                if extended_relief.num_vert() == 0:
                    print("Failed to extend relief - empty mesh")
                    return None
                else:
                    print(f"Proceeding despite extension warning - {extended_relief.num_vert()} vertices")
            elif extended_relief.num_vert() == 0:
                print("Failed to extend relief - empty mesh")
                return None

            # Create full-height coin shape
            full_coin_shape = self._create_coin_shape(shape, diameter, total_thickness)
            full_coin_shape = full_coin_shape.translate([0, 0, total_thickness / 2])

            # Single intersection using XOR operator
            final_mesh = extended_relief ^ full_coin_shape

            # Check if intersection was successful
            if final_mesh.status() != m3d.Error.NoError:
                print(f"Alternative intersection has issues: {final_mesh.status()}")
                if final_mesh.num_vert() == 0:
                    print("Alternative intersection failed - empty mesh")
                    return None
                else:
                    print(f"Proceeding despite intersection warning - {final_mesh.num_vert()} vertices")
            elif final_mesh.num_vert() == 0:
                print("Alternative intersection failed - empty mesh")
                return None

            print(f"Alternative approach successful: {final_mesh.num_vert()} vertices")
            return final_mesh

        except Exception as e:
            print(f"Error in alternative intersection approach: {e}")
            return None

    def _load_stl_to_manifold(self, stl_path: Path) -> m3d.Manifold | None:
        """Load STL file to Manifold using trimesh as recommended bridge."""
        try:
            # Step 1: Load STL using Trimesh
            relief_trimesh = trimesh.load(str(stl_path))

            if not hasattr(relief_trimesh, 'vertices') or not hasattr(relief_trimesh, 'faces'):
                print("Invalid mesh loaded from STL")
                return None

            # Step 2: Extract vertices and faces, ensure correct data types and memory layout
            # Manifold3D requires specific numpy array types with C-contiguous memory layout
            import numpy as np

            # Convert to numpy arrays with the exact types required by Manifold3D
            vertices = np.ascontiguousarray(relief_trimesh.vertices, dtype=np.float32)
            faces = np.ascontiguousarray(relief_trimesh.faces, dtype=np.uint32)

            # Verify the shapes are correct
            if vertices.ndim != 2 or faces.ndim != 2 or faces.shape[1] != 3:
                print(f"Invalid mesh geometry: vertices shape {vertices.shape}, faces shape {faces.shape}")
                return None

            # Step 3: Create Manifold mesh from raw data using the correct API
            # Both vert_properties and tri_verts are required constructor parameters
            mesh = m3d.Mesh(vert_properties=vertices, tri_verts=faces)  # type: ignore[call-arg]
            relief_manifold = m3d.Manifold(mesh)

            print(f"Loaded STL with {len(vertices)} vertices and {len(faces)} faces")
            return relief_manifold

        except Exception as e:
            print(f"Error loading STL to Manifold: {e}")
            import traceback
            traceback.print_exc()
            return None
