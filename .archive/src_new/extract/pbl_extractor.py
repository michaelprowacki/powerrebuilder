"""PBL Extractor - Advanced PowerBuilder Library extraction.

This module provides more advanced extraction capabilities including:
- Corruption recovery
- Resource extraction (images, etc.)
- P-code detection and extraction
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

from src_new._core import ExtractedObject, ObjectType
from src_new._patterns import BinaryReader

logger = logging.getLogger(__name__)


@dataclass
class RecoveryResult:
    """Result from recovery attempt."""

    success: bool
    recovered_data: Optional[bytes] = None
    error: Optional[str] = None
    partial: bool = False


class AdvancedPBLExtractor:
    """Advanced PBL/PBD extractor with recovery capabilities."""

    def __init__(self, enable_recovery: bool = True):
        """Initialize advanced extractor.

        Args:
            enable_recovery: Enable corruption recovery
        """
        self.enable_recovery = enable_recovery
        self.extracted_objects = []

    def extract_with_recovery(
        self, file_path: Path, output_dir: Path
    ) -> List[ExtractedObject]:
        """Extract with corruption recovery.

        Args:
            file_path: PBL/PBD file path
            output_dir: Output directory

        Returns:
            List of extracted objects
        """
        self.extracted_objects = []

        try:
            # Try normal extraction first
            from .extractor import PBLParser

            parser = PBLParser(file_path)
            pbl_file = parser.parse()

            for entry in pbl_file.entries:
                try:
                    data = parser.extract_data(entry)
                    self.extracted_objects.append(
                        ExtractedObject(
                            name=entry.name,
                            type=entry.type,
                            data=data,
                            source_file=str(file_path),
                        )
                    )
                except Exception as e:
                    logger.warning(f"Failed to extract {entry.name}: {e}")
                    if self.enable_recovery:
                        self._attempt_recovery(file_path, entry)

        except Exception as e:
            logger.error(f"Normal extraction failed: {e}")
            if self.enable_recovery:
                self._deep_recovery(file_path, output_dir)

        return self.extracted_objects

    def _attempt_recovery(self, file_path: Path, entry) -> None:
        """Attempt to recover a specific entry.

        Args:
            file_path: PBL file path
            entry: Entry to recover
        """
        with BinaryReader(file_path) as reader:
            # Try direct offset read
            if entry.offset > 0 and entry.size > 0:
                try:
                    reader.seek(entry.offset)
                    data = reader.read(entry.size)

                    # Validate recovered data
                    if self._validate_recovered_data(data, entry.type):
                        self.extracted_objects.append(
                            ExtractedObject(
                                name=entry.name,
                                type=entry.type,
                                data=data,
                                source_file=str(file_path),
                                metadata={"recovered": True},
                            )
                        )
                        logger.info(f"Recovered: {entry.name}")
                except Exception as e:
                    logger.debug(f"Recovery failed for {entry.name}: {e}")

    def _deep_recovery(self, file_path: Path, output_dir: Path) -> None:
        """Perform deep recovery scanning entire file.

        Args:
            file_path: PBL file path
            output_dir: Output directory
        """
        logger.info("Starting deep recovery scan")

        with BinaryReader(file_path) as reader:
            data = reader.read(reader.size)

            # Scan for known signatures
            objects_found = 0

            # Look for P-code functions
            for match in self._find_pcode_functions(data):
                objects_found += 1
                self.extracted_objects.append(
                    ExtractedObject(
                        name=f"recovered_function_{objects_found}.fun",
                        type=ObjectType.FUNCTION,
                        data=match,
                        source_file=str(file_path),
                        metadata={"recovered": True, "deep_scan": True},
                    )
                )

            # Look for source code patterns
            for match in self._find_source_code(data):
                objects_found += 1
                obj_type = self._detect_source_type(match)
                self.extracted_objects.append(
                    ExtractedObject(
                        name=f"recovered_{obj_type.value}_{objects_found}",
                        type=obj_type,
                        data=match,
                        source_file=str(file_path),
                        metadata={"recovered": True, "deep_scan": True},
                    )
                )

            logger.info(f"Deep recovery found {objects_found} objects")

    def _find_pcode_functions(self, data: bytes) -> List[bytes]:
        """Find P-code function blocks in data.

        Args:
            data: Binary data to scan

        Returns:
            List of P-code function data blocks
        """
        functions = []

        # P-code function signatures (simplified)
        # Real implementation would use more sophisticated patterns
        pcode_signatures = [
            b"\x50\x43\x4f\x44",  # "PCOD"
            b"\x46\x55\x4e\x43",  # "FUNC"
        ]

        for sig in pcode_signatures:
            offset = 0
            while True:
                idx = data.find(sig, offset)
                if idx == -1:
                    break

                # Try to extract function block
                # Simplified - real implementation would parse structure
                block_size = min(4096, len(data) - idx)
                functions.append(data[idx : idx + block_size])
                offset = idx + 1

        return functions

    def _find_source_code(self, data: bytes) -> List[bytes]:
        """Find source code blocks in data.

        Args:
            data: Binary data to scan

        Returns:
            List of source code blocks
        """
        source_blocks = []

        # Look for PowerBuilder source patterns
        patterns = [
            b"forward\r\n",
            b"global type",
            b"type variables",
            b"end type",
            b"public function",
            b"private function",
            b"event type",
        ]

        # Find potential source code regions
        for pattern in patterns:
            offset = 0
            while True:
                idx = data.find(pattern, offset)
                if idx == -1:
                    break

                # Extract surrounding context
                start = max(0, idx - 100)
                end = min(len(data), idx + 10000)

                # Try to find complete source block
                block = self._extract_source_block(data[start:end])
                if block and len(block) > 100:
                    source_blocks.append(block)

                offset = idx + 1

        return source_blocks

    def _extract_source_block(self, data: bytes) -> Optional[bytes]:
        """Extract a complete source code block.

        Args:
            data: Data containing potential source

        Returns:
            Extracted source block or None
        """
        try:
            # Try to decode as text
            text = data.decode("utf-8", errors="ignore")

            # Find block boundaries
            # Simplified - real implementation would parse properly
            lines = text.split("\n")

            # Look for start/end markers
            start_idx = 0
            end_idx = len(lines)

            # Find actual code boundaries
            for i, line in enumerate(lines):
                if any(
                    marker in line.lower()
                    for marker in ["forward", "global type", "public:"]
                ):
                    start_idx = i
                    break

            for i in range(len(lines) - 1, start_idx, -1):
                if "end " in lines[i].lower() or lines[i].strip() == "":
                    end_idx = i + 1
                    break

            if end_idx > start_idx + 5:  # Minimum viable block
                result = "\n".join(lines[start_idx:end_idx])
                return result.encode("utf-8")

        except Exception:
            pass

        return None

    def _detect_source_type(self, data: bytes) -> ObjectType:
        """Detect the type of PowerBuilder source code.

        Args:
            data: Source code data

        Returns:
            Detected object type
        """
        try:
            text = data.decode("utf-8", errors="ignore").lower()

            # Check for type indicators
            if "window type" in text or "from w_" in text:
                return ObjectType.WINDOW
            elif "menu type" in text or "from m_" in text:
                return ObjectType.MENU
            elif "datawindow" in text or "dataobject" in text:
                return ObjectType.DATAWINDOW
            elif "application object" in text:
                return ObjectType.APPLICATION
            elif "function " in text and "return" in text:
                return ObjectType.FUNCTION
            elif "structure" in text:
                return ObjectType.STRUCTURE
            elif "query" in text or "select " in text:
                return ObjectType.QUERY
            else:
                return ObjectType.USER_OBJECT

        except:
            return ObjectType.USER_OBJECT

    def _validate_recovered_data(self, data: bytes, expected_type: ObjectType) -> bool:
        """Validate recovered data.

        Args:
            data: Recovered data
            expected_type: Expected object type

        Returns:
            True if data appears valid
        """
        if not data or len(data) < 10:
            return False

        # Check for reasonable size
        if len(data) > 10 * 1024 * 1024:  # 10MB max
            return False

        # Type-specific validation
        if expected_type == ObjectType.FUNCTION:
            # P-code should have certain patterns
            return b"\x00" in data and len(data) > 100

        else:
            # Source code should be mostly text
            try:
                text = data.decode("utf-8", errors="strict")
                return len(text) > 10
            except:
                return False


class ResourceExtractor:
    """Extract embedded resources from PBL files."""

    def extract_resources(self, file_path: Path) -> Dict[str, List[bytes]]:
        """Extract embedded resources like images.

        Args:
            file_path: PBL file path

        Returns:
            Dict of resource type to list of resources
        """
        resources = {
            "images": [],
            "icons": [],
            "sounds": [],
            "other": [],
        }

        with BinaryReader(file_path) as reader:
            data = reader.read(reader.size)

            # Find BMP images
            for bmp in self._find_bitmaps(data):
                resources["images"].append(bmp)

            # Find ICO icons
            for ico in self._find_icons(data):
                resources["icons"].append(ico)

            # Find WAV sounds
            for wav in self._find_sounds(data):
                resources["sounds"].append(wav)

        return resources

    def _find_bitmaps(self, data: bytes) -> List[bytes]:
        """Find embedded bitmap images.

        Args:
            data: Binary data

        Returns:
            List of bitmap data blocks
        """
        bitmaps = []
        bmp_sig = b"BM"  # Bitmap signature

        offset = 0
        while True:
            idx = data.find(bmp_sig, offset)
            if idx == -1:
                break

            # Read BMP header to get size
            if idx + 14 <= len(data):
                size = int.from_bytes(data[idx + 2 : idx + 6], "little")
                if 54 <= size <= 10 * 1024 * 1024:  # Reasonable size
                    bmp_data = data[idx : idx + size]
                    if self._validate_bitmap(bmp_data):
                        bitmaps.append(bmp_data)

            offset = idx + 1

        return bitmaps

    def _find_icons(self, data: bytes) -> List[bytes]:
        """Find embedded icon files.

        Args:
            data: Binary data

        Returns:
            List of icon data blocks
        """
        icons = []
        ico_sig = b"\x00\x00\x01\x00"  # ICO signature

        offset = 0
        while True:
            idx = data.find(ico_sig, offset)
            if idx == -1:
                break

            # Simple extraction - real implementation would parse ICO structure
            if idx + 22 <= len(data):
                # Read basic header
                icon_count = int.from_bytes(data[idx + 4 : idx + 6], "little")
                if 1 <= icon_count <= 20:  # Reasonable icon count
                    # Estimate size (simplified)
                    size = 22 + (icon_count * 16) + 1024
                    size = min(size, len(data) - idx)
                    icons.append(data[idx : idx + size])

            offset = idx + 1

        return icons

    def _find_sounds(self, data: bytes) -> List[bytes]:
        """Find embedded sound files.

        Args:
            data: Binary data

        Returns:
            List of sound data blocks
        """
        sounds = []
        wav_sig = b"RIFF"  # WAV file signature

        offset = 0
        while True:
            idx = data.find(wav_sig, offset)
            if idx == -1:
                break

            # Check for WAVE format
            if idx + 12 <= len(data) and data[idx + 8 : idx + 12] == b"WAVE":
                # Read size from RIFF header
                size = int.from_bytes(data[idx + 4 : idx + 8], "little") + 8
                if size <= 50 * 1024 * 1024:  # Max 50MB
                    wav_data = data[idx : idx + size]
                    sounds.append(wav_data)

            offset = idx + 1

        return sounds

    def _validate_bitmap(self, data: bytes) -> bool:
        """Validate bitmap data.

        Args:
            data: Potential bitmap data

        Returns:
            True if valid bitmap
        """
        if len(data) < 54:  # Minimum BMP header size
            return False

        # Check signature
        if data[:2] != b"BM":
            return False

        # Check file size matches header
        file_size = int.from_bytes(data[2:6], "little")
        if file_size != len(data):
            return False

        return True
