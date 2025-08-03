#!/usr/bin/env python3
"""
Debug script for desktop application issues
"""

import logging
import time
import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

# Configure detailed logging
from core.logging_config import setup_logging
setup_logging(log_level="DEBUG", app_name="debug_desktop")

def main():
    print("=== COIN MAKER DESKTOP DEBUG ===")
    
    try:
        from apps.desktop_app import DesktopApp
        print("Successfully imported DesktopApp")
        
        # Create and initialize
        app = DesktopApp()
        print("Created DesktopApp instance")
        
        app.initialize()
        print("Initialized DesktopApp")
        
        # Get port info
        backend_port = app._allocated_backend_port
        frontend_port = app._allocated_frontend_port
        
        print(f"Backend port: {backend_port}")
        print(f"Frontend port: {frontend_port}")
        
        # Create FastAPI app
        fastapi_app = app.create_fastapi_app()
        print("Created FastAPI app")
        
        # Test if we can start backend in thread
        import threading
        import uvicorn
        
        def run_backend():
            uvicorn.run(
                fastapi_app,
                host="127.0.0.1",
                port=backend_port,
                log_level="info"
            )
        
        print(f"Starting backend server on port {backend_port}...")
        backend_thread = threading.Thread(target=run_backend, daemon=True)
        backend_thread.start()
        
        # Wait for backend to start
        time.sleep(3)
        
        # Test backend connection
        import requests
        try:
            response = requests.get(f"http://127.0.0.1:{backend_port}/docs", timeout=5)
            print(f"Backend responding: {response.status_code}")
        except Exception as e:
            print(f"Backend not responding: {e}")
        
        # Test health endpoint
        try:
            response = requests.get(f"http://127.0.0.1:{backend_port}/health/", timeout=5)
            print(f"Health endpoint: {response.status_code}")
        except Exception as e:
            print(f"Health endpoint failed: {e}")
        
        # Test other API endpoints that the frontend would use
        try:
            response = requests.get(f"http://127.0.0.1:{backend_port}/upload/", timeout=5)
            print(f"Upload endpoint: {response.status_code}")
        except Exception as e:
            print(f"Upload endpoint failed: {e}")
            
        try:
            response = requests.get(f"http://127.0.0.1:{backend_port}/status/", timeout=5)
            print(f"Status endpoint: {response.status_code}")
        except Exception as e:
            print(f"Status endpoint failed: {e}")
            
        print("Keeping server running for 10 seconds...")
        time.sleep(10)
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()