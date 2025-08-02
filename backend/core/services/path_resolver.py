"""
Path Resolution Service

Handles path resolution differences between web and desktop deployment modes.
Provides a single interface for managing frontend build paths, temp directories,
and other path-related concerns.
"""

import sys
from pathlib import Path


class PathResolver:
    """Service for resolving paths in web vs desktop contexts."""

    def __init__(self, desktop_mode: bool = False, temp_dir_setting: str | None = None):
        """Initialize path resolver with explicit mode configuration.

        Args:
            desktop_mode: Whether running in desktop mode
            temp_dir_setting: Temporary directory path (for web mode)
        """
        self._desktop_mode = desktop_mode
        self._temp_dir_setting = temp_dir_setting
        self._app_root = self._detect_app_root()

    def _detect_app_root(self) -> Path:
        """Detect the application root directory."""
        if self._desktop_mode:
            # In desktop mode, assume we're running from the backend directory
            # or from a PyInstaller bundle
            if getattr(sys, 'frozen', False):
                # PyInstaller bundle
                return Path(sys.executable).parent
            else:
                # Development mode - find the project root
                current = Path(__file__).parent
                while current.parent != current:
                    if (current / 'backend').exists() and (current / 'frontend').exists():
                        return current
                    current = current.parent
                # Fallback to backend directory
                return Path(__file__).parent.parent.parent
        else:
            # Web mode - assume standard deployment structure
            return Path(__file__).parent.parent.parent

    @property
    def is_desktop_mode(self) -> bool:
        """Check if running in desktop mode."""
        return self._desktop_mode

    @property
    def app_root(self) -> Path:
        """Get the application root directory."""
        return self._app_root

    def get_temp_dir(self, temp_dir_setting: str | None = None) -> Path:
        """Get the temporary files directory."""
        if self._desktop_mode:
            # Desktop mode - use local temp directory
            temp_path = self._app_root / "temp"
        else:
            # Web mode - use configured temp directory
            configured_temp = temp_dir_setting or self._temp_dir_setting or "/tmp/coin_maker"
            temp_path = Path(configured_temp)

        # Ensure directory exists
        temp_path.mkdir(parents=True, exist_ok=True)
        return temp_path

    def get_frontend_build_dir(self) -> Path:
        """Get the frontend build directory path."""
        if self._desktop_mode:
            # Desktop mode - frontend build is relative to app root
            build_path = self._app_root / "frontend" / "build"
        else:
            # Web mode - build is typically served by separate container
            # This path may not exist in web mode as frontend is served separately
            build_path = self._app_root / "frontend" / "build"

        return build_path

    def get_static_dir(self) -> Path:
        """Get the static files directory."""
        if self._desktop_mode:
            # Desktop mode - static files are bundled with app
            return self._app_root / "static"
        else:
            # Web mode - standard static directory
            return self._app_root / "backend" / "static"

    def get_templates_dir(self) -> Path:
        """Get the templates directory."""
        return self._app_root / "backend" / "core" / "templates"

    def resolve_file_path(self, generation_id: str, file_type: str) -> Path:
        """Resolve file path for a specific generation and file type."""
        temp_dir = self.get_temp_dir()
        generation_dir = temp_dir / generation_id

        # File type to filename mapping
        file_extensions = {
            'original': 'original.png',
            'processed': 'processed.png',
            'heightmap': 'heightmap.png',
            'stl': 'coin.stl'
        }

        filename = file_extensions.get(file_type, f"{file_type}.dat")
        return generation_dir / filename

    def ensure_generation_dir(self, generation_id: str) -> Path:
        """Ensure generation directory exists and return its path."""
        generation_dir = self.get_temp_dir() / generation_id
        generation_dir.mkdir(parents=True, exist_ok=True)
        return generation_dir

    def get_log_dir(self) -> Path:
        """Get the logs directory."""
        if self._desktop_mode:
            # Desktop mode - logs in app directory or user data
            log_dir = self._app_root / "logs"
        else:
            # Web mode - standard log location
            log_dir = Path("/var/log/coin_maker")

        # Ensure directory exists
        log_dir.mkdir(parents=True, exist_ok=True)
        return log_dir

    def get_config_dir(self) -> Path:
        """Get the configuration directory."""
        return self._app_root / "config"

    def is_frontend_build_available(self) -> bool:
        """Check if frontend build is available."""
        build_dir = self.get_frontend_build_dir()
        return build_dir.exists() and (build_dir / "index.html").exists()


# Global path resolver instance for backward compatibility
# This will be replaced when migrating to full dependency injection architecture.
# Current usage: FileSystemStorage, app factories
# Migration path: Update services to receive PathResolver via constructor injection
path_resolver = PathResolver()


# Helper functions for backward compatibility with configuration system
# These provide a bridge between old procedural code and new service architecture
def get_temp_dir() -> Path:
    """Get temporary directory path."""
    return path_resolver.get_temp_dir()


def get_frontend_build_dir() -> Path:
    """Get frontend build directory path."""
    return path_resolver.get_frontend_build_dir()


def resolve_file_path(generation_id: str, file_type: str) -> Path:
    """Resolve file path for generation and file type."""
    return path_resolver.resolve_file_path(generation_id, file_type)
