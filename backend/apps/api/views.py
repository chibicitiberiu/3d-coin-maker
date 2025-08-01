
import time
from pathlib import Path
from typing import Any, cast

from dependency_injector.wiring import Provide, inject
from django.http import FileResponse, Http404
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.request import Request
from rest_framework.response import Response

from core.containers.application import ApplicationContainer
from core.interfaces.task_queue import TaskQueue
from core.services.coin_generation_service import CoinGenerationService

from .serializers import (
    CoinParametersSerializer,
    GenerationStatusSerializer,
    ImageProcessingSerializer,
    ImageUploadSerializer,
)


def get_client_ip(request: Request) -> str:
    """Get client IP address from request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR', '127.0.0.1')
    return ip


@api_view(['POST'])
@inject
def upload_image(
    request: Request,
    coin_service: CoinGenerationService = Provide[ApplicationContainer.coin_generation_service]
) -> Response:
    """Upload image and create generation session."""
    serializer = ImageUploadSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    validated_data = serializer.validated_data
    if not validated_data:
        return Response({'error': 'Invalid data'}, status=status.HTTP_400_BAD_REQUEST)
    uploaded_file = cast(Any, validated_data)['image']
    client_ip = get_client_ip(request)

    # Create generation session
    success, result, error_msg = coin_service.create_generation(uploaded_file, client_ip)

    if not success:
        if result == "rate_limit_exceeded":
            return Response(
                {'error': error_msg},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )
        return Response(
            {'error': error_msg},
            status=status.HTTP_400_BAD_REQUEST
        )

    generation_id = result
    return Response({
        'generation_id': generation_id,
        'message': 'Image uploaded successfully'
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@inject
def process_image(
    request: Request,
    task_queue: TaskQueue = Provide[ApplicationContainer.task_queue]
) -> Response:
    """Process uploaded image with parameters."""
    serializer = ImageProcessingSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    validated_data = serializer.validated_data
    if not validated_data:
        return Response({'error': 'Invalid data'}, status=status.HTTP_400_BAD_REQUEST)
    data = cast(dict[str, Any], validated_data)
    generation_id = str(data['generation_id'])

    # Start background processing task using the injected task queue
    task_id = task_queue.enqueue(
        task_name='process_image_task',
        args=(generation_id, data),
        max_retries=3,
        retry_delay=60
    )

    return Response({
        'task_id': task_id,
        'generation_id': generation_id,
        'message': 'Image processing started'
    }, status=status.HTTP_202_ACCEPTED)


@api_view(['POST'])
@inject
def generate_stl(
    request: Request,
    task_queue: TaskQueue = Provide[ApplicationContainer.task_queue]
) -> Response:
    """Generate STL file from processed image."""
    serializer = CoinParametersSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    validated_data = serializer.validated_data
    if not validated_data:
        return Response({'error': 'Invalid data'}, status=status.HTTP_400_BAD_REQUEST)
    data = cast(dict[str, Any], validated_data)
    generation_id = str(data['generation_id'])

    # Start background STL generation task using the injected task queue
    task_id = task_queue.enqueue(
        task_name='generate_stl_task',
        args=(generation_id, data),
        max_retries=3,
        retry_delay=60
    )

    return Response({
        'task_id': task_id,
        'generation_id': generation_id,
        'message': 'STL generation started'
    }, status=status.HTTP_202_ACCEPTED)


@api_view(['GET'])
@inject
def generation_status(
    request: Request,
    generation_id: str,
    coin_service: CoinGenerationService = Provide[ApplicationContainer.coin_generation_service],
    task_queue: TaskQueue = Provide[ApplicationContainer.task_queue]
) -> Response:
    """Get status of generation process."""
    try:
        # Check if any tasks exist for this generation
        task_id = request.GET.get('task_id')

        if task_id:
            # Get task status using the task queue abstraction
            try:
                task_result = task_queue.get_result(task_id)
                if task_result:
                    task_status = task_result.status.value  # Convert enum to string
                    task_info = {
                        'progress': task_result.progress.get('progress', 0) if task_result.progress else 0,
                        'step': task_result.progress.get('step', 'unknown') if task_result.progress else 'unknown',
                        'error': task_result.error
                    }
                else:
                    task_status = 'UNKNOWN'
                    task_info = {'error': 'Task not found'}

            except Exception as e:
                task_status = 'FAILURE'
                task_info = {'error': f'Error retrieving task status: {str(e)}'}
        else:
            task_status = 'UNKNOWN'
            task_info = {}

        # Check file availability and get timestamps
        has_original = coin_service.get_file_path(generation_id, 'original') is not None
        has_processed = coin_service.get_file_path(generation_id, 'processed') is not None
        has_heightmap = coin_service.get_file_path(generation_id, 'heightmap') is not None

        stl_path = coin_service.get_file_path(generation_id, 'stl')
        has_stl = stl_path is not None and stl_path.exists()

        # Get STL file timestamp for cache busting
        stl_timestamp = None
        if has_stl and stl_path is not None:
            try:
                import time
                stl_timestamp = int(stl_path.stat().st_mtime * 1000)  # milliseconds timestamp
            except (OSError, AttributeError):
                import time
                stl_timestamp = int(time.time() * 1000)

        response_data = {
            'generation_id': generation_id,
            'status': task_status,
            'progress': task_info.get('progress', 0),
            'step': task_info.get('step', 'unknown'),
            'error': task_info.get('error'),
            'has_original': has_original,
            'has_processed': has_processed,
            'has_heightmap': has_heightmap,
            'has_stl': has_stl,
            'stl_timestamp': stl_timestamp
        }

        serializer = GenerationStatusSerializer(response_data)
        return Response(serializer.data)

    except Exception as e:
        return Response(
            {'error': f'Error getting status: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@inject
def download_stl(
    request: Request,
    generation_id: str,
    coin_service: CoinGenerationService = Provide[ApplicationContainer.coin_generation_service]
) -> FileResponse:
    """Download generated STL file."""
    stl_path = coin_service.get_file_path(generation_id, 'stl')

    if not stl_path or not stl_path.exists():
        raise Http404("STL file not found")

    response = FileResponse(
        open(stl_path, 'rb'),
        content_type='application/octet-stream'
    )

    # Get timestamp parameter for cache busting (if provided by frontend)
    timestamp = request.GET.get('t', '')
    filename = f"coin_{generation_id}_{timestamp}.stl" if timestamp else f"coin_{generation_id}.stl"

    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    # Add aggressive cache-busting headers
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    response['ETag'] = f'"{generation_id}-{timestamp}"'

    return response


@api_view(['GET'])
@inject
def preview_image(
    request: Request,
    generation_id: str,
    coin_service: CoinGenerationService = Provide[ApplicationContainer.coin_generation_service]
) -> Response | FileResponse:
    """Get processed/heightmap image preview."""
    image_type = request.GET.get('type', 'processed')  # 'processed' or 'heightmap'

    if image_type not in ['processed', 'heightmap']:
        return Response(
            {'error': 'Invalid image type. Use "processed" or "heightmap"'},
            status=status.HTTP_400_BAD_REQUEST
        )

    image_path = coin_service.get_file_path(generation_id, image_type)

    if not image_path or not image_path.exists():
        raise Http404("Image not found")

    response = FileResponse(
        open(image_path, 'rb'),
        content_type='image/png'
    )

    # Add cache-busting headers to prevent browser caching
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'

    return response


@api_view(['GET'])
@inject
def health_check(
    request: Request,
    task_queue: TaskQueue = Provide[ApplicationContainer.task_queue]
) -> Response:
    """Health check endpoint to verify system status."""

    from django.conf import settings

    status_info = {
        'status': 'healthy',
        'services': {},
        'timestamp': time.time()
    }

    # Check Task Queue
    try:
        task_queue_health = task_queue.health_check()
        status_info['services']['task_queue'] = task_queue_health
        if task_queue_health['status'] != 'healthy':
            status_info['status'] = 'degraded'
    except Exception as e:
        status_info['services']['task_queue'] = {
            'status': 'error',
            'error': str(e)
        }
        status_info['status'] = 'degraded'

    # Check Redis connection (only if using Celery)
    try:
        import os
        if os.getenv('USE_CELERY', 'true').lower() in ('true', '1', 'yes', 'on'):
            from core.containers.application import container
            redis_client = container.redis_client()
            redis_client.ping()
            status_info['services']['redis'] = {'status': 'connected'}
        else:
            status_info['services']['redis'] = {'status': 'skipped', 'reason': 'Using APScheduler'}
    except Exception as e:
        status_info['services']['redis'] = {
            'status': 'error',
            'error': str(e)
        }
        status_info['status'] = 'degraded'

    # Check temp directory
    try:
        temp_dir = Path(settings.TEMP_DIR)
        temp_dir.mkdir(exist_ok=True)
        test_file = temp_dir / 'health_check.tmp'
        test_file.write_text('test')
        test_file.unlink()
        status_info['services']['storage'] = {'status': 'writable'}
    except Exception as e:
        status_info['services']['storage'] = {
            'status': 'error',
            'error': str(e)
        }
        status_info['status'] = 'degraded'

    response_status = status.HTTP_200_OK if status_info['status'] == 'healthy' else status.HTTP_503_SERVICE_UNAVAILABLE
    return Response(status_info, status=response_status)
