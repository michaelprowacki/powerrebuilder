"""Binary Analysis Tools - Advanced binary file analysis utilities.

This module provides tools for analyzing PowerBuilder binary formats,
including structure detection, corruption recovery, and format identification.
"""

import hashlib
import logging
import struct
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from src_new._patterns import BinaryReader

logger = logging.getLogger(__name__)


class BinaryFormat(Enum):
    """Binary file formats."""

    PBL = "PowerBuilder Library"
    PBD = "PowerBuilder Dynamic Library"
    PBR = "PowerBuilder Resource"
    FUN = "P-code Function"
    UNKNOWN = "Unknown"


@dataclass
class BinaryAnalysis:
    """Binary file analysis results."""

    format: BinaryFormat
    version: Optional[str]
    size: int
    checksum: str
    entropy: float
    structure: Dict[str, Any]
    corruption: Optional[List[str]]
    metadata: Dict[str, Any]


class BinaryAnalyzer:
    """Binary file analyzer."""

    # Magic bytes for format detection
    MAGIC_BYTES = {
        b"PBL\x00": BinaryFormat.PBL,
        b"PBD\x00": BinaryFormat.PBD,
        b"PBR\x00": BinaryFormat.PBR,
        b"\x46\x55\x4e": BinaryFormat.FUN,  # FUN
    }

    def analyze(self, file_path: Path) -> BinaryAnalysis:
        """Analyze binary file.

        Args:
            file_path: File to analyze

        Returns:
            Analysis results
        """
        with BinaryReader(file_path) as reader:
            # Detect format
            format_type = self._detect_format(reader)

            # Get version
            version = self._detect_version(reader, format_type)

            # Calculate checksum
            reader.seek(0)
            data = reader.read()
            checksum = hashlib.sha256(data).hexdigest()

            # Calculate entropy
            entropy = self._calculate_entropy(data)

            # Analyze structure
            reader.seek(0)
            structure = self._analyze_structure(reader, format_type)

            # Check for corruption
            reader.seek(0)
            corruption = self._check_corruption(reader, format_type)

            # Extract metadata
            reader.seek(0)
            metadata = self._extract_metadata(reader, format_type)

            return BinaryAnalysis(
                format=format_type,
                version=version,
                size=reader.size,
                checksum=checksum,
                entropy=entropy,
                structure=structure,
                corruption=corruption,
                metadata=metadata,
            )

    def _detect_format(self, reader: BinaryReader) -> BinaryFormat:
        """Detect binary format.

        Args:
            reader: Binary reader

        Returns:
            Detected format
        """
        reader.seek(0)
        header = reader.read(4)

        for magic, format_type in self.MAGIC_BYTES.items():
            if header.startswith(magic):
                return format_type

        # Check for P-code patterns
        reader.seek(0)
        data = reader.read(min(256, reader.size))

        if self._has_pcode_patterns(data):
            return BinaryFormat.FUN

        return BinaryFormat.UNKNOWN

    def _detect_version(
        self, reader: BinaryReader, format_type: BinaryFormat
    ) -> Optional[str]:
        """Detect file version.

        Args:
            reader: Binary reader
            format_type: File format

        Returns:
            Version string if detected
        """
        if format_type in [BinaryFormat.PBL, BinaryFormat.PBD]:
            reader.seek(4)
            version_bytes = reader.read(4)
            if len(version_bytes) == 4:
                major, minor = struct.unpack("<HH", version_bytes)
                return f"{major}.{minor}"

        elif format_type == BinaryFormat.FUN:
            reader.seek(0)
            data = reader.read(min(64, reader.size))

            # Check for version markers
            if b"\x06\x00" in data:
                return "6.0"
            elif b"\x08\x00" in data:
                return "8.0"
            elif b"\x0a\x00" in data:
                return "10.0"
            elif b"\x0c\x05" in data:
                return "12.5"

        return None

    def _calculate_entropy(self, data: bytes) -> float:
        """Calculate Shannon entropy.

        Args:
            data: Data to analyze

        Returns:
            Entropy value (0-8)
        """
        if not data:
            return 0.0

        # Count byte frequencies
        frequencies = {}
        for byte in data:
            frequencies[byte] = frequencies.get(byte, 0) + 1

        # Calculate entropy
        import math

        entropy = 0.0
        data_len = len(data)

        for count in frequencies.values():
            if count > 0:
                probability = count / data_len
                entropy -= probability * math.log2(probability)

        return entropy

    def _analyze_structure(
        self, reader: BinaryReader, format_type: BinaryFormat
    ) -> Dict[str, Any]:
        """Analyze file structure.

        Args:
            reader: Binary reader
            format_type: File format

        Returns:
            Structure information
        """
        structure = {}

        if format_type in [BinaryFormat.PBL, BinaryFormat.PBD]:
            structure = self._analyze_pbl_structure(reader)
        elif format_type == BinaryFormat.FUN:
            structure = self._analyze_pcode_structure(reader)

        return structure

    def _analyze_pbl_structure(self, reader: BinaryReader) -> Dict[str, Any]:
        """Analyze PBL/PBD structure.

        Args:
            reader: Binary reader

        Returns:
            PBL structure
        """
        structure = {
            "header_size": 0,
            "entry_table_offset": 0,
            "entry_count": 0,
            "data_offset": 0,
        }

        try:
            # Read header
            reader.seek(0)
            header = reader.read(32)

            if len(header) >= 32:
                # Parse header fields
                structure["header_size"] = 32
                structure["entry_table_offset"] = struct.unpack("<I", header[8:12])[0]
                structure["entry_count"] = struct.unpack("<I", header[12:16])[0]
                structure["data_offset"] = struct.unpack("<I", header[16:20])[0]

        except Exception as e:
            logger.debug(f"Failed to analyze PBL structure: {e}")

        return structure

    def _analyze_pcode_structure(self, reader: BinaryReader) -> Dict[str, Any]:
        """Analyze P-code structure.

        Args:
            reader: Binary reader

        Returns:
            P-code structure
        """
        structure = {
            "function_count": 0,
            "string_table_offset": 0,
            "code_section_offset": 0,
            "data_section_offset": 0,
        }

        try:
            reader.seek(0)
            data = reader.read(min(1024, reader.size))

            # Look for section markers
            if b"\x00\x00\x00\x00" in data:
                structure["function_count"] = data[:256].count(b"\x00\x00\x00\x00")

            # Find string table
            string_marker = b"\x00" * 8
            if string_marker in data:
                structure["string_table_offset"] = data.find(string_marker)

        except Exception as e:
            logger.debug(f"Failed to analyze P-code structure: {e}")

        return structure

    def _check_corruption(
        self, reader: BinaryReader, format_type: BinaryFormat
    ) -> Optional[List[str]]:
        """Check for file corruption.

        Args:
            reader: Binary reader
            format_type: File format

        Returns:
            List of corruption indicators
        """
        issues = []

        # Check file size
        if reader.size == 0:
            issues.append("Empty file")
        elif reader.size < 16:
            issues.append("File too small")

        # Check header
        reader.seek(0)
        header = reader.read(min(32, reader.size))

        if format_type != BinaryFormat.UNKNOWN:
            # Check for null bytes in header
            if header == b"\x00" * len(header):
                issues.append("Null header")

            # Check entropy
            entropy = self._calculate_entropy(header)
            if entropy < 1.0:
                issues.append("Low header entropy")

        # Check for truncation
        if format_type in [BinaryFormat.PBL, BinaryFormat.PBD]:
            try:
                reader.seek(8)
                table_offset = struct.unpack("<I", reader.read(4))[0]
                if table_offset > reader.size:
                    issues.append("Truncated file")
            except:
                issues.append("Invalid structure")

        return issues if issues else None

    def _extract_metadata(
        self, reader: BinaryReader, format_type: BinaryFormat
    ) -> Dict[str, Any]:
        """Extract file metadata.

        Args:
            reader: Binary reader
            format_type: File format

        Returns:
            Metadata dictionary
        """
        metadata = {
            "format": format_type.value,
            "size_kb": reader.size / 1024,
        }

        if format_type in [BinaryFormat.PBL, BinaryFormat.PBD]:
            # Extract library metadata
            reader.seek(0)
            data = reader.read(min(4096, reader.size))

            # Look for timestamp
            if b"\x20\x20" in data:
                pos = data.find(b"\x20\x20")
                if pos > 0:
                    timestamp_bytes = data[pos - 8 : pos]
                    try:
                        timestamp = struct.unpack("<Q", timestamp_bytes)[0]
                        metadata["timestamp"] = timestamp
                    except:
                        pass

        return metadata

    def _has_pcode_patterns(self, data: bytes) -> bool:
        """Check for P-code patterns.

        Args:
            data: Data to check

        Returns:
            True if P-code patterns found
        """
        # Check for common P-code opcodes
        pcode_opcodes = [0x00, 0x02, 0x03, 0x10, 0x11, 0x20, 0x21]
        opcode_count = sum(1 for b in data if b in pcode_opcodes)

        return opcode_count > len(data) * 0.2


