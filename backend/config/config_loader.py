"""
Configuration Loader

Handles loading configuration from multiple sources in proper hierarchy:
1. default.ini (installation directory)
2. settings.ini (app data directory)
3. Environment variables
4. Command line arguments
"""

import configparser
from pathlib import Path
from typing import Any


class ConfigLoader:
    """Loads configuration from multiple sources with proper hierarchy."""

    def __init__(self):
        self._config_data: dict[str, Any] = {}

    def load_config(self, app_data_dir: str | None = None) -> dict[str, Any]:
        """Load configuration from all sources in proper hierarchy.

        Args:
            app_data_dir: Override app data directory path

        Returns:
            Dictionary of configuration values
        """
        self._config_data = {}

        # 1. Load default.ini (lowest priority)
        self._load_default_ini()

        # 2. Load settings.ini (overrides default.ini)
        self._load_settings_ini(app_data_dir)

        # Environment variables and CLI args are handled by Pydantic
        return self._config_data.copy()

    def _load_default_ini(self) -> None:
        """Load default.ini from installation directory."""
        default_ini = self._get_default_ini_path()
        if default_ini and default_ini.exists():
            data = self._load_ini_file(default_ini)
            self._config_data.update(data)

    def _load_settings_ini(self, app_data_dir: str | None = None) -> None:
        """Load settings.ini from app data directory."""
        settings_ini = self._get_settings_ini_path(app_data_dir)
        if settings_ini and settings_ini.exists():
            data = self._load_ini_file(settings_ini)
            self._config_data.update(data)

    def _get_default_ini_path(self) -> Path | None:
        """Get path to default.ini file."""
        try:
            from core.services.path_resolver import PathResolver
            path_resolver = PathResolver()
            return path_resolver.get_app_root() / "default.ini"
        except Exception:
            # Fallback: look for default.ini in current directory or parent
            current = Path.cwd()
            candidates = [current / "default.ini", current.parent / "default.ini"]
            for candidate in candidates:
                if candidate.exists():
                    return candidate
            return None

    def _get_settings_ini_path(self, app_data_dir: str | None = None) -> Path | None:
        """Get path to settings.ini file in app data directory."""
        try:
            # Use provided app_data_dir or fall back to config data or default
            data_dir = app_data_dir or self._config_data.get('app_data_dir', '../data')
            app_data_path = Path(data_dir)
            settings_dir = app_data_path / "settings"
            settings_dir.mkdir(parents=True, exist_ok=True)
            return settings_dir / "settings.ini"
        except Exception:
            return None

    def _load_ini_file(self, ini_path: Path) -> dict[str, Any]:
        """Load configuration from an INI file.

        Args:
            ini_path: Path to the INI file

        Returns:
            Dictionary of configuration values
        """
        config = configparser.ConfigParser()
        config.read(ini_path)

        data: dict[str, Any] = {}

        # Process each section
        for section_name in config.sections():
            section = config[section_name]

            for key, value in section.items():
                # Parse value based on field type
                parsed_value = self._parse_ini_value(key, value)
                if parsed_value is not None:
                    data[key] = parsed_value

        return data

    def _parse_ini_value(self, key: str, value: str) -> Any:
        """Parse INI value to appropriate Python type.

        Args:
            key: Field name
            value: Raw string value from INI

        Returns:
            Parsed value or None if parsing fails
        """
        if not value:
            return None

        # Handle boolean values
        if value.lower() in ('true', 'yes', '1', 'on'):
            return True
        elif value.lower() in ('false', 'no', '0', 'off'):
            return False

        # Handle numeric values
        try:
            if '.' in value:
                return float(value)
            else:
                return int(value)
        except ValueError:
            pass

        # Handle list values (comma-separated)
        if any(list_field in key for list_field in ['cors_origins', 'chromium_flags']):
            if ',' in value:
                return [item.strip() for item in value.split(',') if item.strip()]

        # Return as string
        return value

    def create_settings_ini_template(self, app_data_dir: str | None = None) -> Path:
        """Create a template settings.ini file if it doesn't exist.

        Args:
            app_data_dir: Override app data directory path

        Returns:
            Path to the created or existing settings.ini file
        """
        settings_ini = self._get_settings_ini_path(app_data_dir)
        if not settings_ini:
            raise ValueError("Could not determine settings.ini path")

        if not settings_ini.exists():
            # Create basic template
            template_content = """# Coin Maker Settings
# This file overrides default.ini settings
# Uncomment and modify values as needed

[general]
# debug = true
# debug_port = 9222

[server]
# host = 127.0.0.1
# port = 8001

[desktop]
# pywebview_gui = qt
# qtwebengine_chromium_flags = --enable-gpu --ignore-gpu-blocklist --use-gl=angle
# chromium_flags = --enable-gpu,--enable-webgl,--enable-webgl2
"""
            settings_ini.write_text(template_content)

        return settings_ini
