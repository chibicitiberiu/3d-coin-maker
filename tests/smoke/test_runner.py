"""
Test runner for smoke tests.
Manages starting/stopping applications and running tests.
"""
import os
import time
import signal
import subprocess
import psutil
import requests
from typing import Dict, Any, Optional, List
from config_detector import ConfigDetector
from conftest import wait_for_url_ready, wait_for_health_check


class ApplicationManager:
    """Manages starting and stopping applications for testing."""
    
    def __init__(self):
        self.process = None
        self.docker_compose_files = []
        self.temp_files = []
    
    def _find_project_root(self):
        """Find project root directory."""
        current = os.path.dirname(os.path.abspath(__file__))
        while current != '/':
            if os.path.exists(os.path.join(current, 'justfile')):
                return current
            current = os.path.dirname(current)
        return os.getcwd()
    
    def start_application(self, config: Dict[str, Any]) -> Dict[str, str]:
        """Start application based on configuration."""
        if config['type'] == 'web':
            return self._start_web_server(config)
        elif config['type'] == 'docker':
            return self._start_docker(config)
        elif config['type'] == 'desktop':
            return self._start_desktop(config)
        elif config['type'] == 'appimage':
            return self._start_appimage(config)
        elif config['type'] == 'flatpak':
            return self._start_flatpak(config)
        else:
            raise ValueError(f"Unknown configuration type: {config['type']}")
    
    def _start_web_server(self, config: Dict[str, Any]) -> Dict[str, str]:
        """Start web server configuration."""
        backend_port = config['ports']['backend']
        frontend_port = config['ports']['frontend']
        
        # Create temporary script to start services
        script_content = f"""#!/bin/bash
set -e

# Start backend
echo "Starting backend on port {backend_port}..."
cd {os.getcwd()}

# Set environment
export ENVIRONMENT={config['environment']}
export BACKEND_PORT={backend_port}
export FRONTEND_PORT={frontend_port}

# Start based on mode
if [ "{config['mode']}" = "apscheduler" ]; then
    export USE_CELERY=false
    python -m uvicorn fastapi_main:app --host 0.0.0.0 --port {backend_port} &
    BACKEND_PID=$!
else
    export USE_CELERY=true
    # Start Redis if not running
    if ! pgrep redis-server > /dev/null; then
        redis-server --daemonize yes --port 6379
    fi
    
    # Start backend
    python -m uvicorn fastapi_main:app --host 0.0.0.0 --port {backend_port} &
    BACKEND_PID=$!
    
    # Start Celery worker
    celery -A workers.celery_app worker --loglevel=info --detach
    
    # Start Celery beat
    celery -A workers.celery_app beat --loglevel=info --detach
fi

# Wait for backend to be ready
echo "Waiting for backend to be ready..."
for i in {{1..30}}; do
    if curl -s http://localhost:{backend_port}/health/ > /dev/null; then
        echo "Backend ready!"
        break
    fi
    sleep 2
done

# Start frontend if development
if [ "{config['environment']}" = "development" ]; then
    cd frontend
    VITE_DEV_SERVER_PORT={frontend_port} pnpm run dev &
    FRONTEND_PID=$!
    cd ..
fi

# Keep running
wait
"""
        
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
            f.write(script_content)
            script_path = f.name
        
        os.chmod(script_path, 0o755)
        self.temp_files.append(script_path)
        
        # Start the script
        self.process = subprocess.Popen([script_path], cwd=os.getcwd())
        
        # Wait for services to be ready
        backend_url = f"http://localhost:{backend_port}"
        health_url = f"{backend_url}/health/"
        
        if config['environment'] == 'development':
            frontend_url = f"http://localhost:{frontend_port}"
        else:
            frontend_url = backend_url  # Production serves frontend from backend
        
        # Wait for backend
        if not wait_for_health_check(health_url, timeout=60):
            raise RuntimeError(f"Backend failed to start on {backend_url}")
        
        # Wait for frontend if development
        if config['environment'] == 'development':
            if not wait_for_url_ready(frontend_url, timeout=60):
                raise RuntimeError(f"Frontend failed to start on {frontend_url}")
        
        return {
            'frontend_url': frontend_url,
            'backend_url': backend_url,
            'health_url': health_url
        }
    
    def _start_docker(self, config: Dict[str, Any]) -> Dict[str, str]:
        """Start Docker configuration."""
        # Find project root directory
        project_root = self._find_project_root()
        
        # Prepare docker compose command
        if config['environment'] == 'production':
            compose_files = ['-f', 'docker-compose.yml', '-f', 'docker-compose.prod.yml']
        else:
            compose_files = ['-f', 'docker-compose.yml', '-f', 'docker-compose.override.yml']  # Base file + dev override
        
        if config['mode'] == 'apscheduler':
            compose_files.extend(['-f', 'docker-compose.apscheduler.yml'])
        elif config['mode'] == 'celery':
            compose_files.extend(['--profile', 'celery'])
        
        # Set environment
        env = os.environ.copy()
        env['ENVIRONMENT'] = config['environment']
        
        # Start containers from project root
        cmd = ['docker', 'compose'] + compose_files + ['up', '-d', '--build']
        self.process = subprocess.Popen(cmd, env=env, cwd=project_root)
        self.process.wait()  # Wait for docker compose to finish starting
        
        # Determine URLs
        backend_port = config['ports']['backend']
        frontend_port = config['ports']['frontend']
        
        backend_url = f"http://localhost:{backend_port}"
        health_url = f"{backend_url}/health/"
        
        if config['environment'] == 'development':
            frontend_url = f"http://localhost:{frontend_port}"
        else:
            frontend_url = f"http://localhost:{frontend_port}"
        
        # Wait for services
        if not wait_for_health_check(health_url, timeout=120):
            raise RuntimeError(f"Docker backend failed to start on {backend_url}")
        
        if not wait_for_url_ready(frontend_url, timeout=60):
            raise RuntimeError(f"Docker frontend failed to start on {frontend_url}")
        
        return {
            'frontend_url': frontend_url,
            'backend_url': backend_url,
            'health_url': health_url
        }
    
    def _start_desktop(self, config: Dict[str, Any]) -> Dict[str, str]:
        """Start desktop application."""
        # Desktop app needs special handling as it creates its own server
        cmd = config['command']
        if not cmd:
            raise RuntimeError("No command available for desktop application")
        
        self.process = subprocess.Popen(cmd)
        
        # Desktop app typically uses dynamic ports, so we need to detect them
        # For now, assume standard ports and wait
        time.sleep(5)  # Give desktop app time to start
        
        # Try common ports for desktop app
        for port in [8000, 8001, 8002]:
            health_url = f"http://localhost:{port}/health/"
            if wait_for_health_check(health_url, timeout=5):
                backend_url = f"http://localhost:{port}"
                frontend_url = backend_url  # Desktop serves frontend from same port
                return {
                    'frontend_url': frontend_url,
                    'backend_url': backend_url,
                    'health_url': health_url
                }
        
        raise RuntimeError("Desktop application failed to start or port not detected")
    
    def _start_appimage(self, config: Dict[str, Any]) -> Dict[str, str]:
        """Start AppImage."""
        appimage_path = config['appimage_path']
        self.process = subprocess.Popen([appimage_path])
        
        # Similar to desktop, detect port
        time.sleep(5)
        
        for port in [8000, 8001, 8002]:
            health_url = f"http://localhost:{port}/health/"
            if wait_for_health_check(health_url, timeout=5):
                backend_url = f"http://localhost:{port}"
                frontend_url = backend_url
                return {
                    'frontend_url': frontend_url,
                    'backend_url': backend_url,
                    'health_url': health_url
                }
        
        raise RuntimeError("AppImage failed to start or port not detected")
    
    def _start_flatpak(self, config: Dict[str, Any]) -> Dict[str, str]:
        """Start Flatpak application."""
        cmd = config['command']
        self.process = subprocess.Popen(cmd)
        
        # Similar to desktop, detect port
        time.sleep(5)
        
        for port in [8000, 8001, 8002]:
            health_url = f"http://localhost:{port}/health/"
            if wait_for_health_check(health_url, timeout=5):
                backend_url = f"http://localhost:{port}"
                frontend_url = backend_url
                return {
                    'frontend_url': frontend_url,
                    'backend_url': backend_url,
                    'health_url': health_url
                }
        
        raise RuntimeError("Flatpak application failed to start or port not detected")
    
    def stop_application(self, config: Dict[str, Any]):
        """Stop application."""
        try:
            if config['type'] == 'docker':
                # Stop docker containers from project root
                project_root = self._find_project_root()
                
                if config['environment'] == 'production':
                    compose_files = ['-f', 'docker-compose.yml', '-f', 'docker-compose.prod.yml']
                else:
                    compose_files = ['-f', 'docker-compose.yml', '-f', 'docker-compose.override.yml']
                
                if config['mode'] == 'apscheduler':
                    compose_files.extend(['-f', 'docker-compose.apscheduler.yml'])
                elif config['mode'] == 'celery':
                    compose_files.extend(['--profile', 'celery'])
                
                cmd = ['docker', 'compose'] + compose_files + ['down']
                subprocess.run(cmd, timeout=30, cwd=project_root)
            
            elif self.process:
                # Stop process tree
                try:
                    parent = psutil.Process(self.process.pid)
                    children = parent.children(recursive=True)
                    for child in children:
                        child.terminate()
                    parent.terminate()
                    
                    # Wait for processes to terminate
                    gone, still_alive = psutil.wait_procs(children + [parent], timeout=10)
                    for p in still_alive:
                        p.kill()
                        
                except psutil.NoSuchProcess:
                    pass
        
        except Exception as e:
            print(f"WARNING: Error stopping application: {e}")
        
        finally:
            # Clean up temp files
            for temp_file in self.temp_files:
                try:
                    os.unlink(temp_file)
                except:
                    pass
            self.temp_files = []