class CorruptionRecovery:
    """Binary corruption recovery engine."""

    def recover(self, file_path: Path, output_path: Path) -> bool:
        """Attempt to recover corrupted file.

        Args:
            file_path: Corrupted file
            output_path: Output path for recovered file

        Returns:
            True if recovery successful
        """
        analyzer = BinaryAnalyzer()
        analysis = analyzer.analyze(file_path)

        if not analysis.corruption:
            # No corruption detected
            import shutil

            shutil.copy2(file_path, output_path)
            return True

        logger.info(f"Attempting recovery for {file_path}")
        logger.info(f"Issues: {analysis.corruption}")

        with BinaryReader(file_path) as reader:
            if "Truncated file" in analysis.corruption:
                return self._recover_truncated(reader, output_path, analysis)
            elif "Null header" in analysis.corruption:
                return self._recover_null_header(reader, output_path, analysis)
            elif "Invalid structure" in analysis.corruption:
                return self._recover_structure(reader, output_path, analysis)
            else:
                # Generic recovery
                return self._generic_recovery(reader, output_path)

    def _recover_truncated(
        self, reader: BinaryReader, output_path: Path, analysis: BinaryAnalysis
    ) -> bool:
        """Recover truncated file.

        Args:
            reader: Binary reader
            output_path: Output path
            analysis: File analysis

        Returns:
            True if successful
        """
        try:
            reader.seek(0)
            data = reader.read()

            # Pad to expected size
            if analysis.format in [BinaryFormat.PBL, BinaryFormat.PBD]:
                # Find expected size from header
                if len(data) >= 20:
                    expected_size = struct.unpack("<I", data[16:20])[0]
                    if expected_size > len(data):
                        # Pad with zeros
                        data += b"\x00" * (expected_size - len(data))

            # Write recovered file
            with open(output_path, "wb") as f:
                f.write(data)

            return True

        except Exception as e:
            logger.error(f"Truncation recovery failed: {e}")
            return False

    def _recover_null_header(
        self, reader: BinaryReader, output_path: Path, analysis: BinaryAnalysis
    ) -> bool:
        """Recover file with null header.

        Args:
            reader: Binary reader
            output_path: Output path
            analysis: File analysis

        Returns:
            True if successful
        """
        try:
            reader.seek(0)
            data = reader.read()

            # Skip null bytes at start
            start = 0
            for i, byte in enumerate(data):
                if byte != 0:
                    start = i
                    break

            if start > 0:
                data = data[start:]

            # Write recovered file
            with open(output_path, "wb") as f:
                f.write(data)

            return True

        except Exception as e:
            logger.error(f"Null header recovery failed: {e}")
            return False

    def _recover_structure(
        self, reader: BinaryReader, output_path: Path, analysis: BinaryAnalysis
    ) -> bool:
        """Recover file structure.

        Args:
            reader: Binary reader
            output_path: Output path
            analysis: File analysis

        Returns:
            True if successful
        """
        try:
            reader.seek(0)
            data = reader.read()

            # Rebuild header for known formats
            if analysis.format == BinaryFormat.PBL:
                # Create minimal PBL header
                header = b"PBL\x00"
                header += struct.pack("<I", 0x0600)  # Version 6.0
                header += struct.pack("<I", 32)  # Entry table offset
                header += struct.pack("<I", 0)  # Entry count
                header += struct.pack("<I", len(data))  # Data offset
                header += b"\x00" * (32 - len(header))  # Padding

                data = header + data[32:] if len(data) > 32 else header

            # Write recovered file
            with open(output_path, "wb") as f:
                f.write(data)

            return True

        except Exception as e:
            logger.error(f"Structure recovery failed: {e}")
            return False

    def _generic_recovery(self, reader: BinaryReader, output_path: Path) -> bool:
        """Generic recovery attempt.

        Args:
            reader: Binary reader
            output_path: Output path

        Returns:
            True if successful
        """
        try:
            reader.seek(0)
            data = reader.read()

            # Remove trailing nulls
            while data and data[-1] == 0:
                data = data[:-1]

            # Write recovered file
            with open(output_path, "wb") as f:
                f.write(data)

            return True

        except Exception as e:
            logger.error(f"Generic recovery failed: {e}")
            return False


def analyze_directory(directory: Path) -> Dict[Path, BinaryAnalysis]:
    """Analyze all binary files in directory.

    Args:
        directory: Directory to analyze

    Returns:
        Analysis results by file
    """
    analyzer = BinaryAnalyzer()
    results = {}

    for file_path in directory.rglob("*"):
        if file_path.is_file():
            try:
                analysis = analyzer.analyze(file_path)
                if analysis.format != BinaryFormat.UNKNOWN:
                    results[file_path] = analysis
            except Exception as e:
                logger.debug(f"Failed to analyze {file_path}: {e}")

    return results
