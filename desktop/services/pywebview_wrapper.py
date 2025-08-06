"""
PyWebView Wrapper Service

Provides pywebview integration for desktop application.
Handles window creation, native dialogs, and JavaScript bridge functionality.
"""

import logging
import os
import shutil
import subprocess
from typing import Any

import webview

logger = logging.getLogger(__name__)


class PyWebViewWrapper:
    """Manages pywebview window and native integration for desktop application."""

    def __init__(self, frontend_url: str, backend_port: int, enable_debugging: bool = False, debug_port: int = 9222):
        """Initialize pywebview wrapper.

        Args:
            frontend_url: URL of the SvelteKit frontend server
            backend_port: Port of the FastAPI backend server
            enable_debugging: Enable remote debugging for Selenium (QtWebEngine only)
            debug_port: Port for remote debugging (default: 9222)
        """
        self.frontend_url = frontend_url
        self.backend_port = backend_port
        self.enable_debugging = enable_debugging
        self.debug_port = debug_port
        self.window = None
        self.is_running = False

    def start(self) -> bool:
        """Start the pywebview window.

        Returns:
            True if started successfully, False otherwise
        """
        try:
            logger.info(f"Starting pywebview window with URL: {self.frontend_url}")

            # Verify the frontend URL is accessible before starting PyWebView
            try:
                import requests
                response = requests.get(self.frontend_url, timeout=5)
                if response.status_code != 200:
                    logger.error(f"Frontend URL not accessible: {self.frontend_url} (status: {response.status_code})")
                    return False
                logger.info(f"Verified frontend URL is accessible: {self.frontend_url}")
            except Exception as e:
                logger.error(f"Cannot access frontend URL {self.frontend_url}: {e}")
                return False

            # Configure QtWebEngine with intelligent graphics handling
            self._configure_qtwebengine_graphics()

            # Create the window with GPU-friendly settings
            self.window = webview.create_window(
                title="Coin Maker" + (" [Debug Mode]" if self.enable_debugging else ""),
                url=self.frontend_url,
                width=1400,
                height=900,
                min_size=(800, 600),
                resizable=True,
                js_api=self._create_js_api(),
                shadow=True,  # Enable window effects
                on_top=False,
                text_select=True  # Allow text selection for better interaction
            )


            # Log initial window creation details
            logger.info("Created PyWebView window:")
            logger.info(f"  Title: {self.window.title}")
            logger.info(f"  Initial URL: {self.frontend_url}")
            logger.info(f"  Debug mode: {self.enable_debugging}")
            logger.info("  Window size: 1400x900")

            # Start webview with Qt GUI backend for better GPU support
            # Use a function to handle post-load actions
            def on_webview_ready():
                """Called after webview window is ready."""
                try:
                    logger.info("PyWebView window is ready")
                    current_url = self.window.get_current_url()
                    logger.info(f"Current URL after ready: {current_url}")

                    # Inject JavaScript to monitor for navigation attempts and errors
                    monitor_js = """
                    (function() {
                        console.log('PyWebView monitoring script loaded');

                        // Monitor fetch requests
                        const originalFetch = window.fetch;
                        window.fetch = function(...args) {
                            console.log('FETCH REQUEST:', args[0]);
                            return originalFetch.apply(this, args).catch(err => {
                                console.error('FETCH ERROR:', args[0], err);
                                throw err;
                            });
                        };

                        // Monitor XMLHttpRequest
                        const originalXHR = window.XMLHttpRequest;
                        window.XMLHttpRequest = function() {
                            const xhr = new originalXHR();
                            const originalOpen = xhr.open;
                            xhr.open = function(method, url) {
                                console.log('XHR REQUEST:', method, url);
                                return originalOpen.apply(this, arguments);
                            };
                            xhr.addEventListener('error', function() {
                                console.error('XHR ERROR:', xhr.status, xhr.responseURL);
                            });
                            return xhr;
                        };

                        // Monitor window.open attempts
                        const originalWindowOpen = window.open;
                        window.open = function(url, name, features) {
                            console.warn('WINDOW.OPEN BLOCKED:', url, name, features);
                            return null; // Block popup windows
                        };

                        // Monitor for navigation attempts
                        window.addEventListener('beforeunload', function(e) {
                            console.log('BEFORE UNLOAD - Navigation attempt detected');
                        });

                        console.log('PyWebView monitoring setup complete');
                    })();
                    """

                    # Execute the monitoring script after a short delay
                    import threading
                    import time
                    def delayed_inject():
                        time.sleep(2)  # Wait for page to fully load
                        try:
                            self.window.evaluate_js(monitor_js)
                            logger.info("Injected navigation monitoring script")
                        except Exception as e:
                            logger.warning(f"Could not inject monitoring script: {e}")

                    monitoring_thread = threading.Thread(target=delayed_inject, daemon=True)
                    monitoring_thread.start()

                except Exception as e:
                    logger.warning(f"Error in webview ready handler: {e}")

            webview.start(
                debug=False,  # Always disable PyWebView's built-in web inspector to prevent popup
                gui='qt',     # Force Qt backend for better GPU support
                private_mode=False,  # Allow cookies/storage and GPU access
                func=on_webview_ready  # Function to call when ready
            )

            self.is_running = True
            logger.info("PyWebView window started successfully")
            return True

        except ImportError as e:
            logger.error(f"Failed to import webview: {e}")
            logger.info("Try installing GUI dependencies: poetry install")
            return False
        except Exception as e:
            # Check for common GUI library issues
            error_msg = str(e)
            if "QT cannot be loaded" in error_msg or "GTK cannot be loaded" in error_msg:
                logger.error("PyWebView GUI libraries not available")
                logger.info("On Linux: Install via 'sudo apt install python3-pyqt6' or 'poetry install' to get PyQt6")
                logger.info("On macOS: GUI libraries should be available by default")
                logger.info("On Windows: GUI libraries should be available by default")
            else:
                logger.error(f"Failed to start pywebview window: {e}")
            return False

    def _create_js_api(self) -> 'JSApi':
        """Create JavaScript API object for pywebview.

        Returns:
            JSApi instance with exposed methods
        """
        return JSApi(self.backend_port)

    def _configure_qtwebengine_graphics(self) -> None:
        """Configure QtWebEngine with intelligent graphics fallback strategy."""
        import os

        # Base flags for all configurations
        base_flags = [
            '--no-first-run',
            '--disable-extensions',
            '--disable-default-apps',
            '--disable-popup-blocking',
            '--disable-background-timer-throttling',
            '--disable-renderer-backgrounding',
            '--disable-backgrounding-occluded-windows'
        ]

        # Add remote debugging if enabled
        if self.enable_debugging:
            logger.info(f"Enabling QtWebEngine remote debugging on port {self.debug_port}")
            os.environ['QTWEBENGINE_REMOTE_DEBUGGING'] = str(self.debug_port)
            base_flags.extend([
                f'--remote-debugging-port={self.debug_port}',
                '--block-new-web-contents'
            ])

        # Try progressive fallback for graphics configuration
        self._configure_progressive_graphics(base_flags)

    def _configure_progressive_graphics(self, base_flags: list[str]) -> None:
        """Configure graphics with progressive fallback strategy."""
        import os

        # Strategy 1: Try intelligent hardware detection first
        hw_accel_flags = self._detect_hardware_acceleration()

        # Strategy 2: If no clear GPU detected, try universal compatibility mode
        if self._should_use_compatibility_mode():
            logger.info("Using universal compatibility mode for maximum WebGL support")
            hw_accel_flags = self._get_compatibility_mode_flags()

        # Combine and set flags
        all_flags = base_flags + hw_accel_flags
        chromium_flags = ' '.join(all_flags)

        logger.info(f"QtWebEngine configuration: {chromium_flags}")
        os.environ['QTWEBENGINE_CHROMIUM_FLAGS'] = chromium_flags

        # Also set additional environment variables for better WebGL support
        self._set_webgl_environment_variables()

    def _should_use_compatibility_mode(self) -> bool:
        """Determine if we should use universal compatibility mode."""
        import os

        # Use compatibility mode if:
        # 1. No clear GPU information available
        # 2. Running in development/debug mode (prioritize functionality over performance)
        # 3. Previous WebGL failures detected (could implement persistence later)

        gpu_info = self._get_gpu_info()
        is_dev_mode = self.enable_debugging or os.environ.get('COIN_MAKER_DEV_MODE')

        return not gpu_info.strip() or is_dev_mode

    def _get_compatibility_mode_flags(self) -> list[str]:
        """Flags for maximum WebGL compatibility across systems."""
        return [
            '--enable-gpu-rasterization',
            '--enable-webgl',
            '--enable-webgl2',  # Try WebGL2 but with fallbacks
            '--enable-accelerated-2d-canvas',
            '--disable-gpu-compositing',  # Disable for stability
            '--use-gl=angle',  # Use ANGLE for better compatibility
            '--use-angle=gl',  # Force ANGLE to use OpenGL
            '--ignore-gpu-blacklist',
            '--disable-gpu-sandbox',
            '--enable-webgl-draft-extensions',
            '--enable-webgl-image-chromium',
            '--max-gles-version=3.0'  # Limit to GLES 3.0 for compatibility
        ]

    def _set_webgl_environment_variables(self) -> None:
        """Set additional environment variables for WebGL support."""
        import os

        # Mesa/OpenGL settings for better software rendering
        os.environ['MESA_GL_VERSION_OVERRIDE'] = '3.3'
        os.environ['MESA_GLSL_VERSION_OVERRIDE'] = '330'

        # Qt WebEngine specific settings
        os.environ['QT_OPENGL'] = 'software'  # Force software OpenGL if needed
        os.environ['QTWEBENGINE_CHROMIUM_FLAGS'] = os.environ.get('QTWEBENGINE_CHROMIUM_FLAGS', '')

    def _detect_hardware_acceleration(self) -> list[str]:
        """Detect and configure the best graphics acceleration strategy.

        Returns:
            List of Chromium flags for graphics configuration
        """
        import os

        logger.info("Detecting graphics acceleration capabilities...")

        # Check if we're in a headless environment (common in containers/CI)
        if os.environ.get('DISPLAY') is None and os.environ.get('WAYLAND_DISPLAY') is None:
            logger.info("No display detected - using software rendering")
            return self._get_software_rendering_flags()

        # Check for GPU info
        gpu_info = self._get_gpu_info()

        # Check if running in a container or virtualized environment
        if self._is_virtualized():
            logger.info("Virtualized environment detected - using software rendering with WebGL fallback")
            return self._get_virtualized_flags()

        # Check for dedicated GPU vs integrated/software
        if self._has_dedicated_gpu(gpu_info):
            logger.info("Dedicated GPU detected - enabling full hardware acceleration")
            return self._get_hardware_acceleration_flags()

        elif self._has_integrated_gpu(gpu_info):
            logger.info("Integrated GPU detected - using hybrid acceleration")
            return self._get_hybrid_acceleration_flags()

        else:
            logger.info("No GPU acceleration available - using software rendering")
            return self._get_software_rendering_flags()

    def _get_gpu_info(self) -> str:
        """Get GPU information from the system."""
        try:
            # Try multiple methods to get GPU info
            methods = [
                ['lspci', '-nn'],
                ['glxinfo', '-B'],
                ['nvidia-smi', '--query-gpu=name', '--format=csv,noheader']
            ]

            for method in methods:
                try:
                    if shutil.which(method[0]):
                        result = subprocess.run(method, capture_output=True, text=True, timeout=5)
                        if result.returncode == 0 and result.stdout.strip():
                            return result.stdout.strip()
                except Exception:
                    continue

        except Exception as e:
            logger.debug(f"Could not get GPU info: {e}")

        return ""

    def _is_virtualized(self) -> bool:
        """Check if running in a virtualized environment."""
        try:
            # Check for common virtualization indicators
            virt_files = ['/sys/class/dmi/id/product_name', '/sys/class/dmi/id/sys_vendor']

            for virt_file in virt_files:
                try:
                    if os.path.exists(virt_file):
                        with open(virt_file) as f:
                            content = f.read().lower()
                            if any(vm in content for vm in ['vmware', 'virtualbox', 'qemu', 'kvm', 'xen', 'docker']):
                                return True
                except Exception:
                    continue

            # Check environment variables
            if any(var in os.environ for var in ['DOCKER_CONTAINER', 'container']):
                return True

        except Exception as e:
            logger.debug(f"Could not detect virtualization: {e}")

        return False

    def _has_dedicated_gpu(self, gpu_info: str) -> bool:
        """Check if system has a dedicated GPU."""
        gpu_lower = gpu_info.lower()
        dedicated_indicators = ['nvidia', 'geforce', 'quadro', 'tesla', 'amd', 'radeon', 'rx ', 'intel arc']
        return any(indicator in gpu_lower for indicator in dedicated_indicators)

    def _has_integrated_gpu(self, gpu_info: str) -> bool:
        """Check if system has integrated GPU."""
        gpu_lower = gpu_info.lower()
        integrated_indicators = ['intel', 'integrated', 'uhd', 'iris']
        return any(indicator in gpu_lower for indicator in integrated_indicators)

    def _get_hardware_acceleration_flags(self) -> list[str]:
        """Flags for full hardware acceleration."""
        return [
            '--enable-gpu',
            '--enable-webgl',
            '--enable-webgl2',
            '--enable-accelerated-2d-canvas',
            '--enable-gpu-compositing'
        ]

    def _get_hybrid_acceleration_flags(self) -> list[str]:
        """Flags for integrated GPU with conservative settings."""
        return [
            '--enable-gpu',
            '--enable-webgl',
            '--disable-webgl2',  # WebGL2 can be problematic on integrated GPUs
            '--enable-accelerated-2d-canvas',
            '--disable-gpu-compositing'  # Conservative for stability
        ]

    def _get_virtualized_flags(self) -> list[str]:
        """Flags for virtualized environments with software fallback."""
        return [
            '--disable-gpu',
            '--enable-webgl',  # Try WebGL with software rendering
            '--disable-webgl2',
            '--disable-accelerated-2d-canvas',
            '--disable-gpu-compositing',
            '--use-gl=swiftshader',  # Use SwiftShader for WebGL
            '--ignore-gpu-blacklist'
        ]

    def _get_software_rendering_flags(self) -> list[str]:
        """Flags for software rendering with WebGL fallback."""
        return [
            '--disable-gpu',
            '--enable-webgl',  # Allow WebGL with software rendering
            '--disable-webgl2',  # Disable WebGL2 to prevent errors
            '--disable-accelerated-2d-canvas',
            '--disable-gpu-compositing',
            '--use-gl=swiftshader',  # Use SwiftShader for WebGL
            '--ignore-gpu-blacklist',
            '--disable-gpu-sandbox'
        ]

    def get_debug_port(self) -> int | None:
        """Get the remote debugging port if enabled.

        Returns:
            Debug port number if debugging is enabled, None otherwise
        """
        return self.debug_port if self.enable_debugging else None

    def stop(self) -> None:
        """Stop the pywebview window."""
        try:
            if self.window:
                import webview
                webview.destroy_window(self.window)
                self.is_running = False
                logger.info("PyWebView window stopped")
        except Exception as e:
            logger.error(f"Error stopping pywebview window: {e}")


