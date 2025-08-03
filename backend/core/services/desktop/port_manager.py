"""
Port Management Service

Provides dynamic port allocation for desktop application to avoid conflicts
with other services running on the system.
"""

import logging
import socket
from typing import Optional

logger = logging.getLogger(__name__)


class PortManager:
    """Manages dynamic port allocation for desktop servers."""
    
    def __init__(self, preferred_backend_port: int = 8000, preferred_frontend_port: int = 5173):
        """Initialize port manager with preferred ports.
        
        Args:
            preferred_backend_port: Preferred port for FastAPI backend
            preferred_frontend_port: Preferred port for SvelteKit frontend
        """
        self.preferred_backend_port = preferred_backend_port
        self.preferred_frontend_port = preferred_frontend_port
        
    def is_port_available(self, port: int, host: str = "127.0.0.1") -> bool:
        """Check if a port is available for binding.
        
        Args:
            port: Port number to check
            host: Host to check (default: localhost)
            
        Returns:
            True if port is available, False otherwise
        """
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(1)
                result = sock.connect_ex((host, port))
                return result != 0  # 0 means connection successful (port in use)
        except Exception as e:
            logger.warning(f"Error checking port {port}: {e}")
            return False
    
    def find_available_port(self, preferred_port: int, port_range: range = range(8000, 9000)) -> Optional[int]:
        """Find an available port, starting with preferred port.
        
        Args:
            preferred_port: Try this port first
            port_range: Range of ports to search if preferred is unavailable
            
        Returns:
            Available port number, or None if none found
        """
        # Try preferred port first
        if self.is_port_available(preferred_port):
            logger.info(f"Using preferred port: {preferred_port}")
            return preferred_port
        
        logger.warning(f"Preferred port {preferred_port} is in use, searching for alternative...")
        
        # Search in the port range
        for port in port_range:
            if port == preferred_port:
                continue  # Already tried
            if self.is_port_available(port):
                logger.info(f"Found available port: {port}")
                return port
        
        logger.error(f"No available ports found in range {port_range}")
        return None
    
    def allocate_backend_port(self) -> Optional[int]:
        """Allocate a port for the FastAPI backend server.
        
        Returns:
            Available port number for backend, or None if none found
        """
        return self.find_available_port(
            self.preferred_backend_port, 
            range(8000, 8100)  # Backend ports: 8000-8099
        )
    
    def allocate_frontend_port(self) -> Optional[int]:
        """Allocate a port for the SvelteKit frontend server.
        
        Returns:
            Available port number for frontend, or None if none found
        """
        return self.find_available_port(
            self.preferred_frontend_port,
            range(5000, 5200)  # Frontend ports: 5000-5199
        )
    
    def allocate_ports(self) -> tuple[Optional[int], Optional[int]]:
        """Allocate both backend and frontend ports.
        
        Returns:
            Tuple of (backend_port, frontend_port), with None for any that failed
        """
        backend_port = self.allocate_backend_port()
        frontend_port = self.allocate_frontend_port()
        
        if backend_port and frontend_port:
            logger.info(f"Allocated ports - Backend: {backend_port}, Frontend: {frontend_port}")
        else:
            logger.error(f"Port allocation failed - Backend: {backend_port}, Frontend: {frontend_port}")
        
        return backend_port, frontend_port
    
    def get_random_port(self, min_port: int = 49152, max_port: int = 65535) -> Optional[int]:
        """Get a random available port from the ephemeral port range.
        
        Args:
            min_port: Minimum port number (default: 49152 - start of ephemeral range)
            max_port: Maximum port number (default: 65535 - end of port range)
            
        Returns:
            Random available port, or None if none found after 50 attempts
        """
        import random
        
        for _ in range(50):  # Try up to 50 random ports
            port = random.randint(min_port, max_port)
            if self.is_port_available(port):
                logger.info(f"Found random available port: {port}")
                return port
        
        logger.error("Could not find available random port after 50 attempts")
        return None


def test_port_manager():
    """Test the port manager functionality."""
    pm = PortManager()
    
    print("Testing port availability...")
    print(f"Port 8000 available: {pm.is_port_available(8000)}")
    print(f"Port 5173 available: {pm.is_port_available(5173)}")
    print(f"Port 99999 available: {pm.is_port_available(99999)}")  # Should be False (invalid)
    
    print("\nTesting port allocation...")
    backend_port, frontend_port = pm.allocate_ports()
    print(f"Allocated backend port: {backend_port}")
    print(f"Allocated frontend port: {frontend_port}")
    
    print("\nTesting random port...")
    random_port = pm.get_random_port()
    print(f"Random available port: {random_port}")


if __name__ == "__main__":
    test_port_manager()