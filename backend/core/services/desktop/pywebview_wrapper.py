"""
PyWebView Wrapper Service

Provides pywebview integration for desktop application.
Handles window creation, native dialogs, and JavaScript bridge functionality.
"""

import logging
import threading
import time
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class PyWebViewWrapper:
    """Manages pywebview window and native integration for desktop application."""
    
    def __init__(self, frontend_url: str, backend_port: int):
        """Initialize pywebview wrapper.
        
        Args:
            frontend_url: URL of the SvelteKit frontend server
            backend_port: Port of the FastAPI backend server
        """
        self.frontend_url = frontend_url
        self.backend_port = backend_port
        self.window = None
        self.is_running = False
        
    def start(self) -> bool:
        """Start the pywebview window.
        
        Returns:
            True if started successfully, False otherwise
        """
        try:
            import webview
            logger.info(f"Starting pywebview window with URL: {self.frontend_url}")
            
            # Create the window with GPU-friendly settings
            self.window = webview.create_window(
                title="Coin Maker",
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
            
            # Start webview with Qt GUI backend for better GPU support
            webview.start(
                debug=False,  # Set to True for debugging webview issues
                gui='qt',     # Force Qt backend for better GPU support
                private_mode=False  # Allow cookies/storage and GPU access
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
        
    def open_file_dialog(self) -> Optional[str]:
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
    
    def save_file_dialog(self, default_filename: str = "coin.stl") -> Optional[str]:
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
    
    def show_folder_dialog(self, title: str = "Select Folder") -> Optional[str]:
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
    
    def get_desktop_info(self) -> Dict[str, Any]:
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