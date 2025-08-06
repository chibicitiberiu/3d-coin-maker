#!/usr/bin/env python3
"""
Unified Backend Entry Point

Single entry point for the Coin Maker backend that supports:
- Direct execution with uvicorn (--run)
- ASGI server integration (module-level app variable)
- CLI arguments override settings system defaults

Usage:
    python main.py --run                    # Run with settings defaults
    python main.py --run --debug            # Override debug mode
    python main.py --run --scheduler celery # Override scheduler
    gunicorn main:app                       # Production ASGI (uses settings defaults)
"""

import argparse
import logging
import sys
from pathlib import Path


def setup_python_path() -> None:
    """Add backend directory to Python path for imports."""
    backend_dir = Path(__file__).parent
    if str(backend_dir) not in sys.path:
        sys.path.insert(0, str(backend_dir))


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Coin Maker Backend Server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --run                        # Use settings defaults
  python main.py --run --debug                # Override debug mode
  python main.py --run --scheduler celery     # Override scheduler
  gunicorn main:app                           # Production ASGI
        """
    )

    parser.add_argument(
        '--run',
        action='store_true',
        help='Run the server directly with uvicorn'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug mode (overrides settings)'
    )
    parser.add_argument(
        '--scheduler',
        choices=['apscheduler', 'celery'],
        help='Task scheduler to use (overrides settings)'
    )
    parser.add_argument(
        '--host',
        help='Host to bind to (overrides settings)'
    )
    parser.add_argument(
        '--port',
        type=int,
        help='Port to bind to (overrides settings)'
    )

    return parser.parse_args()


def create_web_app(**overrides):
    """Create and initialize WebApp instance with optional setting overrides."""
    from apps.web_app import WebApp
    from config.factory import create_web_settings

    # Create settings using normal settings system
    settings = create_web_settings()

    # Apply any CLI overrides
    for key, value in overrides.items():
        if value is not None:  # Only override if explicitly provided
            if key == 'scheduler':
                settings.use_celery = (value == 'celery')
            else:
                setattr(settings, key, value)

    # Create and initialize web app with settings
    web_app = WebApp(settings=settings)
    web_app.initialize()
    return web_app


def run_server(args: argparse.Namespace) -> None:
    """Run the server directly with uvicorn."""
    # Prepare overrides from CLI args
    overrides = {}
    if args.debug:
        overrides['debug'] = True
    if args.scheduler:
        overrides['scheduler'] = args.scheduler
    if args.host:
        overrides['host'] = args.host
    if args.port:
        overrides['port'] = args.port

    # Create web app with overrides
    web_app = create_web_app(**overrides)

    # Configure logging
    from core.logging_config import setup_web_logging
    setup_web_logging(debug=web_app.settings.debug)

    logger = logging.getLogger(__name__)
    logger.info(f"Starting Coin Maker Backend - Debug: {web_app.settings.debug}, Use Celery: {web_app.settings.use_celery}")

    try:
        # Run the application
        web_app.run()

    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)
    finally:
        logger.info("Backend server stopped")


def main():
    """Main entry point for CLI usage."""
    setup_python_path()

    # Parse arguments
    args = parse_arguments()

    if not args.run:
        print("Error: --run flag is required for direct execution")
        print("For ASGI server usage, import main:app instead")
        sys.exit(1)

    # Run server with parsed configuration
    run_server(args)


def _create_asgi_app():
    """Create ASGI app for server imports - deferred until needed."""
    setup_python_path()
    return create_web_app().create_fastapi_app()

# For ASGI server imports (e.g., gunicorn main:app)
# Uses settings system defaults (no CLI overrides)
app = _create_asgi_app()

if __name__ == "__main__":
    main()
