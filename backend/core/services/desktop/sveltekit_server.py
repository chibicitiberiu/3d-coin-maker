"""
SvelteKit Server Management

Manages the SvelteKit frontend server for desktop application.
Handles starting, stopping, and communicating with the SvelteKit development
or production server.
"""

import logging
import subprocess
import time
import threading
import requests
import http.server
import socketserver
from pathlib import Path
from typing import Optional

from core.services.path_resolver import PathResolver

logger = logging.getLogger(__name__)


class SvelteKitServer:
    """Manages SvelteKit frontend server for desktop application."""
    
    def __init__(self, frontend_dir: Path, port: int, backend_port: int, path_resolver: Optional[PathResolver] = None):
        """Initialize SvelteKit server manager.
        
        Args:
            frontend_dir: Path to the frontend directory
            port: Port for the SvelteKit server
            backend_port: Port of the FastAPI backend (for API proxy)
            path_resolver: Path resolver for build directory location
        """
        self.frontend_dir = frontend_dir
        self.port = port
        self.backend_port = backend_port
        self.path_resolver = path_resolver or PathResolver()
        self.process: Optional[subprocess.Popen] = None
        self.static_server: Optional[socketserver.TCPServer] = None
        self.static_thread: Optional[threading.Thread] = None
        self.is_running = False
        
    def _check_dependencies(self) -> bool:
        """Check if required dependencies are available."""
        # Check if frontend directory exists
        if not self.frontend_dir.exists():
            logger.error(f"Frontend directory not found: {self.frontend_dir}")
            return False
        
        # Check if package.json exists
        package_json = self.frontend_dir / "package.json"
        if not package_json.exists():
            logger.error(f"package.json not found: {package_json}")
            return False
        
        # Check if node_modules exists or if we can run npm/pnpm
        node_modules = self.frontend_dir / "node_modules"
        if not node_modules.exists():
            logger.warning("node_modules not found - you may need to run 'pnpm install' first")
        
        return True
    
    def _get_start_command(self) -> list[str]:
        """Get the command to start the SvelteKit server.
        
        Returns:
            Command list for subprocess
        """
        # Check if we have a complete build (production mode with server manifest)
        build_dir = self.path_resolver.get_frontend_build_dir()
        
        # Check for both server and client output needed for preview mode
        server_manifest = self.frontend_dir / ".svelte-kit" / "output" / "server" / "manifest.js"
        client_output = self.frontend_dir / ".svelte-kit" / "output" / "client"
        
        if build_dir.exists() and server_manifest.exists() and client_output.exists():
            # Complete build - use vite preview
            logger.info("Found complete build with both server and client output - starting in preview mode")
            return ["pnpm", "run", "preview", "--port", str(self.port), "--host", "127.0.0.1"]
        elif build_dir.exists():
            # Static build exists - use simple static server for fast startup
            logger.info("Found static build directory - using fast static server for desktop")
            return None  # Will use built-in static server
        else:
            # No build directory - development mode
            logger.info("No build directory found - starting in development mode")
            return ["pnpm", "run", "dev", "--port", str(self.port), "--host", "127.0.0.1"]
    
    def _start_static_server(self) -> bool:
        """Start a simple static HTTP server for built SvelteKit files.
        
        Returns:
            True if started successfully, False otherwise
        """
        try:
            build_dir = self.path_resolver.get_frontend_build_dir()
            logger.info(f"Starting static server for {build_dir} on port {self.port}")
            
            class StaticHandler(http.server.SimpleHTTPRequestHandler):
                def __init__(self, *args, **kwargs):
                    super().__init__(*args, directory=str(build_dir), **kwargs)
                
                def end_headers(self):
                    # Add CORS headers for API requests
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
                    self.send_header('Access-Control-Allow-Headers', 'Content-Type')
                    super().end_headers()
                
                def do_GET(self):
                    # Handle SPA routing - serve index.html for routes that don't exist as files
                    if not Path(str(build_dir) + self.path).exists() and not self.path.startswith('/api/'):
                        # Check if it's likely a frontend route (not a file with extension)
                        if '.' not in Path(self.path).name or self.path.endswith('/'):
                            self.path = '/index.html'
                    return super().do_GET()
                
                def do_OPTIONS(self):
                    # Handle preflight CORS requests
                    self.send_response(200)
                    self.end_headers()
                
                def log_message(self, format, *args):
                    # Suppress default HTTP server logs to avoid noise
                    pass
            
            # Create and start the server
            self.static_server = socketserver.TCPServer(("127.0.0.1", self.port), StaticHandler)
            self.static_server.timeout = 1  # Allow for clean shutdown
            
            # Start server in a separate thread
            def serve_forever():
                try:
                    self.static_server.serve_forever()
                except Exception as e:
                    if self.is_running:  # Only log if we expect the server to be running
                        logger.error(f"Static server error: {e}")
            
            self.static_thread = threading.Thread(target=serve_forever, daemon=True)
            self.static_thread.start()
            
            # Wait a moment and check if server is ready
            time.sleep(0.5)
            if self._wait_for_server(timeout=10):
                self.is_running = True
                logger.info(f"Static server started successfully on port {self.port}")
                return True
            else:
                logger.error("Static server did not become ready in time")
                self._stop_static_server()
                return False
                
        except Exception as e:
            logger.error(f"Failed to start static server: {e}")
            return False
    
    def _stop_static_server(self) -> None:
        """Stop the static HTTP server."""
        if self.static_server:
            logger.info("Stopping static server...")
            try:
                self.static_server.shutdown()
                self.static_server.server_close()
            except Exception as e:
                logger.error(f"Error stopping static server: {e}")
            finally:
                self.static_server = None
        
        if self.static_thread and self.static_thread.is_alive():
            try:
                self.static_thread.join(timeout=5)
            except Exception as e:
                logger.error(f"Error joining static server thread: {e}")
            finally:
                self.static_thread = None
    
    def start(self) -> bool:
        """Start the SvelteKit server.
        
        Returns:
            True if started successfully, False otherwise
        """
        if self.is_running:
            logger.warning("SvelteKit server is already running")
            return True
        
        if not self._check_dependencies():
            return False
        
        try:
            # Get the start command
            cmd = self._get_start_command()
            
            # Check if we should use static server (cmd is None)
            if cmd is None:
                return self._start_static_server()
            
            logger.info(f"Starting SvelteKit server: {' '.join(cmd)}")
            
            # Set environment variables for the SvelteKit server
            env = {
                "PORT": str(self.port),
                "PUBLIC_API_BASE_URL": f"http://127.0.0.1:{self.backend_port}",
                "BACKEND_URL": f"http://127.0.0.1:{self.backend_port}",
                "NODE_ENV": "production"  # Use production mode for desktop
            }
            
            # Start the process
            self.process = subprocess.Popen(
                cmd,
                cwd=self.frontend_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env={**dict(subprocess.os.environ), **env}
            )
            
            # Wait a moment and check if process is still running
            time.sleep(2)
            if self.process.poll() is not None:
                # Process died
                stdout, stderr = self.process.communicate()
                logger.error(f"SvelteKit server failed to start")
                logger.error(f"STDOUT: {stdout}")
                logger.error(f"STDERR: {stderr}")
                return False
            
            # Wait for server to be ready
            if self._wait_for_server():
                self.is_running = True
                logger.info(f"SvelteKit server started on port {self.port}")
                return True
            else:
                logger.error("SvelteKit server did not become ready in time")
                self.stop()
                return False
                
        except Exception as e:
            logger.error(f"Failed to start SvelteKit server: {e}")
            return False
    
    def _wait_for_server(self, timeout: int = 30) -> bool:
        """Wait for the SvelteKit server to be ready.
        
        Args:
            timeout: Maximum time to wait in seconds
            
        Returns:
            True if server is ready, False if timeout
        """
        url = f"http://127.0.0.1:{self.port}"
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                response = requests.get(url, timeout=2)
                if response.status_code == 200:
                    logger.info(f"SvelteKit server is ready at {url}")
                    return True
            except requests.exceptions.RequestException:
                pass  # Server not ready yet
            
            time.sleep(1)
        
        logger.error(f"SvelteKit server did not respond within {timeout} seconds")
        return False
    
    def stop(self) -> None:
        """Stop the SvelteKit server."""
        if not self.is_running:
            return
        
        logger.info("Stopping SvelteKit server...")
        
        try:
            # Stop static server if running
            if self.static_server:
                self._stop_static_server()
            
            # Stop process if running
            if self.process:
                # Terminate the process
                self.process.terminate()
                
                # Wait for it to finish
                try:
                    self.process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    # Force kill if it doesn't stop gracefully
                    logger.warning("SvelteKit server did not stop gracefully, force killing...")
                    self.process.kill()
                    self.process.wait()
                
                self.process = None
            
            self.is_running = False
            logger.info("SvelteKit server stopped")
            
        except Exception as e:
            logger.error(f"Error stopping SvelteKit server: {e}")
    
    def get_url(self) -> str:
        """Get the URL of the SvelteKit server.
        
        Returns:
            Full URL of the frontend server
        """
        return f"http://127.0.0.1:{self.port}"
    
    def is_healthy(self) -> bool:
        """Check if the SvelteKit server is healthy.
        
        Returns:
            True if server is running and responding
        """
        if not self.is_running:
            return False
        
        # Check if process is still alive (for non-static servers)
        if self.process and self.process.poll() is not None:
            logger.warning("SvelteKit server process has died")
            self.is_running = False
            return False
        
        # Check if static server thread is still alive (for static servers)
        if self.static_server and self.static_thread and not self.static_thread.is_alive():
            logger.warning("Static server thread has died")
            self.is_running = False
            return False
        
        # Check if server responds
        try:
            response = requests.get(self.get_url(), timeout=5)
            return response.status_code == 200
        except requests.exceptions.RequestException as e:
            logger.warning(f"SvelteKit server health check failed: {e}")
            return False


def test_sveltekit_server():
    """Test the SvelteKit server manager."""
    from pathlib import Path
    
    # Assume frontend is in the parent directory
    frontend_dir = Path(__file__).parent.parent.parent.parent / "frontend"
    
    if not frontend_dir.exists():
        print(f"Frontend directory not found: {frontend_dir}")
        return
    
    server = SvelteKitServer(frontend_dir, 5173, 8000)
    
    print("Starting SvelteKit server...")
    if server.start():
        print(f"Server started at: {server.get_url()}")
        print(f"Server healthy: {server.is_healthy()}")
        
        # Keep running for a bit
        time.sleep(5)
        
        print("Stopping server...")
        server.stop()
    else:
        print("Failed to start server")


if __name__ == "__main__":
    test_sveltekit_server()