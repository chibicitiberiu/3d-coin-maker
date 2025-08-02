from abc import ABC, abstractmethod
from collections.abc import Callable
from pathlib import Path

from core.models import CoinParameters


class ISTLGenerator(ABC):
    """Interface for STL generation operations."""

    @abstractmethod
    def generate_stl(
        self,
        heightmap_path: Path,
        coin_parameters: CoinParameters,
        output_path: Path,
        progress_callback: Callable[[int, str], None] | None = None
    ) -> tuple[bool, str | None]:
        """Generate STL file from heightmap and coin parameters.

        Args:
            heightmap_path: Path to the heightmap image
            coin_parameters: Parameters for coin generation
            output_path: Path where STL should be saved
            progress_callback: Optional callback for progress updates (progress: int, step: str)

        Returns:
            tuple[bool, str | None]: (success, error_message)

        Raises:
            ProcessingError: If generation fails
        """
        pass

    @abstractmethod
    def validate_parameters(self, parameters: CoinParameters) -> bool:
        """Validate coin parameters."""
        pass
