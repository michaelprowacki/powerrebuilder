"""Binary Reader Pattern - Unified binary file operations.

This consolidates ALL binary reading/parsing operations found across:
- Extract stage (PBL/PBD parsing)
- Decompile stage (P-code reading)
- Multiple "binary_ops" implementations

Single source of truth for binary operations.
"""

from __future__ import annotations

import mmap
import struct
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple, Union

PathLike = Union[str, Path]


@dataclass
class BinaryHeader:
    """Common binary file header structure."""

    signature: bytes
    version: int
    size: int
    checksum: Optional[int] = None
    metadata: dict = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class BinaryReader:
    """Unified binary file reader with all common operations.

    This replaces multiple implementations of binary reading found in:
    - src/core/unified_binary_ops.py
    - src/extract/binary_ops.py
    - src/decompile/pcode/decoder.py
    """

    def __init__(
        self,
        file_path: Optional[PathLike] = None,
        data: Optional[bytes] = None,
        use_mmap: bool = True,
        endian: str = "little",
    ):
        """Initialize reader with file or data.

        Args:
            file_path: Path to binary file
            data: Raw bytes to read from
            use_mmap: Use memory mapping for large files
            endian: Byte order ('little' or 'big')
        """
        self.file_path = Path(file_path) if file_path else None
        self._data = data
        self._mmap = None
        self._file = None
        self.use_mmap = use_mmap
        self.endian = "<" if endian == "little" else ">"
        self.offset = 0

        if self.file_path and not self._data:
            self._open_file()

    def _open_file(self) -> None:
        """Open file for reading."""
        if not self.file_path.exists():
            raise FileNotFoundError(f"File not found: {self.file_path}")

        self._file = open(self.file_path, "rb")

        if self.use_mmap and self.file_path.stat().st_size > 0:
            self._mmap = mmap.mmap(self._file.fileno(), 0, access=mmap.ACCESS_READ)
            self._data = self._mmap
        else:
            self._data = self._file.read()

    def close(self) -> None:
        """Close file and cleanup resources."""
        if self._mmap:
            self._mmap.close()
            self._mmap = None
        if self._file:
            self._file.close()
            self._file = None

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, *args):
        """Context manager exit."""
        self.close()

    @property
    def size(self) -> int:
        """Get total size of data."""
        return len(self._data) if self._data else 0

    @property
    def position(self) -> int:
        """Get current position in file."""
        return self.offset

    @property
    def remaining(self) -> int:
        """Get remaining bytes from current position."""
        return self.size - self.offset

    def seek(self, offset: int, whence: int = 0) -> None:
        """Seek to position.

        Args:
            offset: Byte offset
            whence: 0=start, 1=current, 2=end
        """
        if whence == 0:
            self.offset = offset
        elif whence == 1:
            self.offset += offset
        elif whence == 2:
            self.offset = self.size + offset
        else:
            raise ValueError(f"Invalid whence: {whence}")

        self.offset = max(0, min(self.offset, self.size))

    def read(self, size: int) -> bytes:
        """Read raw bytes."""
        if self.offset + size > self.size:
            size = self.remaining

        data = self._data[self.offset : self.offset + size]
        self.offset += size
        return data

    def read_at(self, offset: int, size: int) -> bytes:
        """Read bytes at specific offset without changing position."""
        if offset + size > self.size:
            size = self.size - offset
        return self._data[offset : offset + size]

    def peek(self, size: int) -> bytes:
        """Read bytes without advancing position."""
        return self.read_at(self.offset, size)

    # ============================================================================
    # STRUCTURED DATA READING
    # ============================================================================

    def read_struct(self, fmt: str) -> Tuple:
        """Read structured data.

        Args:
            fmt: Struct format string (without endian marker)

        Returns:
            Unpacked values as tuple
        """
        full_fmt = self.endian + fmt
        size = struct.calcsize(full_fmt)
        data = self.read(size)

        if len(data) < size:
            raise ValueError(f"Not enough data for format {fmt}")

        return struct.unpack(full_fmt, data)

    def read_uint8(self) -> int:
        """Read unsigned 8-bit integer."""
        return self.read_struct("B")[0]

    def read_uint16(self) -> int:
        """Read unsigned 16-bit integer."""
        return self.read_struct("H")[0]

    def read_uint32(self) -> int:
        """Read unsigned 32-bit integer."""
        return self.read_struct("I")[0]

    def read_uint64(self) -> int:
        """Read unsigned 64-bit integer."""
        return self.read_struct("Q")[0]

    def read_int8(self) -> int:
        """Read signed 8-bit integer."""
        return self.read_struct("b")[0]

    def read_int16(self) -> int:
        """Read signed 16-bit integer."""
        return self.read_struct("h")[0]

    def read_int32(self) -> int:
        """Read signed 32-bit integer."""
        return self.read_struct("i")[0]

    def read_int64(self) -> int:
        """Read signed 64-bit integer."""
        return self.read_struct("q")[0]

    def read_float(self) -> float:
        """Read 32-bit float."""
        return self.read_struct("f")[0]

    def read_double(self) -> float:
        """Read 64-bit double."""
        return self.read_struct("d")[0]

    # ============================================================================
    # STRING READING
    # ============================================================================

    def read_string(self, size: int, encoding: str = "utf-8") -> str:
        """Read fixed-size string."""
        data = self.read(size)
        # Remove null terminator if present
        null_idx = data.find(b"\x00")
        if null_idx >= 0:
            data = data[:null_idx]
        return data.decode(encoding, errors="replace")

    def read_cstring(self, encoding: str = "utf-8", max_size: int = 1024) -> str:
        """Read null-terminated C string."""
        chars = []
        for _ in range(max_size):
            char = self.read(1)
            if not char or char == b"\x00":
                break
            chars.append(char)
        return b"".join(chars).decode(encoding, errors="replace")

    def read_pascal_string(self, encoding: str = "utf-8") -> str:
        """Read Pascal-style string (length prefix)."""
        length = self.read_uint8()
        return self.read_string(length, encoding)

    def read_unicode_string(self, size: int) -> str:
        """Read UTF-16 LE string."""
        data = self.read(size * 2)
        return data.decode("utf-16-le", errors="replace").rstrip("\x00")

    # ============================================================================
    # SEARCH AND PATTERN MATCHING
    # ============================================================================

    def find(self, pattern: bytes, start: Optional[int] = None) -> int:
        """Find pattern in data.

        Returns:
            Offset of pattern or -1 if not found
        """
        start = start or self.offset
        idx = self._data.find(pattern, start)
        return idx

    def find_all(self, pattern: bytes) -> list[int]:
        """Find all occurrences of pattern.

        Returns:
            List of offsets where pattern occurs
        """
        offsets = []
        start = 0
        while True:
            idx = self.find(pattern, start)
            if idx == -1:
                break
            offsets.append(idx)
            start = idx + len(pattern)
        return offsets

    # ============================================================================
    # CHECKSUM AND VALIDATION
    # ============================================================================

    def calculate_checksum(
        self, algorithm: str = "crc32", start: int = 0, size: Optional[int] = None
    ) -> int:
        """Calculate checksum of data range.

        Args:
            algorithm: Checksum algorithm (crc32, sum32)
            start: Start offset
            size: Number of bytes (None for all remaining)

        Returns:
            Checksum value
        """
        if size is None:
            size = self.size - start

        data = self._data[start : start + size]

        if algorithm == "crc32":
            import zlib

            return zlib.crc32(data) & 0xFFFFFFFF
        elif algorithm == "sum32":
            # Simple 32-bit sum
            total = 0
            for i in range(0, len(data), 4):
                chunk = data[i : i + 4]
                if len(chunk) == 4:
                    total += struct.unpack("<I", chunk)[0]
            return total & 0xFFFFFFFF
        else:
            raise ValueError(f"Unknown algorithm: {algorithm}")

    def validate_signature(self, expected: bytes, offset: int = 0) -> bool:
        """Validate file signature at offset.

        Args:
            expected: Expected signature bytes
            offset: Offset to check at

        Returns:
            True if signature matches
        """
        actual = self.read_at(offset, len(expected))
        return actual == expected
