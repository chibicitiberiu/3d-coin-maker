#!/usr/bin/env python3
"""
Quick smoke test runner - tests first available configuration.
"""
import os
import sys
from config_detector import ConfigDetector
from test_runner import SmokeTestRunner
from cli import create_driver

def main():
    # Get first available config
    detector = ConfigDetector()
    configs = detector.get_available_configurations()
    if not configs:
        print("ERROR: No configurations available")
        return 1

    config = configs[0]
    print(f"Testing: {config['name']}")

    # Create driver
    try:
        driver = create_driver("chrome", True)
    except Exception as e:
        print(f"ERROR: Failed to create driver: {e}")
        return 1

    try:
        # Get test image path
        test_image_path = os.path.join("..", "assets", "test-coin-image.png")
        
        # Run test
        runner = SmokeTestRunner()
        result = runner.run_single_test(config, driver, test_image_path)
        
        if result["status"] == "error":
            print(f"ERROR: {result['error']}")
            return 1
        
        test_results = result["results"]
        failed_steps = [step for step, passed in test_results.items() if not passed]
        
        if failed_steps:
            print(f"ERROR: Failed steps: {failed_steps}")
            return 1
        else:
            print("Quick test passed!")
            return 0

    finally:
        driver.quit()

if __name__ == "__main__":
    sys.exit(main())