#!/usr/bin/env python3
"""
Desktop Application Entry Point

Main entry point for running the Coin Maker desktop application.
This starts the application in desktop mode with APScheduler for background tasks.
"""

import logging
import os
import sys
from pathlib import Path


def setup_python_path() -> None:
    """Add backend directory to Python path for imports."""
    backend_dir = Path(__file__).parent
    if str(backend_dir) not in sys.path:
        sys.path.insert(0, str(backend_dir))


def setup_desktop_environment() -> None:
    """Set environment variables for desktop mode."""
    os.environ['COIN_MAKER_DESKTOP_MODE'] = 'true'
    
    # Enable GPU acceleration for Chromium/PyWebView
    os.environ['PYWEBVIEW_GUI'] = 'qt'  # Use Qt backend which often has better GPU support
    
    # Qt/WebEngine GPU environment variables (use ANGLE as required by platform)
    os.environ['QTWEBENGINE_CHROMIUM_FLAGS'] = '--enable-gpu --ignore-gpu-blocklist --use-gl=angle'
    
    # Compatible Chromium GPU flags that work with ANGLE
    chromium_flags = [
        '--enable-gpu',
        '--enable-webgl',
        '--enable-webgl2',
        '--ignore-gpu-blocklist',
        '--enable-gpu-rasterization',
        '--use-gl=angle',  # Use ANGLE as required by the platform
        '--enable-accelerated-2d-canvas',
        '--disable-gpu-sandbox'
    ]
    os.environ['CHROMIUM_FLAGS'] = ' '.join(chromium_flags)

# Set up desktop environment
setup_desktop_environment()

# Configure logging
from core.logging_config import setup_desktop_logging
setup_desktop_logging(debug=False)

logger = logging.getLogger(__name__)


def main():
    """Main entry point for desktop application."""
    setup_python_path()

    # Import after path setup
    from apps.desktop_app import DesktopApp

    try:
        logger.info("Starting Coin Maker Desktop Application...")

        # Create and initialize desktop app
        app = DesktopApp()
        app.initialize()

        # Run the application
        app.run()

    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)
    finally:
        logger.info("Desktop application stopped")


if __name__ == "__main__":
    main()
