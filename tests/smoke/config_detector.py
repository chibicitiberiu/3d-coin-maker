"""
Configuration detection for smoke tests.
Detects available test configurations on the current system.
"""
import os
import subprocess
import shutil
import socket
from typing import List, Dict, Any


class ConfigDetector:
    """Detects available configurations for smoke testing."""
    
    def __init__(self):
        self.project_root = self._find_project_root()
    
    def _find_project_root(self):
        """Find project root directory."""
        current = os.path.dirname(os.path.abspath(__file__))
        while current != '/':
            if os.path.exists(os.path.join(current, 'justfile')):
                return current
            current = os.path.dirname(current)
        return os.getcwd()
    
    def _command_exists(self, command):
        """Check if command exists in PATH."""
        return shutil.which(command) is not None
    
    def _port_is_free(self, port):
        """Check if port is free."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            return sock.connect_ex(('localhost', port)) != 0
    
    def _can_run_docker(self):
        """Check if Docker is available and working."""
        try:
            result = subprocess.run(
                ['docker', 'version'],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except:
            return False
    
    def _can_run_just(self):
        """Check if Just is available."""
        return self._command_exists('just')
    
    def _redis_available(self):
        """Check if Redis is available locally."""
        # Check if redis-server exists
        if not self._command_exists('redis-server'):
            return False
        
        # Try to connect to default Redis port
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(1)
                result = sock.connect_ex(('localhost', 6379))
                return result == 0
        except:
            return False
    
    def _flatpak_available(self):
        """Check if Flatpak is available."""
        return self._command_exists('flatpak')
    
    def _appimage_exists(self):
        """Check if AppImage exists."""
        # Look for AppImage in common locations
        possible_paths = [
            os.path.join(self.project_root, 'dist', 'coin-maker.AppImage'),
            os.path.join(self.project_root, 'build', 'coin-maker.AppImage'),
            os.path.join(self.project_root, 'coin-maker.AppImage'),
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        return None
    
    def _python_env_ready(self):
        """Check if Python environment is ready for web server."""
        try:
            # Check if we can import required modules
            import fastapi
            import uvicorn
            return True
        except ImportError:
            return False
    
    def _poetry_env_ready(self):
        """Check if Poetry environment is ready for desktop/web server."""
        try:
            # Check if Poetry is available and can run Python with required modules
            result = subprocess.run(
                ['poetry', 'run', 'python', '-c', 'import fastapi, uvicorn'],
                cwd=os.path.join(self.project_root, 'backend'),
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def detect_configurations(self) -> List[Dict[str, Any]]:
        """Detect all available test configurations."""
        configs = []
        
        # Web server configurations (direct Python)
        if self._python_env_ready():
            # APScheduler mode (always available if Python is ready)
            configs.append({
                'name': 'Web APScheduler (Development)',
                'type': 'web',
                'mode': 'apscheduler',
                'environment': 'development',
                'command': ['just', 'run-web-apscheduler-dev'] if self._can_run_just() else None,
                'ports': {'backend': 8000, 'frontend': 5173},
                'available': True
            })
            
            configs.append({
                'name': 'Web APScheduler (Production)',
                'type': 'web',
                'mode': 'apscheduler',
                'environment': 'production',
                'command': ['just', 'run-web-apscheduler-prod'] if self._can_run_just() else None,
                'ports': {'backend': 8001, 'frontend': 3001},
                'available': True
            })
            
            # Celery mode (only if Redis available)
            if self._redis_available():
                configs.append({
                    'name': 'Web Celery (Development)',
                    'type': 'web',
                    'mode': 'celery',
                    'environment': 'development',
                    'command': ['just', 'run-web-celery-dev'] if self._can_run_just() else None,
                    'ports': {'backend': 8002, 'frontend': 5174},
                    'available': True
                })
                
                configs.append({
                    'name': 'Web Celery (Production)',
                    'type': 'web',
                    'mode': 'celery',
                    'environment': 'production',
                    'command': ['just', 'run-web-celery-prod'] if self._can_run_just() else None,
                    'ports': {'backend': 8003, 'frontend': 3003},
                    'available': True
                })
        
        # Docker configurations
        if self._can_run_docker():
            # Docker APScheduler
            configs.append({
                'name': 'Docker APScheduler (Development)',
                'type': 'docker',
                'mode': 'apscheduler',
                'environment': 'development',
                'command': ['just', 'docker-dev', 'apscheduler'] if self._can_run_just() else None,
                'ports': {'backend': 8000, 'frontend': 5173},
                'available': True
            })
            
            configs.append({
                'name': 'Docker APScheduler (Production)',
                'type': 'docker',
                'mode': 'apscheduler',
                'environment': 'production',
                'command': ['just', 'docker-prod', 'apscheduler'] if self._can_run_just() else None,
                'ports': {'backend': 8000, 'frontend': 3000},
                'available': True
            })
            
            # Docker Celery
            configs.append({
                'name': 'Docker Celery (Development)',
                'type': 'docker',
                'mode': 'celery',
                'environment': 'development',
                'command': ['just', 'docker-dev', 'celery'] if self._can_run_just() else None,
                'ports': {'backend': 8000, 'frontend': 5173},
                'available': True
            })
            
            configs.append({
                'name': 'Docker Celery (Production)',
                'type': 'docker',
                'mode': 'celery',
                'environment': 'production',
                'command': ['just', 'docker-prod', 'celery'] if self._can_run_just() else None,
                'ports': {'backend': 8000, 'frontend': 3000},
                'available': True
            })
        
        # Desktop configurations
        if self._poetry_env_ready():
            configs.append({
                'name': 'Desktop Application',
                'type': 'desktop',
                'mode': 'desktop',
                'environment': 'development',
                'command': ['poetry', 'run', 'python', 'desktop_main.py'],
                'ports': {'backend': 8000, 'frontend': 5173},  # Fixed ports for desktop
                'available': True,
                'working_directory': os.path.join(self.project_root, 'backend')
            })
        
        # AppImage configuration
        appimage_path = self._appimage_exists()
        if appimage_path:
            configs.append({
                'name': 'AppImage',
                'type': 'appimage',
                'mode': 'appimage',
                'environment': 'production',
                'command': [appimage_path],
                'ports': {'backend': None, 'frontend': None},  # Dynamic ports
                'available': True,
                'appimage_path': appimage_path
            })
        
        # Flatpak configuration
        if self._flatpak_available():
            configs.append({
                'name': 'Flatpak',
                'type': 'flatpak',
                'mode': 'flatpak',
                'environment': 'production',
                'command': ['flatpak', 'run', 'io.github.coinmaker.CoinMaker'],
                'ports': {'backend': None, 'frontend': None},  # Dynamic ports
                'available': self._flatpak_installed()
            })
        
        return configs
    
    def _flatpak_installed(self):
        """Check if Flatpak package is installed."""
        try:
            result = subprocess.run(
                ['flatpak', 'list', '--app-id=io.github.coinmaker.CoinMaker'],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0 and 'io.github.coinmaker.CoinMaker' in result.stdout
        except:
            return False
    
    def get_available_configurations(self) -> List[Dict[str, Any]]:
        """Get only available configurations."""
        all_configs = self.detect_configurations()
        return [config for config in all_configs if config['available']]
    
    def print_configurations(self):
        """Print available configurations."""
        configs = self.get_available_configurations()
        
        print("Available Test Configurations:")
        print("=" * 50)
        
        if not configs:
            print("ERROR: No configurations available!")
            print("\nTo enable configurations:")
            if not self._python_env_ready():
                print("  - Install Python dependencies (poetry install)")
            if not self._can_run_docker():
                print("  - Install and start Docker")
            if not self._redis_available():
                print("  - Install and start Redis (for Celery tests)")
            if not self._can_run_just():
                print("  - Install Just command runner")
            return
        
        for i, config in enumerate(configs, 1):
            status = "AVAILABLE" if config['available'] else "UNAVAILABLE"
            print(f"{i:2d}. {status} {config['name']}")
            if config['command']:
                print(f"     Command: {' '.join(config['command'])}")
            if config['ports']['backend']:
                print(f"     Ports: Backend {config['ports']['backend']}, Frontend {config['ports']['frontend']}")
            print()
        
        print(f"Total: {len(configs)} available configurations")


if __name__ == '__main__':
    detector = ConfigDetector()
    detector.print_configurations()