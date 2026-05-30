"""
Path Resolution Service

Provides a single interface for managing application paths including
data directories, install paths, and resource locations.
"""

from pathlib import Path


class PathResolver:
    """Service for resolving application paths."""

    def __init__(self, app_data_dir: str | Path, install_path: str | Path, frontend_path: str | Path | None = None):
        """Initialize path resolver with explicit directory paths.

        Args:
            app_data_dir: Directory for application data (generations, logs, settings, etc.)
            install_path: Root directory of the application installation
            frontend_path: Optional override for frontend directory (useful in development mode)
        """
        self._app_data_dir = Path(app_data_dir)
        self._install_path = Path(install_path)
        self._frontend_path = Path(frontend_path) if frontend_path else None

        # Ensure app data directory exists
        self._app_data_dir.mkdir(parents=True, exist_ok=True)

    @property
    def app_data_dir(self) -> Path:
        """Get the application data directory."""
        return self._app_data_dir

    @property
    def install_path(self) -> Path:
        """Get the application install directory."""
        return self._install_path

    @property
    def generations_dir(self) -> Path:
        """Get the generations directory for file storage."""
        generations_path = self._app_data_dir / "generations"
        generations_path.mkdir(parents=True, exist_ok=True)
        return generations_path

    @property
    def logs_dir(self) -> Path:
        """Get the logs directory."""
        logs_path = self._app_data_dir / "logs"
        logs_path.mkdir(parents=True, exist_ok=True)
        return logs_path

    @property
    def settings_dir(self) -> Path:
        """Get the settings directory."""
        settings_path = self._app_data_dir / "settings"
        settings_path.mkdir(parents=True, exist_ok=True)
        return settings_path

    @property
    def frontend_dir(self) -> Path:
        """Get the frontend directory path."""
        if self._frontend_path:
            return self._frontend_path
        return self._install_path / "frontend"

    @property
    def config_dir(self) -> Path:
        """Get the configuration directory."""
        return self._install_path / "config"

    def get_generation_file_path(self, generation_id: str, filename: str) -> Path:
        """Get file path for a specific generation and filename, ensuring generation dir exists."""
        generation_dir = self.get_generation_dir(generation_id)
        return generation_dir / filename

    def get_generation_dir(self, generation_id: str) -> Path:
        """Get generation directory, ensuring it exists."""
        generation_dir = self.generations_dir / generation_id
        generation_dir.mkdir(parents=True, exist_ok=True)
        return generation_dir

    @property
    def is_frontend_available(self) -> bool:
        """Check if frontend is available."""
        return self.frontend_dir.exists() and (self.frontend_dir / "index.html").exists()
