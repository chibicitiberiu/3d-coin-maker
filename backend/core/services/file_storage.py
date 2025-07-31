import time
from pathlib import Path

from django.conf import settings

from core.interfaces.storage import IFileStorage, UploadedFile


class FileSystemStorage(IFileStorage):
    """File system implementation of IFileStorage."""

    def __init__(self):
        self._temp_dir = Path(settings.TEMP_DIR)
        self._temp_dir.mkdir(parents=True, exist_ok=True)

    @property
    def temp_dir(self) -> Path:
        """Get the temporary directory path."""
        return self._temp_dir

    def save_file(self, file_data: UploadedFile, filename: str, generation_id: str) -> Path:
        """Save a file and return its path."""
        generation_dir = self._temp_dir / generation_id
        generation_dir.mkdir(parents=True, exist_ok=True)

        file_path = generation_dir / filename
        with open(file_path, 'wb') as f:
            for chunk in file_data.chunks():
                f.write(chunk)

        return file_path

    def get_file_path(self, filename: str, generation_id: str) -> Path | None:
        """Get the path to a stored file."""
        file_path = self._temp_dir / generation_id / filename
        return file_path if file_path.exists() else None

    def delete_file(self, filename: str, generation_id: str) -> bool:
        """Delete a stored file."""
        file_path = self._temp_dir / generation_id / filename
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

        for generation_dir in self._temp_dir.iterdir():
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
