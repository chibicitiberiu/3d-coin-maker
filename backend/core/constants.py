"""
Application Constants

Business rules and algorithm constants that should not be configurable.
These are separated from deployment-specific configuration in config/settings.py.
"""


class ValidationConstants:
    """Constants for input validation - business rules."""

    # Filename constraints
    MAX_FILENAME_LENGTH = 255

    # Image processing limits - business rules
    BRIGHTNESS_MIN = -100
    BRIGHTNESS_MAX = 100
    CONTRAST_MIN = 0
    CONTRAST_MAX = 300

    # Coin parameter defaults - business defaults
    DEFAULT_DIAMETER = 30.0
    DEFAULT_THICKNESS = 3.0
    DEFAULT_RELIEF_DEPTH = 1.0

    # Image format constraints
    SUPPORTED_IMAGE_FORMATS = {'jpg', 'jpeg', 'png', 'bmp', 'tiff', 'webp'}

    # Processing pipeline constants
    MIN_IMAGE_DIMENSION = 16   # Minimum width/height in pixels
    MAX_IMAGE_DIMENSION = 4096 # Maximum width/height in pixels


class PerformanceConstants:
    """Performance optimization constants."""

    # File I/O optimization
    FILE_CHUNK_SIZE = 8192  # 8KB chunks for file operations


class ProcessingConstants:
    """Constants for image and STL processing."""

    # Image processing defaults
    DEFAULT_CONTRAST_VALUE = 200
    DEFAULT_BRIGHTNESS_FACTOR = 100.0
    GAMMA_LUT_SIZE = 256
    GAMMA_LUT_MAX_VALUE = 255

    # 3D mesh generation constants
    DEFAULT_RELIEF_BASE_THICKNESS = 0.1
    DEFAULT_CYLINDER_RESOLUTION = 128
    DEFAULT_MESH_SCALE_FACTOR = 1.0
    IMAGE_RESIZE_TARGET = 2048

    # Progress reporting intervals
    PROGRESS_IMAGE_START = 10
    PROGRESS_HEIGHTMAP = 20
    PROGRESS_MESH_CREATION = 30
    PROGRESS_BOOLEAN_OPS = 60
    PROGRESS_STL_EXPORT = 90
    PROGRESS_COMPLETE = 100


# Note: The following have been moved to configuration (config/settings.py):
# - MAX_FILE_SIZE_BYTES → settings.max_file_size_mb
# - DEFAULT_MAX_GENERATIONS → settings.max_generations_per_hour
# - DEFAULT_TASK_TIMEOUT → settings.image_processing_timeout_seconds / stl_generation_timeout_seconds
#
# This separation ensures business rules (constants) are separate from
# deployment policies (configuration).
