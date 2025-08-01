"""
FastAPI Main Application

Modern API server replacing Django for the Coin Maker application.
Provides the same REST API endpoints with better performance and
smaller bundle size for desktop deployment.
"""

# Initialize FastAPI settings
import time
from uuid import UUID

from fastapi import FastAPI, HTTPException, Request, UploadFile, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from core.interfaces.task_queue import TaskQueue
from core.services.coin_generation_service import CoinGenerationService
from fastapi_dependencies import ClientIPDep, CoinServiceDep, TaskQueueDep
from fastapi_models import (
    CoinParametersRequest,
    GenerationStatusResponse,
    HealthCheckResponse,
    ImageProcessingRequest,
    TaskResponse,
    UploadResponse,
    validate_image_file,
)
from fastapi_settings import settings

# Create FastAPI application
app = FastAPI(
    title="Coin Maker API",
    description="3D Coin Generation API - Create STL files from images",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Custom exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors with consistent error format."""
    errors = []
    for error in exc.errors():
        field = " -> ".join(str(x) for x in error["loc"])
        message = error["msg"]
        errors.append(f"{field}: {message}")

    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail={"error": "Validation failed", "details": errors}
    )


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """Handle ValueError exceptions."""
    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail={"error": str(exc)}
    )


# API Routes

@app.post("/api/upload/", response_model=UploadResponse, status_code=201)
async def upload_image(
    image: UploadFile,
    coin_service: CoinGenerationService = CoinServiceDep,
    client_ip: str = ClientIPDep
) -> UploadResponse:
    """Upload image and create generation session."""

    # Validate the uploaded file
    try:
        validate_image_file(image)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": str(e)}
        ) from e

    # Create generation session
    success, result, error_msg = coin_service.create_generation(image, client_ip)

    if not success:
        if result == "rate_limit_exceeded":
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={"error": error_msg}
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": error_msg}
        )

    generation_id = result
    return UploadResponse(
        generation_id=UUID(generation_id) if isinstance(generation_id, str) else generation_id,
        message="Image uploaded successfully"
    )


@app.post("/api/process/", response_model=TaskResponse, status_code=202)
async def process_image(
    request_data: ImageProcessingRequest,
    task_queue: TaskQueue = TaskQueueDep
) -> TaskResponse:
    """Process uploaded image with parameters."""

    # Convert Pydantic model to dict for task queue
    parameters = request_data.dict()
    generation_id = str(parameters['generation_id'])

    # Start background processing task
    task_id = task_queue.enqueue(
        task_name='process_image_task',
        args=(generation_id, parameters),
        max_retries=3,
        retry_delay=60
    )

    return TaskResponse(
        task_id=task_id,
        generation_id=request_data.generation_id,
        message="Image processing started"
    )


@app.post("/api/generate/", response_model=TaskResponse, status_code=202)
async def generate_stl(
    request_data: CoinParametersRequest,
    task_queue: TaskQueue = TaskQueueDep
) -> TaskResponse:
    """Generate STL file from processed image."""

    # Convert Pydantic model to dict for task queue
    parameters = request_data.dict()
    generation_id = str(parameters['generation_id'])

    # Start background STL generation task
    task_id = task_queue.enqueue(
        task_name='generate_stl_task',
        args=(generation_id, parameters),
        max_retries=3,
        retry_delay=60
    )

    return TaskResponse(
        task_id=task_id,
        generation_id=request_data.generation_id,
        message="STL generation started"
    )


@app.get("/api/status/{generation_id}/", response_model=GenerationStatusResponse)
async def generation_status(
    generation_id: str,
    request: Request,
    coin_service: CoinGenerationService = CoinServiceDep,
    task_queue: TaskQueue = TaskQueueDep
) -> GenerationStatusResponse:
    """Get status of generation process."""

    try:
        # Check if any tasks exist for this generation
        task_id = request.query_params.get('task_id')

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
                stl_timestamp = int(stl_path.stat().st_mtime * 1000)  # milliseconds timestamp
            except (OSError, AttributeError):
                stl_timestamp = int(time.time() * 1000)

        # Ensure progress is an integer
        progress_value = task_info.get('progress', 0)
        if not isinstance(progress_value, int):
            progress_value = int(progress_value) if progress_value is not None else 0

        return GenerationStatusResponse(
            generation_id=UUID(generation_id) if isinstance(generation_id, str) else generation_id,
            status=task_status,
            progress=progress_value,
            step=task_info.get('step', 'unknown'),
            error=task_info.get('error'),
            has_original=has_original,
            has_processed=has_processed,
            has_heightmap=has_heightmap,
            has_stl=has_stl,
            stl_timestamp=stl_timestamp
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": f"Error getting status: {str(e)}"}
        ) from e


@app.get("/api/download/{generation_id}/stl")
async def download_stl(
    generation_id: str,
    request: Request,
    coin_service: CoinGenerationService = CoinServiceDep
) -> FileResponse:
    """Download generated STL file."""

    stl_path = coin_service.get_file_path(generation_id, 'stl')

    if not stl_path or not stl_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "STL file not found"}
        )

    # Get timestamp parameter for cache busting (if provided by frontend)
    timestamp = request.query_params.get('t', '')
    filename = f"coin_{generation_id}_{timestamp}.stl" if timestamp else f"coin_{generation_id}.stl"

    return FileResponse(
        path=stl_path,
        media_type='application/octet-stream',
        filename=filename,
        headers={
            'Cache-Control': 'no-cache, no-store, must-revalidate, max-age=0',
            'Pragma': 'no-cache',
            'Expires': '0',
            'ETag': f'"{generation_id}-{timestamp}"'
        }
    )


@app.get("/api/preview/{generation_id}")
async def preview_image(
    generation_id: str,
    request: Request,
    coin_service: CoinGenerationService = CoinServiceDep
) -> FileResponse:
    """Get processed/heightmap image preview."""

    image_type = request.query_params.get('type', 'processed')  # 'processed' or 'heightmap'

    if image_type not in ['processed', 'heightmap']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": 'Invalid image type. Use "processed" or "heightmap"'}
        )

    image_path = coin_service.get_file_path(generation_id, image_type)

    if not image_path or not image_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "Image not found"}
        )

    return FileResponse(
        path=image_path,
        media_type='image/png',
        headers={
            'Cache-Control': 'no-cache, no-store, must-revalidate',
            'Pragma': 'no-cache',
            'Expires': '0'
        }
    )


@app.get("/api/health/", response_model=HealthCheckResponse)
async def health_check(
    task_queue: TaskQueue = TaskQueueDep
) -> HealthCheckResponse:
    """Health check endpoint to verify system status."""


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
        if settings.use_celery:
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
        temp_dir = settings.temp_path
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

    # Return appropriate status code
    response_status = 200 if status_info['status'] == 'healthy' else 503

    if response_status != 200:
        raise HTTPException(
            status_code=response_status,
            detail=status_info
        )

    return HealthCheckResponse(**status_info)


# Root redirect for API documentation
@app.get("/")
async def root():
    """Redirect to API documentation."""
    return {"message": "Coin Maker API", "docs": "/api/docs", "redoc": "/api/redoc"}


if __name__ == "__main__":
    import uvicorn

    # Initialize the application container
    from core.containers.application import initialize_task_queue
    initialize_task_queue()

    # Run the FastAPI server
    uvicorn.run(
        "fastapi_main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="debug" if settings.debug else "info"
    )
