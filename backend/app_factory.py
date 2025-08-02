"""
FastAPI Application Factory

Creates FastAPI applications with different configurations for web and desktop modes.
Provides clean separation between web/desktop app initialization and integrates
with the BaseApp lifecycle.
"""

from typing import TYPE_CHECKING

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

from api.routes.router import create_api_router
from config.factory import Settings, create_settings

if TYPE_CHECKING:
    from core.base_app import BaseApp


def create_app(desktop_mode: bool = False, settings_override: Settings | None = None, base_app: 'BaseApp | None' = None) -> FastAPI:
    """
    Create FastAPI application with mode-specific configuration.

    Args:
        desktop_mode: If True, create desktop-optimized app
        settings_override: Optional settings instance to use instead of auto-detection
        base_app: Optional BaseApp instance to integrate with lifecycle management

    Returns:
        Configured FastAPI application
    """
    # Determine settings - prefer base_app, then override, then auto-detect
    if base_app and base_app.settings:
        app_settings = base_app.settings
    elif settings_override:
        app_settings = settings_override
    else:
        app_settings = create_settings(desktop_mode=desktop_mode)

    # Create FastAPI application with mode-specific config
    is_desktop = not app_settings.use_celery
    app_title = "Coin Maker Desktop" if is_desktop else "Coin Maker API"

    app = FastAPI(
        title=app_title,
        description="3D Coin Maker - Generate 3D printable coins from images",
        version="1.0.0",
        debug=app_settings.debug,
        docs_url="/docs" if app_settings.debug else None,
        redoc_url="/redoc" if app_settings.debug else None,
    )

    # Store reference to base app for lifecycle integration
    if base_app:
        app.state.base_app = base_app
        # Make services available to FastAPI dependencies if base app is initialized
        if base_app.is_initialized and base_app.services:
            app.state.services = base_app.services

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=app_settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["*"],
    )

    # Configure exception handlers
    _configure_exception_handlers(app)

    # Configure routes
    _configure_routes(app, app_settings, base_app)

    return app


def _configure_exception_handlers(app: FastAPI) -> None:
    """Configure custom exception handlers."""

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Handle validation errors with detailed messages."""
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": "Validation failed",
                "detail": exc.errors(),
                "body": exc.body if hasattr(exc, 'body') else None
            }
        )

    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError):
        """Handle ValueError exceptions."""
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": str(exc)}
        )


def _configure_routes(app: FastAPI, app_settings: Settings, base_app: 'BaseApp | None' = None) -> None:
    """Configure API routes."""

    # Define route prefix based on mode
    is_desktop = not app_settings.use_celery
    route_prefix = "" if is_desktop else "/api"

    # Include API routes
    api_router = create_api_router(route_prefix)
    app.include_router(api_router)

    # Desktop-specific routes
    if is_desktop:
        @app.get("/")
        async def root():
            """Root endpoint redirects to frontend in desktop mode."""
            # Use base_app services if available, otherwise create temporary ones
            if base_app and base_app.services:
                path_resolver = base_app.services.get_path_resolver()
            else:
                # Fallback to temporary service container
                from core.service_container import ServiceContainer
                services = ServiceContainer(app_settings)
                path_resolver = services.get_path_resolver()

            if path_resolver.is_frontend_build_available():
                return FileResponse(path_resolver.get_frontend_build_dir() / "index.html")
            else:
                return {"message": "Coin Maker Desktop API", "docs": "/docs"}
