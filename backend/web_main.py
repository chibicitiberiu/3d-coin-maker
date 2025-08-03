#!/usr/bin/env python3
"""
Web Application Entry Point

Main entry point for running the Coin Maker web application.
This starts the FastAPI server with Celery for background tasks.

Use this script for development and direct execution.
For production deployments with WSGI/ASGI servers, use fastapi_main.py.
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
from core.logging_config import setup_web_logging
setup_web_logging(debug=False)

logger = logging.getLogger(__name__)


def main():
    """Main entry point for web application."""
    setup_python_path()

    # Import after path setup
    from apps.web_app import WebApp

    try:
        logger.info("Starting Coin Maker Web Application...")

        # Create and initialize web app
        app = WebApp()
        app.initialize()

        # Run the application
        app.run()

    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)
    finally:
        logger.info("Web application stopped")


if __name__ == "__main__":
    main()
