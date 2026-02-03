"""Filesystem Adapter - File I/O operations for the application.

Consolidates all filesystem operations into a single adapter.
"""

import json
from pathlib import Path
from typing import List, Dict
import asyncio


class FilesystemAdapter:
    """Unified filesystem adapter for all file operations.

    Handles reading and writing files for all domains.
    """

    def __init__(self, base_dir: str = "."):
        """Initialize with base directory.

        Args:
            base_dir: Base directory for file operations
        """
        self.base_dir = Path(base_dir)

    # Read operations
    async def read_binary(self, path: str) -> bytes:
        """Read binary file contents.

        Args:
            path: File path to read

        Returns:
            Raw bytes from file

        Raises:
            IOError: If file cannot be read
        """
        file_path = Path(path) if Path(path).is_absolute() else self.base_dir / path

        if not file_path.exists():
            raise IOError(f"File not found: {path}")

        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, file_path.read_bytes)
        except Exception as e:
            raise IOError(f"Failed to read file: {str(e)}")

    async def read_text(self, path: str, encoding: str = "utf-8") -> str:
        """Read text file contents.

        Args:
            path: File path to read
            encoding: Text encoding (default: utf-8)

        Returns:
            File contents as string

        Raises:
            IOError: If file cannot be read
        """
        file_path = Path(path) if Path(path).is_absolute() else self.base_dir / path

        if not file_path.exists():
            raise IOError(f"File not found: {path}")

        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None, lambda: file_path.read_text(encoding=encoding)
            )
        except Exception as e:
            raise IOError(f"Failed to read file: {str(e)}")

    async def file_exists(self, path: str) -> bool:
        """Check if file exists.

        Args:
            path: File path to check

        Returns:
            True if file exists
        """
        file_path = Path(path) if Path(path).is_absolute() else self.base_dir / path
        return file_path.exists()

    # Write operations
    async def write_binary(self, path: str, data: bytes) -> None:
        """Write binary data to file.

        Args:
            path: File path to write
            data: Binary data to write

        Raises:
            IOError: If write fails
        """
        file_path = Path(path) if Path(path).is_absolute() else self.base_dir / path

        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, file_path.write_bytes, data)
        except Exception as e:
            raise IOError(f"Failed to write file: {str(e)}")

    async def write_text(
        self, path: str, content: str, encoding: str = "utf-8"
    ) -> None:
        """Write text content to file.

        Args:
            path: File path to write
            content: Text content to write
            encoding: Text encoding (default: utf-8)

        Raises:
            IOError: If write fails
        """
        file_path = Path(path) if Path(path).is_absolute() else self.base_dir / path

        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None, lambda: file_path.write_text(content, encoding=encoding)
            )
        except Exception as e:
            raise IOError(f"Failed to write file: {str(e)}")

    async def write_json(self, path: str, data: dict) -> None:
        """Write JSON data to file.

        Args:
            path: File path to write
            data: Dictionary to serialize as JSON

        Raises:
            IOError: If write fails
        """
        json_content = json.dumps(data, indent=2)
        await self.write_text(path, json_content)

    async def read_json(self, path: str) -> dict:
        """Read JSON data from file.

        Args:
            path: File path to read

        Returns:
            Parsed JSON as dictionary

        Raises:
            IOError: If read fails
            json.JSONDecodeError: If JSON is invalid
        """
        content = await self.read_text(path)
        return json.loads(content)

    # Directory operations
    async def list_files(self, path: str, pattern: str = "*") -> List[str]:
        """List files in directory.

        Args:
            path: Directory path
            pattern: Glob pattern for filtering

        Returns:
            List of file paths
        """
        dir_path = Path(path) if Path(path).is_absolute() else self.base_dir / path

        if not dir_path.exists():
            return []

        return [
            str(p.relative_to(dir_path)) for p in dir_path.glob(pattern) if p.is_file()
        ]

    async def create_directory(self, path: str) -> None:
        """Create directory if it doesn't exist.

        Args:
            path: Directory path to create
        """
        dir_path = Path(path) if Path(path).is_absolute() else self.base_dir / path
        dir_path.mkdir(parents=True, exist_ok=True)


class MemoryFilesystem:
    """In-memory filesystem for testing.

    Implements the same interface as FilesystemAdapter but stores in memory.
    """

    def __init__(self):
        """Initialize in-memory storage."""
        self.files: Dict[str, bytes] = {}
        self.text_files: Dict[str, str] = {}

    async def read_binary(self, path: str) -> bytes:
        """Read from memory."""
        if path not in self.files:
            raise IOError(f"File not found: {path}")
        return self.files[path]

    async def write_binary(self, path: str, data: bytes) -> None:
        """Write to memory."""
        self.files[path] = data

    async def read_text(self, path: str, encoding: str = "utf-8") -> str:
        """Read text from memory."""
        if path not in self.text_files:
            raise IOError(f"File not found: {path}")
        return self.text_files[path]

    async def write_text(
        self, path: str, content: str, encoding: str = "utf-8"
    ) -> None:
        """Write text to memory."""
        self.text_files[path] = content

    async def file_exists(self, path: str) -> bool:
        """Check if file exists in memory."""
        return path in self.files or path in self.text_files

    async def write_json(self, path: str, data: dict) -> None:
        """Write JSON to memory."""
        self.text_files[path] = json.dumps(data, indent=2)

    async def read_json(self, path: str) -> dict:
        """Read JSON from memory."""
        if path not in self.text_files:
            raise IOError(f"File not found: {path}")
        return json.loads(self.text_files[path])

    async def list_files(self, path: str, pattern: str = "*") -> List[str]:
        """List files in memory matching pattern."""
        from fnmatch import fnmatch

        all_files = list(self.files.keys()) + list(self.text_files.keys())
        path_prefix = path if path.endswith("/") else path + "/"

        matching = []
        for file_path in all_files:
            if file_path.startswith(path_prefix):
                rel_path = file_path[len(path_prefix) :]
                if fnmatch(rel_path, pattern):
                    matching.append(rel_path)

        return matching

    async def create_directory(self, path: str) -> None:
        """No-op for in-memory filesystem."""
        pass