class SmokeTestRunner:
    """Main test runner that coordinates everything."""
    
    def __init__(self):
        self.detector = ConfigDetector()
        self.app_manager = ApplicationManager()
    
    def run_single_test(self, config: Dict[str, Any], driver, test_image_path: str) -> Dict[str, Any]:
        """Run smoke test for a single configuration."""
        from base_test import BaseSmokeTest
        
        print(f"\nTesting: {config['name']}")
        print("=" * 60)
        
        try:
            # Start application
            print("Starting application...")
            urls = self.app_manager.start_application(config)
            
            # Run test
            test = BaseSmokeTest(driver)
            results = test.run_full_test(
                urls['frontend_url'],
                urls['health_url'],
                test_image_path
            )
            
            return {
                'config': config,
                'results': results,
                'status': 'completed',
                'urls': urls
            }
            
        except Exception as e:
            print(f"ERROR: Failed to test {config['name']}: {e}")
            return {
                'config': config,
                'results': {},
                'status': 'error',
                'error': str(e)
            }
        
        finally:
            # Always try to stop application
            print("Stopping application...")
            try:
                self.app_manager.stop_application(config)
                time.sleep(2)  # Give time for cleanup
            except Exception as e:
                print(f"WARNING: Error during cleanup: {e}")
    
    def run_all_tests(self, driver, test_image_path: str, config_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """Run smoke tests for all available configurations."""
        configs = self.detector.get_available_configurations()
        
        if config_filter:
            configs = [c for c in configs if config_filter.lower() in c['name'].lower()]
        
        if not configs:
            print("ERROR: No configurations available for testing!")
            return []
        
        print(f"Running smoke tests for {len(configs)} configurations...")
        
        results = []
        for i, config in enumerate(configs, 1):
            print(f"\n[{i}/{len(configs)}] ", end="")
            result = self.run_single_test(config, driver, test_image_path)
            results.append(result)
            
            # Brief pause between tests
            if i < len(configs):
                time.sleep(5)
        
        return results
    
    def print_summary(self, results: List[Dict[str, Any]]):
        """Print test summary."""
        print("\n" + "=" * 80)
        print("SMOKE TEST SUMMARY")
        print("=" * 80)
        
        total_tests = len(results)
        passed_tests = 0
        failed_tests = 0
        error_tests = 0
        
        for result in results:
            config = result['config']
            status = result['status']
            
            if status == 'error':
                print(f"ERROR: {config['name']}: ERROR - {result.get('error', 'Unknown error')}")
                error_tests += 1
            else:
                test_results = result['results']
                all_passed = all(test_results.values()) if test_results else False
                
                if all_passed:
                    print(f"PASSED: {config['name']}")
                    passed_tests += 1
                else:
                    failed_steps = [step for step, passed in test_results.items() if not passed]
                    print(f"FAILED: {config['name']} - {', '.join(failed_steps)}")
                    failed_tests += 1
        
        print(f"\nResults: {passed_tests} passed, {failed_tests} failed, {error_tests} errors out of {total_tests} total")
        
        if passed_tests == total_tests:
            print("All tests passed!")
            return True
        else:
            print("Some tests failed!")
            return False