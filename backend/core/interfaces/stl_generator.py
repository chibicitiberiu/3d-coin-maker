from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any


class ISTLGenerator(ABC):
    """Interface for STL generation operations."""

    @abstractmethod
    def generate_stl(
        self,
        heightmap_path: Path,
        coin_parameters: dict[str, Any],
        output_path: Path
    ) -> bool:
        """Generate STL file from heightmap and coin parameters."""
        pass

    @abstractmethod
    def validate_parameters(self, parameters: dict[str, Any]) -> bool:
        """Validate coin parameters."""
        pass
