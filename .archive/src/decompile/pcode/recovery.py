"""P-code recovery strategies for handling invalid or corrupted sequences.

This module provides recovery mechanisms for dealing with invalid P-code
sequences that may occur due to:
    - Corrupted data
    - Version mismatches
    - Incomplete extractions
    - Unknown opcodes
"""

import logging
from dataclasses import dataclass
from typing import Any, Dict

from src.decompile.pcode.decoder import PCodeInstruction

logger = logging.getLogger(__name__)


@dataclass
class RecoveryResult:
    """Result of a recovery attempt."""

    success: bool
    recovered_instructions: list[PCodeInstruction]
    skipped_bytes: int
    recovery_method: str
    confidence: float


class PCodeRecoveryManager:
    """Manages recovery strategies for invalid P-code sequences."""

    # Common P-code patterns that indicate valid code
    VALID_PATTERNS = [
        # Function prologue patterns
        [0x1E, 0x1F],  # PUSH_LOCAL_VAR, PUSH_SHARED_VAR
        [0x21, 0x1E],  # PUSH_THIS, PUSH_LOCAL_VAR
        # Function epilogue patterns
        [0x00, 0x00],  # RETURN, RETURN
        [0x01, 0x00],  # STORE_RETURN_VAL, RETURN
        # Common control flow
        [0x02, 0x04],  # JUMPTRUE, JUMP
        [0x03, 0x04],  # JUMPFALSE, JUMP
        # Common operations
        [0x1E, 0x1E, 0x53],  # PUSH, PUSH, ADD_INT
        [0x1E, 0x1E, 0xA6],  # PUSH, PUSH, EQ_INT
    ]

    # Opcodes that should never appear consecutively
    INVALID_SEQUENCES = [
        # Multiple returns without code between
        [0x00, 0x00, 0x00, 0x00, 0x00],  # 5+ RETURNs
        # Invalid jump patterns
        [0x04, 0x04, 0x04],  # Multiple unconditional jumps
    ]

    def __init__(self) -> None:
        """Initialize the recovery manager."""
        self.recovery_stats = {
            "total_attempts": 0,
            "successful_recoveries": 0,
            "bytes_recovered": 0,
            "bytes_skipped": 0,
        }

    def attempt_recovery(
        self,
        pcode_bytes: bytes,
        error_offset: int,
        context_before: list[PCodeInstruction],
        error_description: str,
    ) -> RecoveryResult | None:
        """Attempt to recover from an invalid P-code sequence.

        pcode_bytes: The full P-code byte array
        error_offset: Offset where the error occurred
        context_before: Instructions decoded before the error
        error_description: Description of the error

        RecoveryResult if recovery successful, None otherwise
        """
        self.recovery_stats["total_attempts"] += 1

        logger.info(
            "Attempting recovery at offset 0x%04X: %s", error_offset, error_description
        )

        # Try recovery strategies in order of preference
        strategies = [
            self._try_pattern_matching_recovery,
            self._try_resync_recovery,
            self._try_heuristic_skip_recovery,
            self._try_boundary_detection_recovery,
        ]

        for strategy in strategies:
            result = strategy(pcode_bytes, error_offset, context_before)
            if result and result.success:
                self.recovery_stats["successful_recoveries"] += 1
                self.recovery_stats["bytes_recovered"] += len(
                    result.recovered_instructions
                )
                self.recovery_stats["bytes_skipped"] += result.skipped_bytes

                logger.info(
                    "Recovery successful using %s (confidence: %.2f)",
                    result.recovery_method,
                    result.confidence,
                )
                return result

        logger.warning("All recovery strategies failed at offset 0x%04X", error_offset)
        return None

    def _try_pattern_matching_recovery(
        self, pcode_bytes: bytes, error_offset: int, _context: Any
    ) -> RecoveryResult | None:
        """Try to recover by finding known valid patterns."""
        window_size = 20  # Look ahead 20 bytes

        if error_offset + window_size > len(pcode_bytes):
            window_size = len(pcode_bytes) - error_offset

        # Search for valid patterns in the window
        for i in range(window_size):
            check_offset = error_offset + i

            # Check each valid pattern
            for pattern in self.VALID_PATTERNS:
                if self._matches_pattern(pcode_bytes, check_offset, pattern):
                    logger.debug("Found valid pattern at offset 0x%04X", check_offset)

                    # Skip to the valid pattern
                    return RecoveryResult(
                        success=True,
                        recovered_instructions=[],
                        skipped_bytes=i,
                        recovery_method="pattern_matching",
                        confidence=0.8,
                    )

        return None

    def _try_resync_recovery(
        self, pcode_bytes: bytes, error_offset: int, _context: Any
    ) -> RecoveryResult | None:
        """Try to resynchronize by finding the next valid opcode."""
        max_skip = 10  # Don't skip more than 10 bytes

        for skip in range(1, max_skip + 1):
            check_offset = error_offset + skip
            if check_offset >= len(pcode_bytes):
                break

            opcode = pcode_bytes[check_offset]

            # Check if this looks like a valid opcode
            if self._is_likely_valid_opcode(opcode, pcode_bytes, check_offset):
                logger.debug(
                    "Resync found likely valid opcode 0x%02X at offset 0x%04X",
                    opcode,
                    check_offset,
                )

                return RecoveryResult(
                    success=True,
                    recovered_instructions=[],
                    skipped_bytes=skip,
                    recovery_method="resync",
                    confidence=0.6,
                )

        return None

    def _try_heuristic_skip_recovery(
        self, pcode_bytes: bytes, error_offset: int, _context: Any
    ) -> RecoveryResult | None:
        """Use heuristics to determine how many bytes to skip."""
        # Look at the error byte and surrounding context
        if error_offset >= len(pcode_bytes):
            return None

        error_byte = pcode_bytes[error_offset]

        # High byte values often indicate data, not code
        if error_byte > 0xF0:
            # Skip until we find a byte < 0x80
            skip = 0
            while (
                error_offset + skip < len(pcode_bytes)
                and pcode_bytes[error_offset + skip] > 0x80
            ):
                skip += 1

            if skip > 0:
                return RecoveryResult(
                    success=True,
                    recovered_instructions=[],
                    skipped_bytes=skip,
                    recovery_method="heuristic_skip",
                    confidence=0.5,
                )

        return None

    def _try_boundary_detection_recovery(
        self, pcode_bytes: bytes, error_offset: int, context: list[PCodeInstruction]
    ) -> RecoveryResult | None:
        """Try to find the next function or block boundary."""
        # Look for patterns that indicate function boundaries
        boundary_patterns = [
            [0x00, 0x00, 0x00],  # Multiple returns
            [0xFF, 0xFF, 0xFF],  # Padding
            [0x00] * 8,  # Null padding
        ]

        search_window = 50
        for i in range(min(search_window, len(pcode_bytes) - error_offset)):
            check_offset = error_offset + i

            for pattern in boundary_patterns:
                if self._matches_pattern(pcode_bytes, check_offset, pattern):
                    # Skip past the boundary pattern
                    skip_bytes = i + len(pattern)

                    return RecoveryResult(
                        success=True,
                        recovered_instructions=[],
                        skipped_bytes=skip_bytes,
                        recovery_method="boundary_detection",
                        confidence=0.7,
                    )

        return None

    def _matches_pattern(
        self, pcode_bytes: bytes, offset: int, pattern: list[int]
    ) -> bool:
        """Check if bytes at offset match the given pattern."""
        if offset + len(pattern) > len(pcode_bytes):
            return False

        for i, expected in enumerate(pattern):
            if pcode_bytes[offset + i] != expected:
                return False

        return True

    def _is_likely_valid_opcode(
        self, opcode: int, pcode_bytes: bytes, offset: int
    ) -> bool:
        """Determine if an opcode is likely valid based on context."""
        # Basic range check
        if opcode > 0x246:  # Max known opcode
            return False

        # Check if it's a known common opcode
        common_opcodes = {
            0x00,  # RETURN
            0x01,  # STORE_RETURN_VAL
            0x02,
            0x03,
            0x04,  # Jumps
            0x1E,
            0x1F,  # Push operations
            0x53,
            0x54,
            0x55,  # Arithmetic
            0xA6,
            0xA7,
            0xA8,  # Comparisons
        }

        if opcode in common_opcodes:
            return True

        # Check if next bytes look like valid operands
        if offset + 1 < len(pcode_bytes):
            next_byte = pcode_bytes[offset + 1]
            # Most operands are small values
            if next_byte < 0x20:
                return True

        return False

    def analyze_corruption_patterns(
        self, pcode_bytes: bytes, instructions: list[PCodeInstruction]
    ) -> Dict[str, Any]:
        """Analyze P-code for corruption patterns.

        Dictionary with analysis results
        """
        analysis: Dict[str, Any] = {
            "total_bytes": len(pcode_bytes),
            "decoded_instructions": len(instructions),
            "invalid_sequences": [],
            "suspicious_patterns": [],
            "recovery_suggestions": [],
        }

        # Check for invalid sequences
        for i in range(len(instructions) - 1):
            curr = instructions[i]
            next_inst = instructions[i + 1]

            # Multiple consecutive returns
            if curr.opcode_name == "RETURN" and next_inst.opcode_name == "RETURN":
                if (
                    i + 2 < len(instructions)
                    and instructions[i + 2].opcode_name == "RETURN"
                ):
                    analysis["invalid_sequences"].append(
                        {
                            "offset": curr.offset,
                            "pattern": "multiple_returns",
                            "description": "3+ consecutive RETURN instructions",
                        }
                    )

        # Check for suspicious patterns
        opcode_histogram: dict[str, list[str]] = {}
        for inst in instructions:
            opcode_histogram[inst.opcode_name] = (
                opcode_histogram.get(inst.opcode_name, 0) + 1
            )

        # Unusually high frequency of unknown opcodes
        unknown_count = sum(
            1 for inst in instructions if inst.opcode_name.startswith("UNK_")
        )
        if unknown_count > len(instructions) * 0.2:  # More than 20% unknown
            analysis["suspicious_patterns"].append(
                {
                    "type": "high_unknown_ratio",
                    "ratio": unknown_count / len(instructions),
                    "suggestion": "Check PowerBuilder version or corruption",
                }
            )

        # Generate recovery suggestions
        if analysis["invalid_sequences"]:
            analysis["recovery_suggestions"].append(
                "Use pattern-based recovery to skip invalid sequences"
            )

        if analysis["suspicious_patterns"]:
            analysis["recovery_suggestions"].append(
                "Consider different PowerBuilder version or re-extraction"
            )

        return analysis