class JSApi:
    """JavaScript API exposed to the frontend via pywebview."""

    def __init__(self, backend_port: int):
        """Initialize JavaScript API.

        Args:
            backend_port: Port of the FastAPI backend server
        """
        self.backend_port = backend_port

    def open_file_dialog(self) -> str | None:
        """Open native file dialog for image selection.

        Returns:
            File path if selected, None if cancelled
        """
        try:
            import webview

            result = webview.windows[0].create_file_dialog(
                webview.OPEN_DIALOG,
                allow_multiple=False,
                file_types=(
                    'Image Files (*.png;*.jpg;*.jpeg;*.gif;*.bmp;*.tiff;*.webp)',
                    'PNG Files (*.png)',
                    'JPEG Files (*.jpg;*.jpeg)',
                    'All Files (*.*)'
                )
            )

            if result and len(result) > 0:
                file_path = result[0]
                logger.info(f"File selected: {file_path}")
                return file_path
            else:
                logger.info("File selection cancelled")
                return None

        except Exception as e:
            logger.error(f"Error opening file dialog: {e}")
            return None

    def save_file_dialog(self, default_filename: str = "coin.stl") -> str | None:
        """Open native save dialog for STL export.

        Args:
            default_filename: Default name for the file

        Returns:
            File path if selected, None if cancelled
        """
        try:
            import webview

            result = webview.windows[0].create_file_dialog(
                webview.SAVE_DIALOG,
                save_filename=default_filename,
                file_types=('STL Files (*.stl)', 'All Files (*.*)')
            )

            if result and len(result) > 0:
                file_path = result[0]
                logger.info(f"Save location selected: {file_path}")
                return file_path
            else:
                logger.info("Save dialog cancelled")
                return None

        except Exception as e:
            logger.error(f"Error opening save dialog: {e}")
            return None

    def show_folder_dialog(self, title: str = "Select Folder") -> str | None:
        """Open native folder selection dialog.

        Args:
            title: Dialog title

        Returns:
            Folder path if selected, None if cancelled
        """
        try:
            import webview

            result = webview.windows[0].create_file_dialog(
                webview.FOLDER_DIALOG
            )

            if result and len(result) > 0:
                folder_path = result[0]
                logger.info(f"Folder selected: {folder_path}")
                return folder_path
            else:
                logger.info("Folder selection cancelled")
                return None

        except Exception as e:
            logger.error(f"Error opening folder dialog: {e}")
            return None

    def get_desktop_info(self) -> dict[str, Any]:
        """Get desktop application information.

        Returns:
            Dictionary with desktop app info
        """
        return {
            "is_desktop": True,
            "platform": "desktop",
            "has_native_dialogs": True,
            "version": "1.0.0",
            "webview_engine": "pywebview",
            "backend_url": f"http://127.0.0.1:{self.backend_port}"
        }

    def show_info_dialog(self, title: str, message: str) -> None:
        """Show native info dialog.

        Args:
            title: Dialog title
            message: Dialog message
        """
        try:
            import webview
            webview.windows[0].show_info_dialog(title, message)
        except Exception as e:
            logger.error(f"Error showing info dialog: {e}")

    def show_error_dialog(self, title: str, message: str) -> None:
        """Show native error dialog.

        Args:
            title: Dialog title
            message: Error message
        """
        try:
            import webview
            webview.windows[0].show_error_dialog(title, message)
        except Exception as e:
            logger.error(f"Error showing error dialog: {e}")


def test_pywebview_wrapper():
    """Test the pywebview wrapper functionality."""
    wrapper = PyWebViewWrapper("http://127.0.0.1:5000", 8000)

    print("Testing pywebview wrapper...")
    print(f"Frontend URL: {wrapper.frontend_url}")
    print(f"Backend port: {wrapper.backend_port}")

    # This would start the actual window - only for testing
    # wrapper.start()


if __name__ == "__main__":
    test_pywebview_wrapper()
