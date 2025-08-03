#!/usr/bin/env python3
"""
Command line interface for smoke tests.
"""
import argparse
import sys
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions

from config_detector import ConfigDetector
from test_runner import SmokeTestRunner


def create_driver(browser_type="chrome", headless=False):
    """Create WebDriver instance."""
    # Find project root and WebDriver directory
    project_root = find_project_root()
    webdriver_dir = os.path.join(project_root, "build", "test-drivers")
    
    if browser_type.lower() == "firefox":
        options = FirefoxOptions()
        if headless:
            options.add_argument("--headless")
        options.add_argument("--width=1920")
        options.add_argument("--height=1080")
        
        try:
            # Try to use local GeckoDriver first
            geckodriver_path = os.path.join(webdriver_dir, "geckodriver")
            if os.path.exists(geckodriver_path):
                from selenium.webdriver.firefox.service import Service
                service = Service(geckodriver_path)
                return webdriver.Firefox(service=service, options=options)
            else:
                return webdriver.Firefox(options=options)
        except Exception as e:
            print(f"WARNING: Firefox not available ({e}), falling back to Chrome")
            return create_chrome_driver(headless, webdriver_dir)
    else:
        return create_chrome_driver(headless, webdriver_dir)


def create_chrome_driver(headless, webdriver_dir=None):
    """Create Chrome WebDriver."""
    options = ChromeOptions()
    if headless:
        options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-web-security")
    options.add_argument("--allow-running-insecure-content")
    
    # Try to use local ChromeDriver first
    if webdriver_dir:
        chromedriver_path = os.path.join(webdriver_dir, "chromedriver")
        if os.path.exists(chromedriver_path):
            from selenium.webdriver.chrome.service import Service
            service = Service(chromedriver_path)
            return webdriver.Chrome(service=service, options=options)
    
    return webdriver.Chrome(options=options)


def find_project_root():
    """Find project root directory."""
    current = os.path.dirname(os.path.abspath(__file__))
    while current != '/':
        if os.path.exists(os.path.join(current, 'justfile')):
            return current
        current = os.path.dirname(current)
    return os.getcwd()


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Coin Maker Smoke Tests")
    parser.add_argument(
        "--list", 
        action="store_true",
        help="List available configurations"
    )
    parser.add_argument(
        "--config",
        type=str,
        help="Run specific configuration (partial name match)"
    )
    parser.add_argument(
        "--browser",
        choices=["chrome", "firefox"],
        default="chrome",
        help="Browser to use"
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run browser in headless mode (hidden)"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=30,
        help="Timeout for operations in seconds"
    )
    parser.add_argument(
        "--image",
        type=str,
        help="Path to test image (default: built-in test image)"
    )
    
    args = parser.parse_args()
    
    # Find test image
    if args.image:
        test_image_path = args.image
    else:
        test_image_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "assets",
            "test-coin-image.png"
        )
    
    if not os.path.exists(test_image_path):
        print(f"ERROR: Test image not found: {test_image_path}")
        return 1
    
    detector = ConfigDetector()
    
    # List configurations
    if args.list:
        detector.print_configurations()
        return 0
    
    # Get available configurations
    configs = detector.get_available_configurations()
    if not configs:
        print("ERROR: No configurations available!")
        detector.print_configurations()
        return 1
    
    # Filter configurations if specified
    if args.config:
        filtered_configs = [c for c in configs if args.config.lower() in c['name'].lower()]
        if not filtered_configs:
            print(f"ERROR: No configurations match '{args.config}'")
            print("\nAvailable configurations:")
            for config in configs:
                print(f"  - {config['name']}")
            return 1
        configs = filtered_configs
    
    # Create driver
    try:
        driver = create_driver(args.browser, args.headless)
        driver.implicitly_wait(10)
    except Exception as e:
        print(f"ERROR: Failed to create WebDriver: {e}")
        return 1
    
    try:
        # Run tests
        runner = SmokeTestRunner()
        
        if len(configs) == 1:
            print(f"Running smoke test for: {configs[0]['name']}")
            result = runner.run_single_test(configs[0], driver, test_image_path)
            results = [result]
        else:
            print(f"Running smoke tests for {len(configs)} configurations...")
            results = runner.run_all_tests(driver, test_image_path, args.config)
        
        # Print summary
        success = runner.print_summary(results)
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\nWARNING: Tests interrupted by user")
        return 1
    except Exception as e:
        print(f"ERROR: Test execution failed: {e}")
        return 1
    finally:
        driver.quit()


if __name__ == "__main__":
    sys.exit(main())