#!/usr/bin/env python3
"""
Desktop Application Entry Point

Main entry point for running the Coin Maker desktop application.
This starts the application in desktop mode with APScheduler for background tasks.
"""

import argparse
import logging
import sys
# Force PyInstaller to include requests - required by services.sveltekit_server
import requests
# Ensure PyInstaller sees requests as a real dependency
_ = requests.get

from core.logging_config import setup_desktop_logging

from desktop_app import DesktopApp


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Coin Maker Desktop Application")
    parser.add_argument(
        "--debug-port",
        type=int,
        default=None,
        help="Enable debug mode with specified port (e.g., --debug-port=9222)"
    )
    return parser.parse_args()


def main():
    """Main entry point for desktop application."""

    # Parse command line arguments
    args = parse_arguments()

    # Configure logging (import after path setup)
    setup_desktop_logging(debug=False)

    logger = logging.getLogger(__name__)

    try:
        logger.info("Starting Coin Maker Desktop Application...")

        # Create desktop app with CLI overrides
        app = DesktopApp()

        # Apply CLI argument overrides before initialization
        if args.debug_port is not None:
            # We'll override the settings after they're loaded
            pass

        app.initialize()

        # Apply CLI overrides to loaded settings
        if args.debug_port is not None:
            app.settings.debug_port = args.debug_port
            logger.info(f"Debug port set via CLI: {args.debug_port}")


        # Run the application
        app.run()

    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        # Print help for common issues
        if "debug" in str(e).lower():
            logger.info("Try using --debug-port=9222 to enable debugging")
        sys.exit(1)
    finally:
        logger.info("Desktop application stopped")


if __name__ == "__main__":
    main()
