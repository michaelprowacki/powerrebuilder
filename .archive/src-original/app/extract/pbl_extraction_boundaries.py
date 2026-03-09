"""Extract Application - Ports.

Small, specific interfaces for the extract slice.
Uses domain types, not primitives where possible.
"""

from typing import Protocol, List
from src_new.domain.extract.shared import PBLEntry


class IFileReader(Protocol):
    """Port for reading binary files."""

    async def read_binary(self, path: str) -> bytes:
        """Read binary file contents.

        Args:
            path: File path to read

        Returns:
            Raw bytes from file

        Raises:
            IOError: If file cannot be read
        """
        ...

    async def file_exists(self, path: str) -> bool:
        """Check if file exists.

        Args:
            path: File path to check

        Returns:
            True if file exists
        """
        ...


class IObjectWriter(Protocol):
    """Port for writing extracted objects."""

    async def write_entries(self, output_dir: str, entries: List[PBLEntry]) -> None:
        """Write extracted entries to storage.

        Args:
            output_dir: Directory to write to
            entries: Extracted PBL entries to write

        Raises:
            IOError: If write fails
        """
        ...

    async def write_metadata(self, output_dir: str, metadata: dict) -> None:
        """Write extraction metadata.

        Args:
            output_dir: Directory to write to
            metadata: Metadata dictionary to persist
        """
        ...
