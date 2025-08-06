"""
Logging Configuration

Provides centralized logging configuration for both web and desktop modes.
Creates log files in logs/ directory and configures console output.
"""

import logging
import logging.handlers
import sys
from pathlib import Path


def setup_logging(
    log_level: str = "INFO",
    log_dir: Path | None = None,
    app_name: str = "coin_maker"
) -> None:
    """
    Configure application logging with both file and console handlers.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory for log files (defaults to logs/ in project root)
        app_name: Application name for log file naming
    """
    # Determine log directory
    if log_dir is None:
        # Default to logs/ directory in project root
        project_root = Path(__file__).parent.parent.parent
        log_dir = project_root / "logs"

    # Create logs directory if it doesn't exist
    log_dir.mkdir(exist_ok=True)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))

    # Remove any existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
    )
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Console handler (stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG if log_level == logging.DEBUG else logging.INFO)
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # Main application log file (rotating)
    app_log_file = log_dir / f"{app_name}.log"
    file_handler = logging.handlers.RotatingFileHandler(
        app_log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)
    root_logger.addHandler(file_handler)

    # Error log file (errors and critical only)
    error_log_file = log_dir / f"{app_name}_errors.log"
    error_handler = logging.handlers.RotatingFileHandler(
        error_log_file,
        maxBytes=5 * 1024 * 1024,  # 5MB
        backupCount=3,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(detailed_formatter)
    root_logger.addHandler(error_handler)

    # Log the configuration
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured - Level: {log_level}")
    logger.info(f"Log directory: {log_dir}")
    logger.info(f"Application log: {app_log_file}")
    logger.info(f"Error log: {error_log_file}")

    # Also configure uvicorn logger if present
    uvicorn_logger = logging.getLogger("uvicorn")
    if uvicorn_logger:
        # Remove uvicorn's default handlers to use our configuration
        uvicorn_logger.handlers = []
        uvicorn_logger.propagate = True

    # Configure fastapi logger
    fastapi_logger = logging.getLogger("fastapi")
    if fastapi_logger:
        fastapi_logger.propagate = True


def get_log_files(log_dir: Path | None = None, app_name: str = "coin_maker") -> dict[str, Path]:
    """
    Get paths to current log files.

    Args:
        log_dir: Directory for log files (defaults to logs/ in project root)
        app_name: Application name for log file naming

    Returns:
        Dictionary mapping log types to file paths
    """
    if log_dir is None:
        project_root = Path(__file__).parent.parent.parent
        log_dir = project_root / "logs"

    return {
        "app": log_dir / f"{app_name}.log",
        "error": log_dir / f"{app_name}_errors.log"
    }


def tail_log_file(log_file: Path, lines: int = 50) -> list[str]:
    """
    Get the last N lines from a log file.

    Args:
        log_file: Path to log file
        lines: Number of lines to retrieve

    Returns:
        List of log lines
    """
    if not log_file.exists():
        return []

    try:
        with open(log_file, encoding='utf-8') as f:
            # Read all lines and return the last N
            all_lines = f.readlines()
            return [line.rstrip() for line in all_lines[-lines:]]
    except Exception as e:
        return [f"Error reading log file: {e}"]


def setup_desktop_logging(debug: bool = True) -> None:
    """
    Setup logging specifically for desktop application.
    Uses user's home directory for logs to ensure AppImage compatibility.

    Args:
        debug: Whether to enable debug level logging
    """
    import os
    
    log_level = "DEBUG" if debug else "INFO"
    
    # For desktop applications (especially AppImage), use a user-writable directory
    # Try user's home directory first, fall back to temp directory
    home_dir = Path.home()
    desktop_log_dir = home_dir / ".coin-maker" / "logs"
    
    # Fallback to temp directory if home is not writable
    try:
        desktop_log_dir.mkdir(parents=True, exist_ok=True)
    except (OSError, PermissionError):
        import tempfile
        desktop_log_dir = Path(tempfile.gettempdir()) / "coin-maker-logs"
        desktop_log_dir.mkdir(parents=True, exist_ok=True)
    
    setup_logging(log_level=log_level, log_dir=desktop_log_dir, app_name="coin_maker_desktop")


def setup_web_logging(debug: bool = False) -> None:
    """
    Setup logging specifically for web application.

    Args:
        debug: Whether to enable debug level logging
    """
    log_level = "DEBUG" if debug else "INFO"
    setup_logging(log_level=log_level, app_name="coin_maker_web")


if __name__ == "__main__":
    # Test the logging configuration
    setup_logging(log_level="DEBUG", app_name="test")

    logger = logging.getLogger(__name__)
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")

    print("\nLog files created:")
    log_files = get_log_files(app_name="test")
    for log_type, log_path in log_files.items():
        print(f"  {log_type}: {log_path}")
        if log_path.exists():
            print(f"    Size: {log_path.stat().st_size} bytes")
