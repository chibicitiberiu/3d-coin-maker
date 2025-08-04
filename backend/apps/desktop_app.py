"""
Desktop Application Implementation

Provides DesktopApp class for standalone desktop deployment mode.
This implementation is optimized for desktop use with APScheduler for
background tasks and desktop-specific configuration defaults.
"""

import logging
from typing import Optional

from config.factory import create_desktop_settings
from core.base_app import BaseApp
from core.service_container import ServiceContainer
from core.services.desktop import PortManager, SvelteKitServer, PyWebViewWrapper

logger = logging.getLogger(__name__)


class DesktopApp(BaseApp):
    """Desktop application implementation for standalone deployment."""

    def __init__(self, settings=None):
        """Initialize desktop application.

        Args:
            settings: Optional desktop settings instance. If not provided,
                     will create desktop-optimized settings during initialization.
        """
        super().__init__(settings)
        self._fastapi_app = None
        self._port_manager = PortManager()
        self._sveltekit_server = None
        self._pywebview_wrapper = None
        self._allocated_backend_port = None
        self._allocated_frontend_port = None

    def load_config(self) -> None:
        """Load desktop-specific configuration."""
        if not self.settings:
            logger.info("Loading desktop application settings...")
            self.settings = create_desktop_settings()

        # Allocate dynamic ports to avoid conflicts
        self._allocate_ports()

        logger.info(f"Desktop app configured - Backend: {self.settings.host}:{self._allocated_backend_port}")
        logger.info(f"Frontend server will run on port: {self._allocated_frontend_port}")
        logger.info(f"APScheduler enabled (Celery disabled): {not self.settings.use_celery}")
        logger.info(f"App data directory: {self.settings.app_data_dir}")
        logger.info(f"File size limit: {self.settings.max_file_size_mb}MB")

    def _allocate_ports(self) -> None:
        """Allocate dynamic ports for backend and frontend servers."""
        logger.info("Allocating ports for dual-server architecture...")
        
        backend_port, frontend_port = self._port_manager.allocate_ports()
        
        if not backend_port or not frontend_port:
            raise RuntimeError("Failed to allocate required ports for desktop application")
        
        self._allocated_backend_port = backend_port
        self._allocated_frontend_port = frontend_port
        
        # Update settings with allocated backend port
        self.settings.port = backend_port
        
        # Add allocated frontend port to CORS origins
        frontend_origin = f"http://127.0.0.1:{frontend_port}"
        if frontend_origin not in self.settings.cors_origins:
            self.settings.cors_origins.append(frontend_origin)
        
        # Also add localhost variant
        frontend_origin_localhost = f"http://localhost:{frontend_port}"
        if frontend_origin_localhost not in self.settings.cors_origins:
            self.settings.cors_origins.append(frontend_origin_localhost)
        
        logger.info(f"Ports allocated - Backend: {backend_port}, Frontend: {frontend_port}")
        logger.info(f"CORS origins updated: {self.settings.cors_origins}")

    def initialize_services(self) -> None:
        """Initialize desktop-specific services."""
        if not self.settings:
            raise RuntimeError("Settings not loaded - call load_config() first")

        logger.info("Initializing desktop application services...")

        # Create service container with desktop settings
        self.services = ServiceContainer(self.settings)

        # Initialize SvelteKit server manager
        path_resolver = self.services.get_path_resolver()
        frontend_dir = path_resolver.get_frontend_dir()
        
        self._sveltekit_server = SvelteKitServer(
            frontend_dir=frontend_dir,
            port=self._allocated_frontend_port,
            backend_port=self._allocated_backend_port,
            path_resolver=path_resolver
        )

        # Initialize PyWebView wrapper (will be configured after servers start)
        logger.info("Desktop application services initialized")

    def create_fastapi_app(self):
        """Create and configure FastAPI application for desktop mode."""
        if self._fastapi_app:
            return self._fastapi_app

        logger.info("Creating FastAPI application for desktop mode...")

        # Import here to avoid circular imports
        from app_factory import create_app

        # Create FastAPI app with desktop configuration and lifecycle integration
        self._fastapi_app = create_app(
            desktop_mode=True,
            base_app=self
        )

        logger.info("Desktop FastAPI application created")
        return self._fastapi_app

    def run(self) -> None:
        """Run the desktop application with dual-server architecture and PyWebView GUI wrapper."""
        if not self.is_initialized:
            raise RuntimeError("Application not initialized - call initialize() first")

        logger.info("Starting desktop application with dual-server architecture...")
        self._running = True

        try:
            # Start both servers and PyWebView GUI
            self._start_dual_servers()

        except KeyboardInterrupt:
            logger.info("Received shutdown signal")
        except Exception as e:
            logger.error(f"Error running desktop application: {e}")
            raise
        finally:
            self._cleanup_servers()
            self._running = False

    def _start_dual_servers(self) -> None:
        """Start both FastAPI backend and SvelteKit frontend servers, then launch PyWebView GUI."""
        import threading
        import time
        
        logger.info("Starting dual-server architecture...")
        
        # Start FastAPI backend in background thread
        logger.info(f"Starting FastAPI backend on port {self._allocated_backend_port}...")
        backend_thread = threading.Thread(
            target=self._run_backend_server_thread,
            daemon=True
        )
        backend_thread.start()
        
        # Give backend a moment to start
        time.sleep(2)
        
        # Start SvelteKit frontend server
        logger.info(f"Starting SvelteKit frontend on port {self._allocated_frontend_port}...")
        if not self._sveltekit_server.start():
            logger.error("Failed to start SvelteKit server")
            raise RuntimeError("SvelteKit server failed to start")
        
        # Start PyWebView GUI pointing to SvelteKit server
        self._start_pywebview_gui()
    
    def _start_pywebview_gui(self) -> None:
        """Start PyWebView GUI pointing to SvelteKit server."""
        frontend_url = self._sveltekit_server.get_url()
        
        logger.info(f"Starting PyWebView GUI pointing to SvelteKit server: {frontend_url}")
        
        # Check if debugging mode is enabled
        enable_debugging = self._should_enable_debugging()
        debug_port = 9222  # Standard Chrome DevTools port
        
        if enable_debugging:
            logger.info(f"Desktop debugging mode enabled on port {debug_port}")
        
        # Create PyWebView wrapper
        self._pywebview_wrapper = PyWebViewWrapper(
            frontend_url=frontend_url,
            backend_port=self._allocated_backend_port,
            enable_debugging=enable_debugging,
            debug_port=debug_port
        )
        
        # Try to start pywebview
        try:
            if self._pywebview_wrapper.start():
                logger.info("PyWebView GUI started successfully")
            else:
                logger.warning("PyWebView failed to start, falling back to window mode")
                self._run_fallback_window()
                
        except Exception as e:
            logger.error(f"PyWebView startup failed: {e}")
            self._run_fallback_window()
    
    def _cleanup_servers(self) -> None:
        """Clean up both servers and GUI on shutdown."""
        logger.info("Cleaning up servers and GUI...")
        
        if self._pywebview_wrapper:
            self._pywebview_wrapper.stop()
        
        if self._sveltekit_server:
            self._sveltekit_server.stop()
        
        # FastAPI server runs in daemon thread, so it will exit automatically
        logger.info("Server cleanup complete")
    
    def _should_enable_debugging(self) -> bool:
        """Check if desktop debugging should be enabled.
        
        Returns:
            True if debugging should be enabled (for smoke tests), False otherwise
        """
        import os
        # Enable debugging if:
        # 1. COIN_MAKER_DEBUG_MODE environment variable is set
        # 2. COIN_MAKER_SMOKE_TEST environment variable is set (for smoke tests)
        # 3. Debug mode is enabled in settings
        return (
            os.environ.get('COIN_MAKER_DEBUG_MODE', '').lower() in ('true', '1', 'yes') or
            os.environ.get('COIN_MAKER_SMOKE_TEST', '').lower() in ('true', '1', 'yes') or
            (self.settings and getattr(self.settings, 'debug', False))
        )
    
    def get_debug_port(self) -> Optional[int]:
        """Get the debugging port if available.
        
        Returns:
            Debug port number if debugging is enabled, None otherwise
        """
        if self._pywebview_wrapper and hasattr(self._pywebview_wrapper, 'get_debug_port'):
            return self._pywebview_wrapper.get_debug_port()
        return None

    def _run_backend_server(self) -> None:
        """Run the backend FastAPI server."""
        import uvicorn

        # Create FastAPI app
        app = self.create_fastapi_app()

        logger.info(f"Starting desktop backend server on {self.settings.host}:{self.settings.port}")
        logger.info("Desktop app ready - access at http://localhost:8000")

        # Run Uvicorn server with desktop-optimized settings
        uvicorn.run(
            app,
            host=self.settings.host,
            port=self.settings.port,
            log_level="info" if self.settings.debug else "warning",
            access_log=self.settings.debug
        )

    def get_fastapi_app(self):
        """Get the FastAPI application instance.

        Useful for testing or when the app needs to be used by external
        ASGI servers.
        """
        if not self._fastapi_app:
            self._fastapi_app = self.create_fastapi_app()
        return self._fastapi_app

    def open_browser(self) -> None:
        """Open the default browser to the application URL.

        Useful for desktop mode to automatically open the app.
        """
        import time
        import webbrowser

        url = f"http://{self.settings.host}:{self.settings.port}"

        # Give the server a moment to start
        time.sleep(1)

        logger.info(f"Opening browser to {url}")
        webbrowser.open(url)

    
    def _run_backend_server_thread(self) -> None:
        """Run the backend FastAPI server in a separate thread."""
        import uvicorn
        
        # Create FastAPI app
        app = self.create_fastapi_app()
        
        logger.info(f"Starting background FastAPI server on {self.settings.host}:{self.settings.port}")
        
        # Run Uvicorn server with desktop-optimized settings
        uvicorn.run(
            app,
            host=self.settings.host,
            port=self.settings.port,
            log_level="warning",  # Reduce noise in desktop mode
            access_log=False  # Disable access logs for cleaner output
        )

    def _run_fallback_window(self) -> None:
        """Run a fallback tkinter window when PyWebView fails to start."""
        logger.info("Starting fallback tkinter window...")
        
        try:
            import tkinter as tk
            from tkinter import ttk, messagebox
            import threading
            import webbrowser
            import signal
            import os
            
            logger.info("Tkinter imported successfully")
        except ImportError as e:
            logger.error(f"Failed to import tkinter: {e}")
            logger.error("Fallback to console mode")
            self._run_console_mode()
            return
        except Exception as e:
            logger.error(f"Error importing GUI libraries: {e}")
            logger.error("Fallback to console mode")  
            self._run_console_mode()
            return
        
        # Start FastAPI server in background thread
        fastapi_thread = threading.Thread(
            target=self._run_backend_server_thread, 
            daemon=True
        )
        fastapi_thread.start()
        
        # Give the server a moment to start
        import time
        time.sleep(2)
        
        # Create tkinter window
        root = tk.Tk()
        root.title("Coin Maker Desktop")
        root.geometry("500x300")
        root.resizable(True, True)
        
        # Center the window
        root.update_idletasks()
        x = (root.winfo_screenwidth() // 2) - (500 // 2)
        y = (root.winfo_screenheight() // 2) - (300 // 2)
        root.geometry(f"500x300+{x}+{y}")
        
        # Create main frame
        main_frame = ttk.Frame(root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        
        # Title
        title_label = ttk.Label(
            main_frame, 
            text="Coin Maker Desktop", 
            font=('Arial', 16, 'bold')
        )
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # Status for single-server mode
        app_url = f"http://localhost:{self._allocated_backend_port}"
        
        # Check if frontend is available in the build
        path_resolver = self.services.get_path_resolver() if self.services else None
        has_frontend = path_resolver and path_resolver.is_frontend_build_available()
        
        if has_frontend:
            status_text = (
                "The desktop application is running in fallback mode.\n"
                f"Application URL: {app_url}\n\n"
                "PyWebView failed to start. Click 'Open in Browser' to access the application."
            )
        else:
            status_text = (
                "The desktop application backend is running.\n"
                f"Backend URL: {app_url}\n"
                "Note: Frontend build is not available.\n\n"
                "You can access the API documentation at the URL above."
            )
        status_label = ttk.Label(main_frame, text=status_text, justify=tk.CENTER)
        status_label.grid(row=1, column=0, columnspan=2, pady=(0, 20))
        
        # Buttons frame
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.grid(row=2, column=0, columnspan=2, pady=(0, 20))
        
        def open_browser():
            """Open the application in the default browser."""
            # Single-server mode - always use the FastAPI server URL
            url = f"http://localhost:{self._allocated_backend_port}"
            try:
                webbrowser.open(url)
                logger.info(f"Opened browser to {url}")
            except Exception as e:
                logger.error(f"Failed to open browser: {e}")
                messagebox.showerror("Error", f"Failed to open browser:\n{e}")
        
        def show_logs():
            """Show application logs in a new window."""
            log_window = tk.Toplevel(root)
            log_window.title("Application Logs")
            log_window.geometry("600x400")
            
            # Create text widget with scrollbar
            text_frame = ttk.Frame(log_window)
            text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            log_text = tk.Text(text_frame, wrap=tk.WORD)
            scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=log_text.yview)
            log_text.configure(yscrollcommand=scrollbar.set)
            
            log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            # Add some sample log content
            log_content = (
                "Coin Maker Desktop Application Logs\n"
                "=" * 40 + "\n\n"
                f"Application started in fallback mode\n"
                f"Application URL: http://localhost:{self.settings.port}\n"
                f"Task queue: APScheduler\n"
                f"Debug mode: {self.settings.debug}\n"
                f"App data directory: {self.settings.app_data_dir}\n"
                "\nTo see full logs, check the console output."
            )
            log_text.insert(tk.END, log_content)
            log_text.config(state=tk.DISABLED)
        
        def on_closing():
            """Handle window closing - stop all processes."""
            logger.info("Shutting down application from fallback window...")
            
            # Try to shutdown gracefully
            try:
                # Send termination signal to current process group
                os.killpg(os.getpgid(os.getpid()), signal.SIGTERM)
            except Exception as e:
                logger.warning(f"Error during graceful shutdown: {e}")
            
            root.destroy()
            
            # Force exit if graceful shutdown fails
            import sys
            sys.exit(0)
        
        # Configure buttons
        open_btn = ttk.Button(buttons_frame, text="Open in Browser", command=open_browser)
        open_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        logs_btn = ttk.Button(buttons_frame, text="Show Logs", command=show_logs)
        logs_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        quit_btn = ttk.Button(buttons_frame, text="Quit", command=on_closing)
        quit_btn.pack(side=tk.LEFT)
        
        # Handle window close event
        root.protocol("WM_DELETE_WINDOW", on_closing)
        
        # Focus and show window
        root.focus_force()
        root.lift()
        
        logger.info("Fallback window created - application ready")
        
        # Start the tkinter main loop
        root.mainloop()

    def _run_console_mode(self) -> None:
        """Run in console mode when GUI is not available."""
        logger.info("Starting console mode (no GUI available)")
        
        app_url = f"http://localhost:{self._allocated_backend_port}"
        
        # Check if frontend is available
        path_resolver = self.services.get_path_resolver() if self.services else None
        has_frontend = path_resolver and path_resolver.is_frontend_build_available()
        
        print("\n" + "="*60)
        print("COIN MAKER DESKTOP - CONSOLE MODE")
        print("="*60)
        print(f"Application URL: {app_url}")
        print("="*60)
        
        if has_frontend:
            print("\nThe application is running in console mode.")
            print("Open the Application URL in your browser to use the application.")
        else:
            print("\nFrontend build is not available.")
            print("You can access the API documentation at the Application URL.")
        
        print("\nPress Ctrl+C to stop the application.")
        print("="*60)
        
        # Keep running until interrupted
        try:
            import time
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Console mode interrupted by user")
