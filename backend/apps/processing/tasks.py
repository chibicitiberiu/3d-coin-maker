from typing import Any

from celery import shared_task


@shared_task(bind=True)
def process_image_task(
    self,
    generation_id: str,
    parameters: dict[str, Any]
):
    """Celery task for processing uploaded images."""
    try:
        # Import container inside task to avoid circular imports
        from core.containers.application import container
        coin_service = container.coin_generation_service()

        # Update task state
        self.update_state(
            state='PROCESSING',
            meta={'step': 'image_processing', 'progress': 10}
        )

        # Process the image
        success, error_msg = coin_service.process_image(generation_id, parameters)

        if not success:
            self.update_state(
                state='FAILURE',
                meta={'error': error_msg}
            )
            return {'success': False, 'error': error_msg}

        # Update progress
        self.update_state(
            state='SUCCESS',
            meta={'step': 'image_processed', 'progress': 100}
        )

        return {
            'success': True,
            'generation_id': generation_id,
            'step': 'image_processed'
        }

    except Exception as exc:
        self.update_state(
            state='FAILURE',
            meta={'error': str(exc)}
        )
        raise exc


@shared_task(bind=True)
def generate_stl_task(
    self,
    generation_id: str,
    coin_parameters: dict[str, Any]
):
    """Celery task for generating STL files."""
    try:
        # Import container inside task to avoid circular imports
        from core.containers.application import container
        coin_service = container.coin_generation_service()

        # Update task state
        self.update_state(
            state='PROCESSING',
            meta={'step': 'stl_generation', 'progress': 10}
        )

        # Generate STL
        success, error_msg = coin_service.generate_stl(generation_id, coin_parameters)

        if not success:
            self.update_state(
                state='FAILURE',
                meta={'error': error_msg}
            )
            return {'success': False, 'error': error_msg}

        # Update progress
        self.update_state(
            state='SUCCESS',
            meta={'step': 'stl_generated', 'progress': 100}
        )

        return {
            'success': True,
            'generation_id': generation_id,
            'step': 'stl_generated'
        }

    except Exception as exc:
        self.update_state(
            state='FAILURE',
            meta={'error': str(exc)}
        )
        raise exc


@shared_task
def cleanup_old_files_task():
    """Periodic task to clean up old files."""
    from django.conf import settings

    try:
        # Import container inside task to avoid circular imports  
        from core.containers.application import container
        file_storage = container.file_storage()

        deleted_count = file_storage.cleanup_old_files(settings.FILE_RETENTION)
        return {
            'success': True,
            'deleted_files': deleted_count,
            'message': f'Cleaned up {deleted_count} old files'
        }
    except Exception as exc:
        return {
            'success': False,
            'error': str(exc)
        }
