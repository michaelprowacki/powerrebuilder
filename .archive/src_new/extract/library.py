"""Library Class - PowerBuilder Library extraction support.

This module provides the Library class that was missing from the adapters,
needed for proper PBL/PBD extraction compatibility with main.py.
"""

import asyncio
import logging
from pathlib import Path
from typing import AsyncIterator, Iterator, List, Optional

from src_new._core import ExtractedObject, ObjectType, PBLEntry
from src_new._patterns import FileHandler
from .extractor import PBLParser

logger = logging.getLogger(__name__)


class Library:
    """PowerBuilder Library handler for PBL/PBD files.

    Provides compatibility with the original main.py imports.
    """

    def __init__(self, file_path: Optional[Path] = None):
        """Initialize library.

        Args:
            file_path: Path to PBL/PBD file
        """
        self.file_path = Path(file_path) if file_path else None
        self.pbl_file = None
        self.entries = []
        self._parser = None

    def open(self, file_path: Path) -> None:
        """Open a library file.

        Args:
            file_path: Path to PBL/PBD file
        """
        self.file_path = Path(file_path)
        self._parser = PBLParser(self.file_path)
        self.pbl_file = self._parser.parse()
        self.entries = self.pbl_file.entries

    def close(self) -> None:
        """Close the library."""
        self.file_path = None
        self.pbl_file = None
        self.entries = []
        self._parser = None

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, *args):
        """Context manager exit."""
        self.close()

    def get_entries(self) -> List[PBLEntry]:
        """Get all entries in the library.

        Returns:
            List of library entries
        """
        return self.entries

    def extract_entry(self, entry: PBLEntry) -> bytes:
        """Extract data for a specific entry.

        Args:
            entry: Entry to extract

        Returns:
            Extracted data bytes
        """
        if not self._parser:
            raise RuntimeError("Library not opened")
        return self._parser.extract_data(entry)

    def extract_all(self, output_dir: Path) -> int:
        """Extract all entries to a directory.

        Args:
            output_dir: Output directory

        Returns:
            Number of extracted files
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        extracted = 0
        file_handler = FileHandler()

        for entry in self.entries:
            try:
                data = self.extract_entry(entry)

                # Determine output file
                output_file = output_dir / entry.name

                # Add extension if needed
                if not any(
                    entry.name.endswith(ext)
                    for ext in [
                        ".sru",
                        ".srw",
                        ".srm",
                        ".srd",
                        ".srf",
                        ".srs",
                        ".sra",
                        ".fun",
                    ]
                ):
                    ext_map = {
                        ObjectType.WINDOW: ".srw",
                        ObjectType.USER_OBJECT: ".sru",
                        ObjectType.MENU: ".srm",
                        ObjectType.DATAWINDOW: ".srd",
                        ObjectType.FUNCTION: ".fun",
                        ObjectType.STRUCTURE: ".srs",
                        ObjectType.APPLICATION: ".sra",
                    }
                    output_file = output_file.with_suffix(
                        ext_map.get(entry.type, ".sru")
                    )

                # Write file
                if self._is_text_data(data):
                    text = data.decode("utf-8", errors="replace")
                    file_handler.write_text(output_file, text)
                else:
                    file_handler.write_binary(output_file, data)

                extracted += 1

            except Exception as e:
                logger.error(f"Failed to extract {entry.name}: {e}")

        return extracted

    def _is_text_data(self, data: bytes) -> bool:
        """Check if data is text.

        Args:
            data: Data to check

        Returns:
            True if text data
        """
        if not data:
            return False

        # Check for BOM markers
        if data.startswith(b"\xef\xbb\xbf"):  # UTF-8
            return True
        if data.startswith(b"\xff\xfe") or data.startswith(b"\xfe\xff"):  # UTF-16
            return True

        # Sample check
        sample = data[:1000]
        try:
            sample.decode("utf-8")
            text_chars = sum(
                1 for b in sample if b in range(32, 127) or b in [9, 10, 13]
            )
            return text_chars > len(sample) * 0.7
        except:
            return False

    def iter_entries(self) -> Iterator[PBLEntry]:
        """Iterate over library entries.

        Yields:
            Library entries
        """
        for entry in self.entries:
            yield entry

    async def aiter_entries(self) -> AsyncIterator[PBLEntry]:
        """Async iterate over library entries.

        Yields:
            Library entries
        """
        for entry in self.entries:
            await asyncio.sleep(0)  # Yield control
            yield entry

    def find_entry(self, name: str) -> Optional[PBLEntry]:
        """Find an entry by name.

        Args:
            name: Entry name

        Returns:
            Entry if found, None otherwise
        """
        for entry in self.entries:
            if entry.name == name:
                return entry
        return None

    def get_statistics(self) -> dict:
        """Get library statistics.

        Returns:
            Statistics dictionary
        """
        if not self.pbl_file:
            return {}

        type_counts = {}
        for entry in self.entries:
            type_name = entry.type.value
            type_counts[type_name] = type_counts.get(type_name, 0) + 1

        return {
            "file_path": str(self.file_path),
            "version": self.pbl_file.version,
            "total_entries": len(self.entries),
            "total_size": self.pbl_file.size,
            "checksum": self.pbl_file.checksum,
            "types": type_counts,
        }


class PBLExtractor:
    """Async PBL extractor for compatibility."""

    def __init__(self):
        """Initialize extractor."""
        self.library = Library()

    async def extract_pbl(self, path: Path) -> AsyncIterator[ExtractedObject]:
        """Extract objects from PBL file.

        Args:
            path: Path to PBL/PBD file

        Yields:
            Extracted objects
        """
        self.library.open(path)

        try:
            async for entry in self.library.aiter_entries():
                try:
                    data = self.library.extract_entry(entry)

                    yield ExtractedObject(
                        name=entry.name,
                        type=entry.type,
                        data=data,
                        source_file=str(path),
                    )

                except Exception as e:
                    logger.warning(f"Failed to extract {entry.name}: {e}")

        finally:
            self.library.close()
