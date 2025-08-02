"""
FastAPI Main Application

Modern API server replacing Django for the Coin Maker application.
Uses application factory pattern for clean web/desktop separation.

This module exposes the FastAPI app instance for WSGI/ASGI servers
(uvicorn, gunicorn, etc.) in production deployments.
For direct execution, use web_main.py instead.
"""

from apps.web_app import WebApp

# Create and initialize web application
web_app = WebApp()
web_app.initialize()

# Get the FastAPI app instance
app = web_app.create_fastapi_app()
