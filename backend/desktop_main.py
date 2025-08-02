#!/usr/bin/env python3
"""
Desktop Application Entry Point

Main entry point for running the Coin Maker desktop application.
This starts the application in desktop mode with APScheduler for background tasks.
"""

import logging
import sys
from pathlib import Path


def setup_python_path() -> None:
    """Add backend directory to Python path for imports."""
    backend_dir = Path(__file__).parent
    if str(backend_dir) not in sys.path:
        sys.path.insert(0, str(backend_dir))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

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
