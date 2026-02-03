"""Tiered P-code Detection - Fast pattern matching for P-code analysis.

This module implements a tiered detection strategy for P-code:
1. Ultra-fast: Quick header checks
2. Fast: Pattern matching
3. Comprehensive: Full analysis
4. Deep: Detailed inspection
"""

import logging
from enum import Enum
from pathlib import Path
from typing import Dict, List

from src_new._patterns import BinaryReader
from .opcodes import OPCODES

logger = logging.getLogger(__name__)


class DetectionTier(Enum):
    """P-code detection tiers."""

    ULTRA_FAST = 1  # < 1ms
    FAST = 2  # < 10ms
    COMPREHENSIVE = 3  # < 100ms
    DEEP = 4  # Unbounded


class PCodeSignature:
    """P-code signature patterns."""

    # Common P-code headers
    HEADERS = [
        b"\x50\x42",  # PB
        b"\x46\x55\x4e",  # FUN
        b"\x00\x00\x00\x00",  # NULL header
    ]

    # Function markers
    FUNCTION_START = [
        b"\x01\x00\x00\x00",  # Version 1
        b"\x02\x00\x00\x00",  # Version 2
    ]

    # Opcode sequences
    COMMON_SEQUENCES = [
        bytes([0x00, 0x02, 0x03]),  # RETURN, JUMPTRUE, JUMPFALSE
        bytes([0x10, 0x11, 0x12]),  # PUSH, POP, DUP
        bytes([0x20, 0x21, 0x22]),  # LOAD, STORE, CALL
    ]


class TieredDetector:
    """Tiered P-code detection engine."""

    def __init__(self, tier: DetectionTier = DetectionTier.FAST):
        """Initialize detector.

        Args:
            tier: Detection tier to use
        """
        self.tier = tier
        self.stats = {
            "files_analyzed": 0,
            "pcode_detected": 0,
            "tier_times": {t: 0.0 for t in DetectionTier},
        }

    def detect(self, file_path: Path) -> bool:
        """Detect if file contains P-code.

        Args:
            file_path: File to analyze

        Returns:
            True if P-code detected
        """
        import time

        start = time.time()

        try:
            result = False

            if self.tier.value >= DetectionTier.ULTRA_FAST.value:
                result = self._ultra_fast_detect(file_path)
                if result and self.tier == DetectionTier.ULTRA_FAST:
                    return result

            if self.tier.value >= DetectionTier.FAST.value and not result:
                result = self._fast_detect(file_path)
                if result and self.tier == DetectionTier.FAST:
                    return result

            if self.tier.value >= DetectionTier.COMPREHENSIVE.value and not result:
                result = self._comprehensive_detect(file_path)
                if result and self.tier == DetectionTier.COMPREHENSIVE:
                    return result

            if self.tier.value >= DetectionTier.DEEP.value and not result:
                result = self._deep_detect(file_path)

            self.stats["files_analyzed"] += 1
            if result:
                self.stats["pcode_detected"] += 1

            elapsed = time.time() - start
            self.stats["tier_times"][self.tier] += elapsed

            return result

        except Exception as e:
            logger.debug(f"Detection failed for {file_path}: {e}")
            return False

    def _ultra_fast_detect(self, file_path: Path) -> bool:
        """Ultra-fast detection (< 1ms).

        Args:
            file_path: File to check

        Returns:
            True if likely P-code
        """
        try:
            with BinaryReader(file_path) as reader:
                # Check file size
                if reader.size < 16 or reader.size > 10_000_000:
                    return False

                # Check header
                header = reader.read(4)
                for sig in PCodeSignature.HEADERS:
                    if header.startswith(sig):
                        return True

                # Check for function marker
                reader.seek(0)
                data = reader.read(min(256, reader.size))
                for marker in PCodeSignature.FUNCTION_START:
                    if marker in data:
                        return True

                return False

        except:
            return False

    def _fast_detect(self, file_path: Path) -> bool:
        """Fast detection (< 10ms).

        Args:
            file_path: File to check

        Returns:
            True if likely P-code
        """
        try:
            with BinaryReader(file_path) as reader:
                # Read first KB
                data = reader.read(min(1024, reader.size))

                # Check for opcode sequences
                for seq in PCodeSignature.COMMON_SEQUENCES:
                    if seq in data:
                        return True

                # Check for valid opcodes
                valid_count = 0
                for byte in data:
                    if byte in OPCODES:
                        valid_count += 1

                # If >30% are valid opcodes, likely P-code
                if valid_count > len(data) * 0.3:
                    return True

                return False

        except:
            return False

    def _comprehensive_detect(self, file_path: Path) -> bool:
        """Comprehensive detection (< 100ms).

        Args:
            file_path: File to check

        Returns:
            True if P-code confirmed
        """
        try:
            with BinaryReader(file_path) as reader:
                # Analyze structure
                structure = self._analyze_structure(reader)

                if structure["has_function_table"]:
                    return True

                if structure["opcode_density"] > 0.5:
                    return True

                if structure["has_string_table"] and structure["opcode_density"] > 0.2:
                    return True

                return False

        except:
            return False

    def _deep_detect(self, file_path: Path) -> bool:
        """Deep detection (unbounded time).

        Args:
            file_path: File to check

        Returns:
            True if P-code confirmed
        """
        try:
            with BinaryReader(file_path) as reader:
                # Try to decode as P-code
                from .decompiler import PCodeDecoder

                decoder = PCodeDecoder()
                try:
                    # Attempt decode
                    instructions = decoder.decode(reader.read())
                    return len(instructions) > 0
                except:
                    return False

        except:
            return False

    def _analyze_structure(self, reader: BinaryReader) -> Dict:
        """Analyze file structure.

        Args:
            reader: Binary reader

        Returns:
            Structure analysis
        """
        reader.seek(0)
        data = reader.read(min(8192, reader.size))

        # Check for function table
        has_function_table = b"\x00\x00\x00\x00" in data[:256]

        # Calculate opcode density
        valid_opcodes = sum(1 for b in data if b in OPCODES)
        opcode_density = valid_opcodes / len(data) if data else 0

        # Check for string table
        has_string_table = b"\x00" * 4 in data and data.count(b"\x00") > len(data) * 0.1

        return {
            "has_function_table": has_function_table,
            "opcode_density": opcode_density,
            "has_string_table": has_string_table,
        }

    def get_statistics(self) -> Dict:
        """Get detection statistics.

        Returns:
            Statistics dictionary
        """
        return self.stats.copy()


