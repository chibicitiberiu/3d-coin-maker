#!/usr/bin/env python3
"""
Test individual smoke test components step by step.
"""
import sys
import os
from selenium import webdriver
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.firefox.service import Service

def main():
    print("=== Component-by-Component Smoke Test ===")
    
    # Setup WebDriver
    options = FirefoxOptions()
    options.add_argument("--headless")
    options.add_argument("--width=1920")
    options.add_argument("--height=1080")
    
    webdriver_dir = "/home/tibi/Dev/coin-maker/build/test-drivers"
    geckodriver_path = os.path.join(webdriver_dir, "geckodriver")
    service = Service(geckodriver_path)
    driver = webdriver.Firefox(service=service, options=options)
    driver.implicitly_wait(10)
    
    try:
        # Import BaseSmokeTest
        sys.path.insert(0, '/home/tibi/Dev/coin-maker/tests/smoke')
        from base_test import BaseSmokeTest
        
        test = BaseSmokeTest(driver)
        
        frontend_url = "http://localhost:5173"
        health_url = "http://localhost:8000/health/"
        test_image_path = "/home/tibi/Dev/coin-maker/tests/smoke/assets/test-coin-image.png"
        
        print("\\n1. Testing health check...")
        health_result = test.verify_health_check(health_url)
        print(f"Health check result: {health_result}")
        
        print("\\n2. Testing frontend load...")
        frontend_result = test.load_frontend(frontend_url)
        print(f"Frontend load result: {frontend_result}")
        
        if frontend_result:
            print("\\n3. Testing image upload...")
            upload_result = test.upload_test_image(test_image_path)
            print(f"Image upload result: {upload_result}")
            
            print("\\n4. Testing parameter setting...")
            param_result = test.set_coin_parameters(25.0, 2.0, 1.0)
            print(f"Parameter setting result: {param_result}")
            
            print("\\n5. Testing STL generation...")
            generate_result = test.generate_stl()
            print(f"STL generation result: {generate_result}")
            
            if generate_result:
                print("\\n6. Testing STL download...")
                download_result = test.download_stl()
                print(f"STL download result: {download_result}")
                
                if download_result:
                    print("\\n7. Testing STL validation...")
                    validation_result = test.validate_stl_file(download_result)
                    print(f"STL validation result: {validation_result}")
        
        print("\\n=== Component Test Complete ===")
        return 0
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        driver.quit()

if __name__ == "__main__":
    sys.exit(main())