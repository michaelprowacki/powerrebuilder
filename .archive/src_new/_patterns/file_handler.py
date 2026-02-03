"""File Handler Pattern - Unified file operations.

Consolidates all file I/O operations found throughout the codebase into
a single, consistent interface.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any, Iterator, List, Union

PathLike = Union[str, Path]


class FileHandler:
    """Unified file operations handler.

    Replaces scattered file operations found in:
    - Multiple coordinator implementations
    - Various utility modules
    - Infrastructure components
    """

    def __init__(self, encoding: str = "utf-8"):
        """Initialize file handler.

        Args:
            encoding: Default text encoding
        """
        self.encoding = encoding

    # ============================================================================
    # PATH OPERATIONS
    # ============================================================================

    def ensure_dir(self, path: PathLike) -> Path:
        """Ensure directory exists, creating if needed.

        Args:
            path: Directory path

        Returns:
            Path object
        """
        path_obj = Path(path)
        path_obj.mkdir(parents=True, exist_ok=True)
        return path_obj

    def clean_dir(self, path: PathLike, recreate: bool = True) -> Path:
        """Clean directory contents.

        Args:
            path: Directory path
            recreate: Whether to recreate after cleaning

        Returns:
            Path object
        """
        path_obj = Path(path)
        if path_obj.exists():
            shutil.rmtree(path_obj)
        if recreate:
            path_obj.mkdir(parents=True, exist_ok=True)
        return path_obj

    def copy_file(self, src: PathLike, dest: PathLike, overwrite: bool = True) -> Path:
        """Copy file with optional overwrite.

        Args:
            src: Source file path
            dest: Destination path
            overwrite: Whether to overwrite existing

        Returns:
            Destination path
        """
        src_path = Path(src)
        dest_path = Path(dest)

        if not src_path.exists():
            raise FileNotFoundError(f"Source not found: {src_path}")

        if dest_path.exists() and not overwrite:
            raise FileExistsError(f"Destination exists: {dest_path}")

        # Ensure parent directory exists
        dest_path.parent.mkdir(parents=True, exist_ok=True)

        shutil.copy2(src_path, dest_path)
        return dest_path

    def move_file(self, src: PathLike, dest: PathLike, overwrite: bool = True) -> Path:
        """Move file with optional overwrite.

        Args:
            src: Source file path
            dest: Destination path
            overwrite: Whether to overwrite existing

        Returns:
            Destination path
        """
        src_path = Path(src)
        dest_path = Path(dest)

        if not src_path.exists():
            raise FileNotFoundError(f"Source not found: {src_path}")

        if dest_path.exists() and not overwrite:
            raise FileExistsError(f"Destination exists: {dest_path}")

        # Ensure parent directory exists
        dest_path.parent.mkdir(parents=True, exist_ok=True)

        shutil.move(str(src_path), str(dest_path))
        return dest_path

    # ============================================================================
    # FILE DISCOVERY
    # ============================================================================

    def find_files(
        self, root: PathLike, pattern: str = "*", recursive: bool = True
    ) -> List[Path]:
        """Find files matching pattern.

        Args:
            root: Root directory
            pattern: Glob pattern
            recursive: Search recursively

        Returns:
            List of matching file paths
        """
        root_path = Path(root)
        if not root_path.exists():
            return []

        if recursive:
            return list(root_path.rglob(pattern))
        else:
            return list(root_path.glob(pattern))

    def iter_files(
        self, root: PathLike, pattern: str = "*", recursive: bool = True
    ) -> Iterator[Path]:
        """Iterate over files matching pattern.

        Args:
            root: Root directory
            pattern: Glob pattern
            recursive: Search recursively

        Yields:
            Matching file paths
        """
        root_path = Path(root)
        if not root_path.exists():
            return

        if recursive:
            yield from root_path.rglob(pattern)
        else:
            yield from root_path.glob(pattern)

    # ============================================================================
    # TEXT FILE OPERATIONS
    # ============================================================================

    def read_text(self, path: PathLike) -> str:
        """Read text file.

        Args:
            path: File path

        Returns:
            File contents
        """
        return Path(path).read_text(encoding=self.encoding)

    def write_text(
        self, path: PathLike, content: str, create_dirs: bool = True
    ) -> Path:
        """Write text file.

        Args:
            path: File path
            content: Text content
            create_dirs: Create parent directories

        Returns:
            Path object
        """
        path_obj = Path(path)
        if create_dirs:
            path_obj.parent.mkdir(parents=True, exist_ok=True)
        path_obj.write_text(content, encoding=self.encoding)
        return path_obj

    def append_text(
        self, path: PathLike, content: str, create_dirs: bool = True
    ) -> Path:
        """Append to text file.

        Args:
            path: File path
            content: Text to append
            create_dirs: Create parent directories

        Returns:
            Path object
        """
        path_obj = Path(path)
        if create_dirs:
            path_obj.parent.mkdir(parents=True, exist_ok=True)

        with open(path_obj, "a", encoding=self.encoding) as f:
            f.write(content)

        return path_obj

    def read_lines(self, path: PathLike) -> List[str]:
        """Read file as lines.

        Args:
            path: File path

        Returns:
            List of lines
        """
        return Path(path).read_text(encoding=self.encoding).splitlines()

    def write_lines(
        self, path: PathLike, lines: List[str], create_dirs: bool = True
    ) -> Path:
        """Write lines to file.

        Args:
            path: File path
            lines: Lines to write
            create_dirs: Create parent directories

        Returns:
            Path object
        """
        content = "\n".join(lines)
        return self.write_text(path, content, create_dirs)

    # ============================================================================
    # BINARY FILE OPERATIONS
    # ============================================================================

    def read_binary(self, path: PathLike) -> bytes:
        """Read binary file.

        Args:
            path: File path

        Returns:
            File contents as bytes
        """
        return Path(path).read_bytes()

    def write_binary(
        self, path: PathLike, content: bytes, create_dirs: bool = True
    ) -> Path:
        """Write binary file.

        Args:
            path: File path
            content: Binary content
            create_dirs: Create parent directories

        Returns:
            Path object
        """
        path_obj = Path(path)
        if create_dirs:
            path_obj.parent.mkdir(parents=True, exist_ok=True)
        path_obj.write_bytes(content)
        return path_obj

    # ============================================================================
    # JSON OPERATIONS
    # ============================================================================

    def read_json(self, path: PathLike) -> Any:
        """Read JSON file.

        Args:
            path: File path

        Returns:
            Parsed JSON data
        """
        text = self.read_text(path)
        return json.loads(text)

    def write_json(
        self, path: PathLike, data: Any, indent: int = 2, create_dirs: bool = True
    ) -> Path:
        """Write JSON file.

        Args:
            path: File path
            data: Data to serialize
            indent: Indentation level
            create_dirs: Create parent directories

        Returns:
            Path object
        """
        text = json.dumps(data, indent=indent, ensure_ascii=False)
        return self.write_text(path, text, create_dirs)

    # ============================================================================
    # FILE INFORMATION
    # ============================================================================

    def get_size(self, path: PathLike) -> int:
        """Get file size in bytes.

        Args:
            path: File path

        Returns:
            Size in bytes
        """
        return Path(path).stat().st_size

    def exists(self, path: PathLike) -> bool:
        """Check if path exists.

        Args:
            path: File or directory path

        Returns:
            True if exists
        """
        return Path(path).exists()

    def is_file(self, path: PathLike) -> bool:
        """Check if path is a file.

        Args:
            path: Path to check

        Returns:
            True if file
        """
        path_obj = Path(path)
        return path_obj.exists() and path_obj.is_file()

    def is_dir(self, path: PathLike) -> bool:
        """Check if path is a directory.

        Args:
            path: Path to check

        Returns:
            True if directory
        """
        path_obj = Path(path)
        return path_obj.exists() and path_obj.is_dir()

    def get_extension(self, path: PathLike) -> str:
        """Get file extension.

        Args:
            path: File path

        Returns:
            Extension with dot (e.g., '.txt')
        """
        return Path(path).suffix

    def get_stem(self, path: PathLike) -> str:
        """Get filename without extension.

        Args:
            path: File path

        Returns:
            Filename stem
        """
        return Path(path).stem
