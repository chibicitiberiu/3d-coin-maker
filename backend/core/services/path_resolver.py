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

    def __init__(self, desktop_mode: bool = False, app_data_dir_setting: str | None = None):
        """Initialize path resolver with explicit mode configuration.

        Args:
            desktop_mode: Whether running in desktop mode
            app_data_dir_setting: Application data directory path
        """
        self._desktop_mode = desktop_mode
        self._app_data_dir_setting = app_data_dir_setting
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

    def get_app_data_dir(self, app_data_dir_setting: str | None = None) -> Path:
        """Get the application data directory."""
        from config.settings import Settings
        settings = Settings()
        
        configured_dir = app_data_dir_setting or self._app_data_dir_setting or settings.app_data_dir
        app_data_path = Path(configured_dir)
        
        # If it's a relative path, resolve it relative to the backend directory
        if not app_data_path.is_absolute():
            app_data_path = self._app_root / app_data_path
        
        # Ensure directory exists
        app_data_path.mkdir(parents=True, exist_ok=True)
        return app_data_path
    
    def get_generations_dir(self, app_data_dir_setting: str | None = None) -> Path:
        """Get the generations directory for file storage."""
        generations_path = self.get_app_data_dir(app_data_dir_setting) / "generations"
        
        # Ensure directory exists
        generations_path.mkdir(parents=True, exist_ok=True)
        return generations_path
    
    def get_logs_dir(self, app_data_dir_setting: str | None = None) -> Path:
        """Get the logs directory."""
        logs_path = self.get_app_data_dir(app_data_dir_setting) / "logs"
        
        # Ensure directory exists
        logs_path.mkdir(parents=True, exist_ok=True)
        return logs_path
    
    def get_settings_dir(self, app_data_dir_setting: str | None = None) -> Path:
        """Get the settings directory."""
        settings_path = self.get_app_data_dir(app_data_dir_setting) / "settings"
        
        # Ensure directory exists
        settings_path.mkdir(parents=True, exist_ok=True)
        return settings_path

    def get_frontend_dir(self) -> Path:
        """Get the frontend source directory path."""
        return self._app_root / "frontend"

    def get_frontend_build_dir(self) -> Path:
        """Get the frontend build directory path."""
        if self._desktop_mode:
            # Desktop mode - frontend build is in build directory
            build_path = self._app_root / "build" / "frontend"
        else:
            # Web mode - build is typically served by separate container
            # This path may not exist in web mode as frontend is served separately
            build_path = self._app_root / "build" / "frontend"

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
        generations_dir = self.get_generations_dir()
        generation_dir = generations_dir / generation_id

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
        generation_dir = self.get_generations_dir() / generation_id
        generation_dir.mkdir(parents=True, exist_ok=True)
        return generation_dir

    def get_log_dir(self) -> Path:
        """Get the logs directory (legacy method, use get_logs_dir instead)."""
        return self.get_logs_dir()

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
def get_generations_dir() -> Path:
    """Get generations directory path."""
    return path_resolver.get_generations_dir()


def get_frontend_build_dir() -> Path:
    """Get frontend build directory path."""
    return path_resolver.get_frontend_build_dir()


def resolve_file_path(generation_id: str, file_type: str) -> Path:
    """Resolve file path for generation and file type."""
    return path_resolver.resolve_file_path(generation_id, file_type)
