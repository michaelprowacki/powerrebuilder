"""Enhanced Recovery Engine - Advanced corruption recovery for PBL/PBD files.

This module provides sophisticated recovery mechanisms for corrupted
PowerBuilder library files, including partial extraction and reconstruction.
"""

import logging
import struct
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from src_new._core import ObjectType, PBLEntry
from src_new._patterns import BinaryReader
from ..utils.binary import BinaryAnalyzer, BinaryFormat, CorruptionRecovery

logger = logging.getLogger(__name__)


@dataclass
class RecoveryResult:
    """Recovery operation result."""

    success: bool
    recovered_entries: int
    total_entries: int
    errors: List[str]
    warnings: List[str]
    recovered_file: Optional[Path]


class EnhancedRecoveryEngine:
    """Enhanced recovery engine for PowerBuilder files."""

    def __init__(self, aggressive: bool = False):
        """Initialize recovery engine.

        Args:
            aggressive: Use aggressive recovery techniques
        """
        self.aggressive = aggressive
        self.analyzer = BinaryAnalyzer()
        self.basic_recovery = CorruptionRecovery()

    def recover(self, file_path: Path, output_dir: Path) -> RecoveryResult:
        """Recover corrupted PBL/PBD file.

        Args:
            file_path: Corrupted file path
            output_dir: Output directory for recovered content

        Returns:
            Recovery result
        """
        output_dir.mkdir(parents=True, exist_ok=True)

        # Analyze file
        analysis = self.analyzer.analyze(file_path)

        if analysis.format not in [BinaryFormat.PBL, BinaryFormat.PBD]:
            return RecoveryResult(
                success=False,
                recovered_entries=0,
                total_entries=0,
                errors=[f"Not a PBL/PBD file: {analysis.format.value}"],
                warnings=[],
                recovered_file=None,
            )

        errors = []
        warnings = []

        # Log corruption issues
        if analysis.corruption:
            for issue in analysis.corruption:
                warnings.append(f"Corruption detected: {issue}")

        # Attempt recovery strategies
        recovered_entries = 0
        total_entries = 0

        strategies = [
            self._recover_with_header_reconstruction,
            self._recover_with_pattern_matching,
            self._recover_with_brute_force,
        ]

        if self.aggressive:
            strategies.append(self._recover_with_deep_scan)

        for strategy in strategies:
            try:
                entries = strategy(file_path, analysis)
                if entries:
                    total_entries = len(entries)
                    recovered_entries = self._extract_entries(
                        entries, file_path, output_dir
                    )

                    if recovered_entries > 0:
                        logger.info(
                            f"Recovered {recovered_entries}/{total_entries} entries using {strategy.__name__}"
                        )
                        break

            except Exception as e:
                errors.append(f"{strategy.__name__} failed: {e}")

        # Create recovery report
        report_path = output_dir / "recovery_report.txt"
        self._write_report(
            report_path,
            file_path,
            analysis,
            recovered_entries,
            total_entries,
            errors,
            warnings,
        )

        return RecoveryResult(
            success=recovered_entries > 0,
            recovered_entries=recovered_entries,
            total_entries=total_entries,
            errors=errors,
            warnings=warnings,
            recovered_file=report_path,
        )

    def _recover_with_header_reconstruction(
        self, file_path: Path, analysis: Any
    ) -> Optional[List[PBLEntry]]:
        """Recover by reconstructing header.

        Args:
            file_path: File to recover
            analysis: File analysis

        Returns:
            Recovered entries
        """
        with BinaryReader(file_path) as reader:
            # Skip corrupted header
            reader.seek(32)

            entries = []
            entry_size = 288  # Standard PBL entry size

            # Try to find entry table
            while reader.tell() < reader.size - entry_size:
                try:
                    # Read potential entry
                    entry_data = reader.read(entry_size)

                    if self._looks_like_entry(entry_data):
                        entry = self._parse_entry(entry_data)
                        if entry:
                            entries.append(entry)

                except:
                    reader.seek(reader.tell() + 1)

            return entries if entries else None

    def _recover_with_pattern_matching(
        self, file_path: Path, analysis: Any
    ) -> Optional[List[PBLEntry]]:
        """Recover using pattern matching.

        Args:
            file_path: File to recover
            analysis: File analysis

        Returns:
            Recovered entries
        """
        with BinaryReader(file_path) as reader:
            reader.seek(0)
            data = reader.read()

            entries = []

            # Common PowerBuilder object signatures
            signatures = [
                b"window type",
                b"userobject type",
                b"menu type",
                b"datawindow",
                b"function ",
                b"structure",
                b"application",
            ]

            for sig in signatures:
                pos = 0
                while True:
                    pos = data.find(sig, pos)
                    if pos == -1:
                        break

                    # Try to extract object around signature
                    start = max(0, pos - 1000)
                    end = min(len(data), pos + 10000)

                    obj_data = data[start:end]
                    entry = self._extract_object_from_data(obj_data, sig)

                    if entry:
                        entries.append(entry)

                    pos += len(sig)

            return entries if entries else None

    def _recover_with_brute_force(
        self, file_path: Path, analysis: Any
    ) -> Optional[List[PBLEntry]]:
        """Brute force recovery.

        Args:
            file_path: File to recover
            analysis: File analysis

        Returns:
            Recovered entries
        """
        with BinaryReader(file_path) as reader:
            entries = []

            # Scan file in chunks
            chunk_size = 4096
            reader.seek(0)

            while reader.tell() < reader.size:
                chunk = reader.read(min(chunk_size, reader.size - reader.tell()))

                # Look for entry headers
                for i in range(len(chunk) - 4):
                    if chunk[i : i + 4] == b"\x00\x00\x00\x00":
                        # Potential entry boundary
                        pos = reader.tell() - len(chunk) + i

                        reader.seek(pos)
                        entry = self._try_parse_entry_at(reader)

                        if entry:
                            entries.append(entry)
                            reader.seek(pos + 288)  # Skip to next potential entry
                        else:
                            reader.seek(pos + 1)

            return entries if entries else None

    def _recover_with_deep_scan(
        self, file_path: Path, analysis: Any
    ) -> Optional[List[PBLEntry]]:
        """Deep scan recovery (aggressive).

        Args:
            file_path: File to recover
            analysis: File analysis

        Returns:
            Recovered entries
        """
        logger.info("Starting deep scan recovery (this may take time)...")

        with BinaryReader(file_path) as reader:
            reader.seek(0)
            data = reader.read()

            entries = []

            # Scan every possible offset
            for offset in range(0, len(data) - 32, 1):
                # Check if this could be an entry
                if self._could_be_entry(data[offset : offset + 32]):
                    reader.seek(offset)
                    entry = self._try_parse_entry_at(reader)

                    if entry:
                        entries.append(entry)
                        # Skip ahead to avoid duplicates
                        offset += 287

            # Deduplicate entries
            unique_entries = {}
            for entry in entries:
                if entry.name not in unique_entries:
                    unique_entries[entry.name] = entry

            return list(unique_entries.values()) if unique_entries else None

    def _looks_like_entry(self, data: bytes) -> bool:
        """Check if data looks like a PBL entry.

        Args:
            data: Data to check

        Returns:
            True if likely an entry
        """
        if len(data) < 288:
            return False

        # Check for reasonable values
        try:
            # Name should be ASCII
            name_bytes = data[:256]
            name_end = name_bytes.find(b"\x00")
            if name_end > 0:
                name = name_bytes[:name_end].decode("ascii")
                if name.isprintable():
                    return True
        except:
            pass

        return False

    def _parse_entry(self, data: bytes) -> Optional[PBLEntry]:
        """Parse PBL entry from data.

        Args:
            data: Entry data

        Returns:
            Parsed entry or None
        """
        try:
            # Extract name
            name_bytes = data[:256]
            name_end = name_bytes.find(b"\x00")
            if name_end <= 0:
                return None

            name = name_bytes[:name_end].decode("ascii")

            # Extract metadata
            type_val = struct.unpack("<I", data[256:260])[0]
            offset = struct.unpack("<I", data[260:264])[0]
            size = struct.unpack("<I", data[264:268])[0]

            # Map to object type
            type_map = {
                1: ObjectType.APPLICATION,
                2: ObjectType.DATAWINDOW,
                3: ObjectType.FUNCTION,
                4: ObjectType.MENU,
                5: ObjectType.STRUCTURE,
                6: ObjectType.USER_OBJECT,
                7: ObjectType.WINDOW,
            }

            obj_type = type_map.get(type_val, ObjectType.USER_OBJECT)

            return PBLEntry(
                name=name,
                type=obj_type,
                offset=offset,
                size=size,
            )

        except Exception as e:
            logger.debug(f"Failed to parse entry: {e}")
            return None

    def _extract_object_from_data(
        self, data: bytes, signature: bytes
    ) -> Optional[PBLEntry]:
        """Extract object from data around signature.

        Args:
            data: Data containing object
            signature: Object signature

        Returns:
            Extracted entry or None
        """
        try:
            # Determine object type from signature
            type_map = {
                b"window type": ObjectType.WINDOW,
                b"userobject type": ObjectType.USER_OBJECT,
                b"menu type": ObjectType.MENU,
                b"datawindow": ObjectType.DATAWINDOW,
                b"function ": ObjectType.FUNCTION,
                b"structure": ObjectType.STRUCTURE,
                b"application": ObjectType.APPLICATION,
            }

            obj_type = type_map.get(signature, ObjectType.USER_OBJECT)

            # Extract object name
            sig_pos = data.find(signature)
            if sig_pos == -1:
                return None

            # Look for object name before signature
            before = data[:sig_pos]
            lines = before.split(b"\n")

            for line in reversed(lines):
                if b"from" in line or b"type" in line:
                    # Extract name from declaration
                    parts = line.split()
                    if parts:
                        name = parts[0].decode("ascii", errors="ignore")
                        if name.isidentifier():
                            return PBLEntry(
                                name=name,
                                type=obj_type,
                                offset=sig_pos,
                                size=len(data),
                            )

            # Fallback: generate name
            import hashlib

            hash_val = hashlib.md5(data).hexdigest()[:8]
            name = f"recovered_{obj_type.value}_{hash_val}"

            return PBLEntry(
                name=name,
                type=obj_type,
                offset=0,
                size=len(data),
            )

        except Exception as e:
            logger.debug(f"Failed to extract object: {e}")
            return None

    def _try_parse_entry_at(self, reader: BinaryReader) -> Optional[PBLEntry]:
        """Try to parse entry at current position.

        Args:
            reader: Binary reader

        Returns:
            Parsed entry or None
        """
        try:
            pos = reader.tell()

            if reader.size - pos < 288:
                return None

            data = reader.read(288)
            return self._parse_entry(data)

        except:
            return None

    def _could_be_entry(self, data: bytes) -> bool:
        """Quick check if data could be entry.

        Args:
            data: Data to check

        Returns:
            True if possible entry
        """
        if len(data) < 32:
            return False

        # Check for ASCII characters in name field
        ascii_count = sum(1 for b in data[:32] if 32 <= b < 127)
        return ascii_count > 8

    def _extract_entries(
        self, entries: List[PBLEntry], file_path: Path, output_dir: Path
    ) -> int:
        """Extract recovered entries.

        Args:
            entries: Entries to extract
            file_path: Source file
            output_dir: Output directory

        Returns:
            Number of extracted entries
        """
        extracted = 0

        with BinaryReader(file_path) as reader:
            for entry in entries:
                try:
                    # Read entry data
                    reader.seek(entry.offset)
                    data = reader.read(entry.size)

                    # Determine output file
                    ext_map = {
                        ObjectType.WINDOW: ".srw",
                        ObjectType.USER_OBJECT: ".sru",
                        ObjectType.MENU: ".srm",
                        ObjectType.DATAWINDOW: ".srd",
                        ObjectType.FUNCTION: ".fun",
                        ObjectType.STRUCTURE: ".srs",
                        ObjectType.APPLICATION: ".sra",
                    }

                    ext = ext_map.get(entry.type, ".sru")
                    output_file = output_dir / f"{entry.name}{ext}"

                    # Write file
                    with open(output_file, "wb") as f:
                        f.write(data)

                    extracted += 1
                    logger.debug(f"Extracted {entry.name} to {output_file}")

                except Exception as e:
                    logger.warning(f"Failed to extract {entry.name}: {e}")

        return extracted

    def _write_report(
        self,
        report_path: Path,
        file_path: Path,
        analysis: Any,
        recovered: int,
        total: int,
        errors: List[str],
        warnings: List[str],
    ) -> None:
        """Write recovery report.

        Args:
            report_path: Report file path
            file_path: Original file
            analysis: File analysis
            recovered: Recovered entries
            total: Total entries
            errors: Error messages
            warnings: Warning messages
        """
        with open(report_path, "w") as f:
            f.write("PowerBuilder File Recovery Report\n")
            f.write("=" * 50 + "\n\n")

            f.write(f"File: {file_path}\n")
            f.write(f"Format: {analysis.format.value}\n")
            f.write(f"Size: {analysis.size} bytes\n")
            f.write(f"Checksum: {analysis.checksum}\n")
            f.write(f"Entropy: {analysis.entropy:.2f}\n\n")

            f.write("Recovery Results:\n")
            f.write(f"  Recovered: {recovered}/{total} entries\n")
            f.write(
                f"  Success Rate: {(recovered / total * 100 if total else 0):.1f}%\n\n"
            )

            if warnings:
                f.write("Warnings:\n")
                for warning in warnings:
                    f.write(f"  - {warning}\n")
                f.write("\n")

            if errors:
                f.write("Errors:\n")
                for error in errors:
                    f.write(f"  - {error}\n")
                f.write("\n")

            f.write(f"Report generated: {report_path}\n")


def recover_directory(
    directory: Path, output_dir: Path, aggressive: bool = False
) -> Dict[Path, RecoveryResult]:
    """Recover all corrupted files in directory.

    Args:
        directory: Directory to scan
        output_dir: Output directory
        aggressive: Use aggressive recovery

    Returns:
        Recovery results by file
    """
    engine = EnhancedRecoveryEngine(aggressive)
    results = {}

    for file_path in directory.rglob("*"):
        if file_path.is_file() and file_path.suffix.lower() in [".pbl", ".pbd"]:
            file_output = output_dir / file_path.stem
            result = engine.recover(file_path, file_output)
            results[file_path] = result

            if result.success:
                logger.info(
                    f"Recovered {file_path}: {result.recovered_entries}/{result.total_entries} entries"
                )
            else:
                logger.warning(f"Failed to recover {file_path}")

    return results
