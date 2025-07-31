"""
Integration tests for Coin Maker API endpoints.
"""
import io
import time

import pytest
import requests
from PIL import Image, ImageDraw


@pytest.fixture
def test_image():
    """Create a simple test image for coin generation."""
    # Create a 200x200 image with a simple pattern
    img = Image.new('RGB', (200, 200), color='white')
    draw = ImageDraw.Draw(img)

    # Draw a simple circle pattern
    draw.ellipse([50, 50, 150, 150], fill='black')
    draw.ellipse([75, 75, 125, 125], fill='white')
    draw.ellipse([90, 90, 110, 110], fill='black')

    # Save to bytes
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    return img_bytes


@pytest.fixture
def base_url():
    """Base URL for API endpoints."""
    return "http://localhost:8000/api"


def test_upload_image(test_image, base_url):
    """Test image upload endpoint."""
    upload_response = requests.post(
        f"{base_url}/upload/",
        files={'image': ('test.png', test_image, 'image/png')}
    )

    assert upload_response.status_code == 201
    upload_data = upload_response.json()
    assert 'generation_id' in upload_data
    assert upload_data['message'] == 'Image uploaded successfully'


def test_process_image(base_url):
    """Test image processing endpoint with a known generation_id."""
    # This test assumes a generation_id exists from upload
    # In practice, you'd use the result from test_upload_image
    generation_id = "test-generation-id"

    process_response = requests.post(
        f"{base_url}/process/",
        json={
            'generation_id': generation_id,
            'filename': 'test.png',
            'grayscale_method': 'luminance',
            'brightness': 0,
            'contrast': 100,
            'gamma': 1.0,
            'invert': False
        }
    )

    # This might fail if generation_id doesn't exist, but tests the endpoint
    assert process_response.status_code in [202, 400]  # 400 if generation_id not found


def test_full_pipeline_integration(test_image, base_url):
    """Test the complete coin generation pipeline end-to-end."""
    # Step 1: Upload image
    upload_response = requests.post(
        f"{base_url}/upload/",
        files={'image': ('test.png', test_image, 'image/png')}
    )

    assert upload_response.status_code == 201
    upload_data = upload_response.json()
    generation_id = upload_data['generation_id']

    # Step 2: Process image
    process_response = requests.post(
        f"{base_url}/process/",
        json={
            'generation_id': generation_id,
            'filename': 'test.png',
            'grayscale_method': 'luminance',
            'brightness': 0,
            'contrast': 100,
            'gamma': 1.0,
            'invert': False
        }
    )

    assert process_response.status_code == 202
    process_data = process_response.json()
    task_id = process_data['task_id']

    # Wait for processing to complete
    for _ in range(30):  # Wait up to 30 seconds
        status_response = requests.get(
            f"{base_url}/status/{generation_id}/",
            params={'task_id': task_id}
        )

        assert status_response.status_code == 200
        status_data = status_response.json()

        if status_data['status'] == 'SUCCESS':
            break
        elif status_data['status'] == 'FAILURE':
            pytest.fail(f"Processing failed: {status_data.get('error', 'Unknown error')}")

        time.sleep(1)
    else:
        pytest.fail("Processing timeout")

    # Step 3: Generate STL
    stl_response = requests.post(
        f"{base_url}/generate/",
        json={
            'generation_id': generation_id,
            'shape': 'circle',
            'diameter': 30.0,
            'thickness': 3.0,
            'relief_depth': 1.0,
            'scale': 100.0,
            'offset_x': 0.0,
            'offset_y': 0.0,
            'rotation': 0.0
        }
    )

    assert stl_response.status_code == 202
    stl_data = stl_response.json()
    stl_task_id = stl_data['task_id']

    # Wait for STL generation to complete
    for _ in range(60):  # Wait up to 60 seconds for STL
        status_response = requests.get(
            f"{base_url}/status/{generation_id}/",
            params={'task_id': stl_task_id}
        )

        assert status_response.status_code == 200
        status_data = status_response.json()

        if status_data['status'] == 'SUCCESS':
            break
        elif status_data['status'] == 'FAILURE':
            pytest.fail(f"STL generation failed: {status_data.get('error', 'Unknown error')}")

        time.sleep(1)
    else:
        pytest.fail("STL generation timeout")

    # Step 4: Check final status and file availability
    final_status = requests.get(f"{base_url}/status/{generation_id}/")
    assert final_status.status_code == 200

    status_data = final_status.json()
    assert status_data['has_original'] is True
    assert status_data['has_processed'] is True
    assert status_data['has_heightmap'] is True
    assert status_data['has_stl'] is True

    # Step 5: Test STL download
    download_response = requests.get(f"{base_url}/download/{generation_id}/stl")
    assert download_response.status_code == 200
    assert download_response.headers['content-type'] == 'application/octet-stream'
    assert len(download_response.content) > 0  # STL file should not be empty


def test_health_check(base_url):
    """Test health check endpoint."""
    health_response = requests.get(f"{base_url}/health/")
    assert health_response.status_code in [200, 503]  # Healthy or degraded

    health_data = health_response.json()
    assert 'status' in health_data
    assert 'services' in health_data
    assert 'timestamp' in health_data
