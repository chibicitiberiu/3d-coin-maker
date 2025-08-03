from abc import ABC, abstractmethod
from pathlib import Path
from typing import Protocol


class UploadedFile(Protocol):
    """Protocol for uploaded files."""
    def chunks(self) -> list[bytes]:
        """Return file chunks."""
        ...


class IFileStorage(ABC):
    """Interface for file storage operations."""

    @property
    @abstractmethod
    def generations_dir(self) -> Path:
        """Get the generations directory path."""
        pass

    @abstractmethod
    def save_file(self, file_data: UploadedFile, filename: str, generation_id: str) -> Path:
        """Save a file and return its path."""
        pass

    @abstractmethod
    def get_file_path(self, filename: str, generation_id: str) -> Path | None:
        """Get the path to a stored file."""
        pass

    @abstractmethod
    def delete_file(self, filename: str, generation_id: str) -> bool:
        """Delete a stored file."""
        pass

    @abstractmethod
    def cleanup_old_files(self, max_age_seconds: int) -> int:
        """Clean up files older than max_age_seconds. Returns count of deleted files."""
        pass
