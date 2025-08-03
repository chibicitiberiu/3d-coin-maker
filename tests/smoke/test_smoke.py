"""
Main smoke test module using pytest.
"""
import pytest
import os
from .test_runner import SmokeTestRunner
from .config_detector import ConfigDetector


class TestSmoke:
    """Pytest class for smoke tests."""
    
    def test_configurations_available(self):
        """Test that at least one configuration is available."""
        detector = ConfigDetector()
        configs = detector.get_available_configurations()
        assert len(configs) > 0, "No test configurations available"
    
    @pytest.mark.parametrize("config_name", [
        "Web APScheduler (Development)",
        "Web APScheduler (Production)",
        "Docker APScheduler (Development)",
        "Docker APScheduler (Production)",
    ])
    def test_specific_configuration(self, config_name, driver, test_image_path):
        """Test specific configuration if available."""
        detector = ConfigDetector()
        configs = detector.get_available_configurations()
        
        # Find the specific config
        config = None
        for c in configs:
            if c['name'] == config_name:
                config = c
                break
        
        if not config:
            pytest.skip(f"Configuration '{config_name}' not available")
        
        # Run the test
        runner = SmokeTestRunner()
        result = runner.run_single_test(config, driver, test_image_path)
        
        # Check results
        assert result['status'] != 'error', f"Test failed with error: {result.get('error')}"
        
        test_results = result['results']
        failed_steps = [step for step, passed in test_results.items() if not passed]
        
        assert len(failed_steps) == 0, f"Test steps failed: {failed_steps}"
    
    def test_all_available_configurations(self, driver, test_image_path):
        """Test all available configurations."""
        runner = SmokeTestRunner()
        results = runner.run_all_tests(driver, test_image_path)
        
        assert len(results) > 0, "No configurations were tested"
        
        # Check that at least one configuration passed completely
        passed_configs = []
        for result in results:
            if result['status'] == 'completed':
                test_results = result['results']
                if all(test_results.values()):
                    passed_configs.append(result['config']['name'])
        
        assert len(passed_configs) > 0, f"No configurations passed all tests. Results: {results}"


if __name__ == '__main__':
    # Direct execution for testing
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    
    # Simple test runner
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(options=options)
    
    try:
        test_image_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "assets",
            "test-coin-image.png"
        )
        
        runner = SmokeTestRunner()
        results = runner.run_all_tests(driver, test_image_path)
        runner.print_summary(results)
        
    finally:
        driver.quit()