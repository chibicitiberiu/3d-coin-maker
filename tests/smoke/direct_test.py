#!/usr/bin/env python3
"""
Direct smoke test against running application without container management.
"""
import sys
import os
from cli import create_driver
from base_test import BaseSmokeTest

def main():
    # Use running containers
    frontend_url = "http://localhost:5173"
    health_url = "http://localhost:8000/health/"
    
    # Get test image path
    test_image_path = os.path.join("tests", "smoke", "assets", "test-coin-image.png")
    
    if not os.path.exists(test_image_path):
        print(f"ERROR: Test image not found: {test_image_path}")
        return 1
    
    # Create driver
    try:
        driver = create_driver("firefox", True)  # Headless mode
        driver.implicitly_wait(10)
    except Exception as e:
        print(f"ERROR: Failed to create WebDriver: {e}")
        return 1
    
    try:
        # Run test
        test = BaseSmokeTest(driver)
        results = test.run_full_test(
            frontend_url,
            health_url,
            test_image_path
        )
        
        # Check results
        failed_steps = [step for step, passed in results.items() if not passed]
        
        if failed_steps:
            print(f"FAILED steps: {failed_steps}")
            return 1
        else:
            print("All tests PASSED!")
            return 0

    except Exception as e:
        print(f"ERROR: Test execution failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        driver.quit()

if __name__ == "__main__":
    sys.exit(main())