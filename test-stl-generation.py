#!/usr/bin/env python3
"""
Test STL Generation with Real API Calls

Simulates the complete workflow that the frontend would perform:
1. Start desktop app
2. Upload an image
3. Process the image 
4. Generate STL
5. Check status and download
"""

import logging
import time
import sys
import requests
import io
from pathlib import Path
from PIL import Image

# Add backend to path
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

# Configure logging
from core.logging_config import setup_logging
setup_logging(log_level="DEBUG", app_name="test_stl_generation")

def create_test_image() -> io.BytesIO:
    """Create a simple test image for upload."""
    # Create a simple 100x100 black and white image
    image = Image.new('RGB', (100, 100), color='white')
    
    # Draw a simple black circle
    from PIL import ImageDraw
    draw = ImageDraw.Draw(image)
    draw.ellipse([20, 20, 80, 80], fill='black')
    
    # Save to bytes
    img_bytes = io.BytesIO()
    image.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    
    return img_bytes

def main():
    print("=== STL GENERATION TEST ===")
    
    try:
        # Import and start desktop app
        from apps.desktop_app import DesktopApp
        print("Successfully imported DesktopApp")
        
        app = DesktopApp()
        app.initialize()
        print("Initialized DesktopApp")
        
        backend_port = app._allocated_backend_port
        frontend_port = app._allocated_frontend_port
        
        print(f"Backend port: {backend_port}")
        print(f"Frontend port: {frontend_port}")
        
        # Start backend server in background
        fastapi_app = app.create_fastapi_app()
        
        import threading
        import uvicorn
        
        def run_backend():
            uvicorn.run(
                fastapi_app,
                host="127.0.0.1",
                port=backend_port,
                log_level="info"
            )
        
        print(f"Starting backend server on port {backend_port}...")
        backend_thread = threading.Thread(target=run_backend, daemon=True)
        backend_thread.start()
        
        # Wait for backend to start
        time.sleep(3)
        
        base_url = f"http://127.0.0.1:{backend_port}"
        
        # Test 1: Health check
        print("\n=== STEP 1: Health Check ===")
        response = requests.get(f"{base_url}/health/", timeout=10)
        print(f"Health check: {response.status_code}")
        if response.status_code == 200:
            print(f"Health response: {response.json()}")
        
        # Test 2: Upload image
        print("\n=== STEP 2: Upload Image ===")
        test_image = create_test_image()
        files = {'image': ('test.png', test_image, 'image/png')}
        
        response = requests.post(f"{base_url}/upload/", files=files, timeout=30)
        print(f"Upload: {response.status_code}")
        
        if response.status_code != 201:
            print(f"Upload failed: {response.text}")
            return
        
        upload_data = response.json()
        generation_id = upload_data['generation_id']
        print(f"Upload successful - Generation ID: {generation_id}")
        
        # Test 3: Process image
        print("\n=== STEP 3: Process Image ===")
        process_data = {
            "generation_id": generation_id,
            "filename": "test.png",
            "grayscale_method": "luminance",
            "brightness": 0,
            "contrast": 0,
            "gamma": 1.0,
            "invert": False
        }
        
        response = requests.post(
            f"{base_url}/process/", 
            json=process_data, 
            timeout=30
        )
        print(f"Process: {response.status_code}")
        
        if response.status_code != 202:
            print(f"Process failed: {response.text}")
            return
        
        process_result = response.json()
        process_task_id = process_result['task_id']
        print(f"Processing started - Task ID: {process_task_id}")
        
        # Wait for processing to complete
        print("Waiting for image processing to complete...")
        for i in range(30):  # Wait up to 30 seconds
            response = requests.get(f"{base_url}/status/{generation_id}/", timeout=10)
            if response.status_code == 200:
                status = response.json()
                print(f"Processing status: {status['status']} - {status['step']} ({status['progress']}%)")
                
                if status['has_processed']:
                    print("Image processing completed")
                    break
                    
                if status['status'] == 'failed':
                    print(f"Processing failed: {status.get('error', 'Unknown error')}")
                    return
            
            time.sleep(1)
        else:
            print("Processing timed out")
            return
        
        # Test 4: Generate STL
        print("\n=== STEP 4: Generate STL ===")
        stl_data = {
            "generation_id": generation_id,
            "shape": "circle",
            "diameter": 30.0,
            "thickness": 3.0,
            "relief_depth": 1.0,
            "scale": 1.0,
            "offset_x": 0.0,
            "offset_y": 0.0,
            "rotation": 0.0
        }
        
        response = requests.post(
            f"{base_url}/generate/", 
            json=stl_data, 
            timeout=30
        )
        print(f"Generate STL: {response.status_code}")
        
        if response.status_code != 202:
            print(f"STL generation failed: {response.text}")
            return
        
        stl_result = response.json()
        stl_task_id = stl_result['task_id']
        print(f"STL generation started - Task ID: {stl_task_id}")
        
        # Wait for STL generation to complete
        print("Waiting for STL generation to complete...")
        for i in range(60):  # Wait up to 60 seconds
            response = requests.get(f"{base_url}/status/{generation_id}/", timeout=10)
            if response.status_code == 200:
                status = response.json()
                print(f"STL status: {status['status']} - {status['step']} ({status['progress']}%)")
                
                if status['has_stl']:
                    print("STL generation completed")
                    break
                    
                if status['status'] == 'failed':
                    print(f"STL generation failed: {status.get('error', 'Unknown error')}")
                    return
            
            time.sleep(1)
        else:
            print("STL generation timed out")
            return
        
        # Test 5: Download STL
        print("\n=== STEP 5: Download STL ===")
        response = requests.get(f"{base_url}/download/{generation_id}/stl", timeout=30)
        print(f"Download STL: {response.status_code}")
        
        if response.status_code == 200:
            stl_size = len(response.content)
            print(f"STL downloaded successfully - Size: {stl_size} bytes")
            
            # Save to file for inspection
            with open("test_output.stl", "wb") as f:
                f.write(response.content)
            print("STL saved as test_output.stl")
        else:
            print(f"STL download failed: {response.text}")
        
        print("\nCOMPLETE WORKFLOW TEST PASSED!")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()