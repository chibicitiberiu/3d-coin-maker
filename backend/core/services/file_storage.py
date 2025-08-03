import time
from pathlib import Path

from core.constants import PerformanceConstants
from core.interfaces.storage import IFileStorage, UploadedFile
from core.services.path_resolver import path_resolver


class FileSystemStorage(IFileStorage):
    """File system implementation of IFileStorage."""

    def __init__(self, generations_dir: str | None = None):
        # Use path resolver for consistent generations directory handling
        self._generations_dir = path_resolver.get_generations_dir(generations_dir)

    @property
    def generations_dir(self) -> Path:
        """Get the generations directory path."""
        return self._generations_dir

    def save_file(self, file_data: UploadedFile, filename: str, generation_id: str) -> Path:
        """Save a file and return its path."""
        generation_dir = self._generations_dir / generation_id
        generation_dir.mkdir(parents=True, exist_ok=True)

        file_path = generation_dir / filename
        with open(file_path, 'wb') as f:
            # Handle both Django-style (chunks()) and FastAPI-style (file.file) file objects
            if hasattr(file_data, 'chunks'):
                # Django-style UploadedFile
                for chunk in file_data.chunks():
                    f.write(chunk)
            elif hasattr(file_data, 'file') and hasattr(file_data.file, 'read'):
                # FastAPI UploadFile - has a .file attribute with file-like interface
                file_data.file.seek(0)  # Ensure we're at the beginning
                while True:
                    chunk = file_data.file.read(PerformanceConstants.FILE_CHUNK_SIZE)  # Read in 8KB chunks
                    if not chunk:
                        break
                    f.write(chunk)
            else:
                raise ValueError(f"Unsupported file object type: {type(file_data)}")

        return file_path

    def get_file_path(self, filename: str, generation_id: str) -> Path | None:
        """Get the path to a stored file."""
        file_path = self._generations_dir / generation_id / filename
        return file_path if file_path.exists() else None

    def delete_file(self, filename: str, generation_id: str) -> bool:
        """Delete a stored file."""
        file_path = self._generations_dir / generation_id / filename
        try:
            if file_path.exists():
                file_path.unlink()
                # Remove empty directory
                parent_dir = file_path.parent
                if parent_dir.is_dir() and not any(parent_dir.iterdir()):
                    parent_dir.rmdir()
                return True
        except OSError:
            pass
        return False

    def cleanup_old_files(self, max_age_seconds: int) -> int:
        """Clean up files older than max_age_seconds."""
        deleted_count = 0
        current_time = time.time()

        for generation_dir in self._generations_dir.iterdir():
            if not generation_dir.is_dir():
                continue

            # Check if directory is old enough to delete
            dir_age = current_time - generation_dir.stat().st_mtime
            if dir_age > max_age_seconds:
                try:
                    # Delete all files in directory
                    for file_path in generation_dir.iterdir():
                        if file_path.is_file():
                            file_path.unlink()
                            deleted_count += 1
                    # Remove empty directory
                    generation_dir.rmdir()
                except OSError:
                    continue

        return deleted_count