class OptimizedDetector(TieredDetector):
    """Optimized detector with caching and parallel processing."""

    def __init__(self):
        """Initialize optimized detector."""
        super().__init__(DetectionTier.FAST)
        self._cache: Dict[str, bool] = {}

    def detect_batch(
        self, files: List[Path], parallel: bool = True
    ) -> Dict[Path, bool]:
        """Detect P-code in batch.

        Args:
            files: Files to check
            parallel: Use parallel processing

        Returns:
            Detection results
        """
        results = {}

        if parallel:
            from concurrent.futures import ThreadPoolExecutor

            with ThreadPoolExecutor(max_workers=8) as executor:
                futures = {executor.submit(self.detect, f): f for f in files}

                for future in futures:
                    file_path = futures[future]
                    try:
                        results[file_path] = future.result(timeout=1.0)
                    except:
                        results[file_path] = False
        else:
            for file_path in files:
                results[file_path] = self.detect(file_path)

        return results

    def detect(self, file_path: Path) -> bool:
        """Cached detection.

        Args:
            file_path: File to check

        Returns:
            True if P-code detected
        """
        cache_key = str(file_path.absolute())

        if cache_key in self._cache:
            return self._cache[cache_key]

        result = super().detect(file_path)
        self._cache[cache_key] = result

        return result

    def clear_cache(self) -> None:
        """Clear detection cache."""
        self._cache.clear()


def detect_pcode_files(
    directory: Path, tier: DetectionTier = DetectionTier.FAST
) -> List[Path]:
    """Detect all P-code files in directory.

    Args:
        directory: Directory to scan
        tier: Detection tier

    Returns:
        List of P-code files
    """
    detector = (
        OptimizedDetector() if tier == DetectionTier.FAST else TieredDetector(tier)
    )

    pcode_files = []
    for file_path in directory.rglob("*.fun"):
        if detector.detect(file_path):
            pcode_files.append(file_path)

    logger.info(f"Found {len(pcode_files)} P-code files")
    return pcode_files
