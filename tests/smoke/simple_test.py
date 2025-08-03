#!/usr/bin/env python3
"""
Simplified test to debug WebDriver issues.
"""
import sys
import os
from selenium import webdriver
from selenium.webdriver.firefox.options import Options as FirefoxOptions

def main():
    print("Starting WebDriver test...")
    
    # Create Firefox options
    options = FirefoxOptions()
    options.add_argument("--headless")
    options.add_argument("--width=1920")
    options.add_argument("--height=1080")
    
    print("Creating WebDriver...")
    try:
        # Find project root and WebDriver directory
        project_root = "/home/tibi/Dev/coin-maker"
        webdriver_dir = os.path.join(project_root, "build", "test-drivers")
        
        # Try to use local GeckoDriver first
        geckodriver_path = os.path.join(webdriver_dir, "geckodriver")
        if os.path.exists(geckodriver_path):
            print(f"Using local GeckoDriver: {geckodriver_path}")
            from selenium.webdriver.firefox.service import Service
            service = Service(geckodriver_path)
            driver = webdriver.Firefox(service=service, options=options)
        else:
            print("Using system GeckoDriver")
            driver = webdriver.Firefox(options=options)
        
        print("WebDriver created successfully!")
        
        # Simple test
        print("Testing backend health check...")
        driver.get("http://localhost:8000/health/")
        
        # Get page source to verify
        source = driver.page_source[:200]
        print(f"Backend response: {source}")
        
        print("Testing frontend...")
        driver.get("http://localhost:5173/")
        
        # Get page title
        title = driver.title
        print(f"Frontend title: {title}")
        
        print("SUCCESS: Basic WebDriver test passed!")
        return 0
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        try:
            driver.quit()
            print("WebDriver closed")
        except:
            pass

if __name__ == "__main__":
    sys.exit(main())