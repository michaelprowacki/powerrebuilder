"""Enhanced P-code detection for PowerBuilder objects.

This module provides improved P-code detection that understands
PowerBuilder object structures better.
"""

import logging

logger = logging.getLogger(__name__)


class PCodeSection:
    """Information about a single P-code section."""

    def __init__(
        self,
        offset: int = 0,
        length: int = 0,
        confidence: float = 0.0,
        pattern_matches: int = 0,
        metadata: dict | None = None,
    ) -> None:
        self.offset = offset
        self.length = length
        self.confidence = confidence  # 0.0 to 1.0
        self.pattern_matches = pattern_matches  # Number of pattern matches found
        self.metadata = metadata or {}  # Additional metadata about the section

    def __repr__(self) -> str:
        return f"PCodeSection(offset=0x{self.offset:04x}, length={self.length}, confidence={self.confidence:.2f})"


class PCodeInfo:
    """Information about detected P-code."""

    def __init__(
        self,
        pcode_offset: int = -1,
        pcode_length: int = 0,
        object_type: str = "function",
        confidence: str = "none",
        sections: list[PCodeSection] | None = None,
        detection_time: float = 0.0,
        tiers_used: list[int] | None = None,
        file_size: int = 0,
        **kwargs,
    ) -> None:
        """Initialize P-code information.

        pcode_offset: Offset of P-code in the data (-1 if not found)
        pcode_length: Length of P-code section (0 if not found)
        object_type: Type of PowerBuilder object
        confidence: Confidence level of detection ("high", "medium", "low", "none", or float 0.0-1.0)
        sections: List of detected P-code sections
        detection_time: Time taken for detection (seconds)
        tiers_used: List of tier numbers used in tiered detection
        file_size: Size of the analyzed file
        **kwargs: Additional metadata fields
        """
        self.pcode_offset = pcode_offset
        self.pcode_length = pcode_length
        self.object_type = object_type
        self.confidence = confidence
        self.sections = sections or []
        self.detection_time = detection_time
        self.tiers_used = tiers_used or []
        self.file_size = file_size
        # Store any additional metadata
        for key, value in kwargs.items():
            setattr(self, key, value)


class PCodeDetector:
    """Enhanced P-code detector for PowerBuilder objects."""

    @classmethod
    def is_pcode_object(cls, object_name: str) -> bool:
        """Check if object type typically contains P-code.

        Args:
            object_name: Name of the object (with extension)

        Returns:
            True if the object type typically has P-code
        """
        name_lower = object_name.lower()

        # Object types that contain P-code
        pcode_extensions = [
            ".fun",  # Functions
            ".sru",  # User objects
            ".srw",  # Windows
            ".srm",  # Menus
            ".sra",  # Applications
            ".str",  # Structures (sometimes have constructor/destructor)
            ".men",  # Old menu format
            ".win",  # Old window format
            ".udo",  # Old user object format
        ]

        return any(name_lower.endswith(ext) for ext in pcode_extensions)

    @classmethod
    def find_pcode_in_function(cls, data: bytes) -> tuple[int, int]:
        """Find P-code in a function's data.

        Function structure typically includes:
        1. Header/metadata
        2. Optional source code
        3. P-code section

        Args:
            data: Raw function data (from DAT blocks)

        Returns:
            Tuple of (offset, length) for P-code section, or (-1, 0) if not found
        """
        if len(data) < 16:
            return -1, 0

        # Check for PowerBuilder export format header
        if data.startswith(b"HA$PBExportHeader$"):
            return cls._handle_export_format(data)

        # Find P-code start
        pcode_start = cls._find_pcode_start(data)
        if pcode_start < 0:
            logger.warning("Could not find P-code in function data")
            return -1, 0

        # Find the end of executable P-code
        pcode_end = cls._find_pcode_end(data, pcode_start)
        return pcode_start, pcode_end - pcode_start

    @classmethod
    def _handle_export_format(cls, data: bytes) -> tuple[int, int]:
        r"""Handle PowerBuilder export format.

        HA$PBExportHeader$<objectname>\n
        $PBExportComments$\n
        <binary p-code data>
        """
        # Find the first newline (end of header line)
        first_newline = data.find(b"\n")
        if first_newline < 0:
            logger.warning("Malformed PowerBuilder export header - no newline")
            return -1, 0

        # Find the second newline (end of comments line)
        second_newline = data.find(b"\n", first_newline + 1)
        if second_newline < 0:
            logger.warning("Malformed PowerBuilder export header - no second newline")
            return -1, 0

        # P-code starts after the second newline
        pcode_start = second_newline + 1
        pcode_length = len(data) - pcode_start

        logger.debug(
            "Export format detected. P-code starts at offset %d (0x%04x)",
            pcode_start,
            pcode_start,
        )
        return pcode_start, pcode_length

    @classmethod
    def _find_pcode_start(cls, data: bytes) -> int:
        """Find the start of P-code in the data using high-performance O(n) algorithm.

        This method has been optimized from O(n²) to O(n) complexity using:
        - Boyer-Moore pattern matching for fast signature detection
        - Sliding window with cached confidence scores
        - Heuristics to jump to likely P-code locations
        - Early termination when sufficient confidence is found

        Args:
            data: Raw binary data to search for P-code

        Returns:
            Offset of P-code start, or -1 if not found
        """
        logger.debug("High-performance P-code scanning on %d bytes", len(data))

        # Import the high-performance detector
        try:
            from .high_performance_detector import HighPerformancePCodeDetector

            detector = HighPerformancePCodeDetector()
            offset, confidence = detector.find_pcode_start_optimized(data)

            if offset >= 0:
                logger.info(
                    "High-performance detector found P-code at offset 0x%04x (confidence: %.2f, O(n) complexity)",
                    offset,
                    confidence,
                )
                return offset
            logger.warning("High-performance detector found no P-code")
            return -1

        except ImportError:
            logger.warning(
                "High-performance detector not available, falling back to legacy O(n²) method"
            )
            return cls._find_pcode_start_legacy(data)

    @classmethod
    def _find_pcode_start_legacy(cls, data: bytes) -> int:
        """Legacy O(n²) P-code detection method for fallback.

        This is the original implementation kept for compatibility.
        """
        logger.debug("Using legacy O(n²) P-code scanning on %d bytes", len(data))

        # Common P-code start patterns in functions
        pcode_patterns = [
            b"\x04\x00",  # JUMP instruction (0x04)
            b"\x05\x00",  # DBSTART (0x05)
            b"\x29\x00",  # GLOBFUNCCALL (0x29)
            b"\x2c\x00",  # DOTFUNCCALL (0x2C)
            b"\x32\x00",  # PUSH_CONST_INT (0x32)
            b"\x15\x00",  # DBEXECUTEDYN (0x15)
        ]

        # Scan the ENTIRE file, not just first 1KB
        best_offset = -1
        best_confidence = 0.0

        for i in range(len(data)):
            # Skip obvious UTF-16 strings (lots of alternating 0x00 bytes)
            if cls._is_utf16_string(data, i):
                continue

            confidence = cls._calculate_pcode_confidence(data[i : i + 100])
            if confidence > 0.7:
                logger.debug(
                    "Found high-confidence P-code at offset 0x%04x (confidence: %.2f)",
                    i,
                    confidence,
                )
                if confidence > best_confidence:
                    best_confidence = confidence
                    best_offset = i

            for pattern in pcode_patterns:
                if (
                    i + len(pattern) <= len(data)
                    and data[i : i + len(pattern)] == pattern
                ):
                    # Verify this isn't part of a string or other data
                    if cls._verify_pcode_context(data, i):
                        pattern_confidence = cls._calculate_pcode_confidence(
                            data[i : i + 100]
                        )
                        logger.debug(
                            "Found P-code by pattern %s at offset 0x%04x (confidence: %.2f)",
                            pattern.hex(),
                            i,
                            pattern_confidence,
                        )
                        if pattern_confidence > best_confidence:
                            best_confidence = pattern_confidence
                            best_offset = i

        # If we found a good candidate, return it
        if best_offset >= 0:
            logger.info(
                "Legacy detector found P-code at offset 0x%04x with confidence %.2f",
                best_offset,
                best_confidence,
            )
            return best_offset

        text_end = cls._find_text_to_binary_transition(data)
        if text_end > 0:
            logger.debug(
                "Found P-code after text transition at offset 0x%04x", text_end
            )
            return text_end

        logger.warning("No P-code found in data")
        return -1

    @classmethod
    def _looks_like_pcode(cls, data: bytes) -> bool:
        """Check if data looks like P-code instructions."""
        return cls._calculate_pcode_confidence(data) > 0.5

    @classmethod
    def _calculate_pcode_confidence(cls, data: bytes) -> float:
        """Calculate confidence that data contains P-code.

        ENHANCED ALGORITHM: This confidence calculation was significantly improved
        to better distinguish P-code from other binary data, reducing false positives
        and improving detection accuracy.

        Key improvements:
        1. Extended opcode dictionary with all known PowerBuilder instructions
        2. Better handling of small P-code sections (getters/setters)
        3. Pattern recognition for common instruction sequences
        4. UTF-16 string detection to avoid false positives
        5. Sophisticated scoring based on instruction diversity

        Returns:
            Confidence score from 0.0 to 1.0
        """
        # Handle small P-code sections (e.g., simple getters/setters)
        if len(data) < 1:
            # Empty data cannot be P-code
            return 0.0
        if len(data) < 2:
            # Single byte - check if it's a valid opcode
            if data[0] in {0x00, 0x01}:  # RETURN or STORE_RETURN_VAL
                return 0.4  # Some confidence for single valid opcode
            return 0.0  # Invalid single byte
        if len(data) < 10:
            # Small function - adjust confidence calculation
            logger.debug("Analyzing small P-code section (%d bytes)", len(data))
            # For small sections, we'll use a simplified analysis
            return cls._calculate_small_section_confidence(data)

        # Extended list of known valid opcodes
        valid_opcodes = {
            0x00: "RETURN",
            0x01: "STORE_RETURN_VAL",
            0x02: "JUMPTRUE",
            0x03: "JUMPFALSE",
            0x04: "JUMP",
            0x05: "DBSTART",
            0x06: "DBCOMMIT",
            0x07: "DBROLLBACK",
            0x08: "DBSTOP",
            0x09: "DBCLOSE",
            0x0A: "DBOPEN",
            0x0B: "PUSH_LOCALVAR",
            0x0C: "PUSH_SHAREDVAR",
            0x0D: "PUSH_GLOBALVAR",
            0x0E: "PUSH_STRUCTVAR",
            0x0F: "PUSH_STRUCTFIELD",
            0x10: "PUSH_ARRAYVAR",
            0x11: "POP_LOCALVAR",
            0x12: "POP_SHAREDVAR",
            0x13: "POP_GLOBALVAR",
            0x14: "POP_STRUCTVAR",
            0x15: "DBEXECUTEDYN",
            0x16: "PUSH_ARRAYREF",
            0x17: "POP_ARRAYVAR",
            0x18: "ADD",
            0x19: "SUBTRACT",
            0x1A: "MULTIPLY",
            0x1B: "DIVIDE",
            0x1C: "MODULUS",
            0x1D: "NEGATE",
            0x1E: "EQUAL",
            0x1F: "NOT_EQUAL",
            0x20: "LESS_THAN",
            0x21: "GREATER_THAN",
            0x22: "LESS_EQUAL",
            0x23: "GREATER_EQUAL",
            0x24: "AND",
            0x25: "OR",
            0x26: "NOT",
            0x27: "CONCAT",
            0x28: "FUNCCALL",
            0x29: "GLOBFUNCCALL",
            0x2A: "CREATE",
            0x2B: "DESTROY",
            0x2C: "DOTFUNCCALL",
            0x2D: "PUSH_PROPERTY",
            0x2E: "POP_PROPERTY",
            0x2F: "DUP",
            0x30: "POP",
            0x31: "PUSH_CONST_STR",
            0x32: "PUSH_CONST_INT",
            0x33: "PUSH_CONST_LONG",
            0x34: "PUSH_CONST_REAL",
            0x35: "PUSH_CONST_DOUBLE",
            0x36: "PUSH_CONST_DEC",
            0x37: "PUSH_CONST_DATE",
            0x38: "PUSH_CONST_TIME",
            0x39: "PUSH_CONST_DATETIME",
            0x3A: "PUSH_CONST_TRUE",
            0x3B: "PUSH_CONST_FALSE",
            0x3C: "PUSH_CONST_NULL",
            0x3D: "PUSH_CONST_ENUM",
            0x3E: "ISNULL",
            0x3F: "CNV_TO_STRING",
            0x40: "CNV_INT_TO_ULONG",
            0x41: "CNV_TO_INT",
            0x42: "CNV_TO_LONG",
            0x43: "CNV_TO_REAL",
            0x44: "CNV_TO_DOUBLE",
            0x45: "CNV_TO_DEC",
            0x46: "CNV_TO_DATE",
            0x47: "CNV_TO_TIME",
            0x48: "CNV_TO_DATETIME",
            0x49: "CNV_TO_BOOLEAN",
            0x4A: "INCR_INT",
            0x4B: "DECR_INT",
            0x4C: "INCR_LONG",
            0x4D: "DECR_LONG",
            0x4E: "INCR_REAL",
            0x4F: "DECR_REAL",
            0x50: "INCR_DOUBLE",
            0x51: "DECR_DOUBLE",
            0x52: "ASSIGN",
            0x53: "TRY",
            0x54: "CATCH",
            0x55: "FINALLY",
            0x56: "THROW",
            0x57: "CASE",
            0x58: "SWITCH",
            0x59: "FOR",
            0x5A: "WHILE",
            0x5B: "DO",
            0x5C: "BREAK",
            0x5D: "CONTINUE",
            0x5E: "EXIT",
            0x5F: "HALT",
            0x60: "CALL_PARENT",
            0x61: "CALL_ANCESTOR",
            0x62: "CAST",
            0x63: "TYPEOF",
            0x64: "INSTANCEOF",
            0x65: "TRIGGER_EVENT",
            0x66: "POST_EVENT",
            0xFE: "EXTENDED",
            0xFF: "DEBUG",
        }

        # Calculate various metrics
        valid_opcode_count = 0
        total_bytes = min(len(data), 100)  # Analyze up to 100 bytes
        consecutive_nulls = 0
        max_consecutive_nulls = 0
        instruction_sequences = 0

        i = 0
        while i < total_bytes:
            byte = data[i]

            # Count valid opcodes
            if byte in valid_opcodes:
                valid_opcode_count += 1
                consecutive_nulls = 0

                # Check for common instruction sequences
                if i + 1 < total_bytes:
                    next_byte = data[i + 1]
                    # Common patterns: opcode followed by 0x00 (no operands)
                    if (
                        next_byte == 0x00
                        and byte
                        in {
                            0x00,
                            0x01,
                            0x18,
                            0x19,
                            0x1A,
                            0x1B,
                            0x24,
                            0x25,
                            0x26,
                            0x2F,
                            0x30,
                        }
                    ) or (byte in range(0x31, 0x3E) and next_byte != 0x00):
                        instruction_sequences += 1
            elif byte == 0x00:
                consecutive_nulls += 1
                max_consecutive_nulls = max(max_consecutive_nulls, consecutive_nulls)
            else:
                consecutive_nulls = 0

            i += 1

        # Calculate confidence score
        confidence = 0.0

        opcode_ratio = valid_opcode_count / total_bytes if total_bytes > 0 else 0
        confidence += opcode_ratio * 0.4

        sequence_ratio = min(
            instruction_sequences / 5.0, 1.0
        )  # Expect at least 5 sequences
        confidence += sequence_ratio * 0.3

        # UTF-16 strings have alternating nulls, P-code shouldn't have more than 3-4 in a row
        if max_consecutive_nulls <= 4:
            confidence += 0.2
        elif max_consecutive_nulls <= 8:
            confidence += 0.1

        # P-code should have diverse byte values, not just ASCII
        unique_bytes = len(set(data[:total_bytes]))
        diversity_ratio = unique_bytes / min(total_bytes, 50)
        if diversity_ratio > 0.3:  # At least 30% unique bytes
            confidence += 0.1

        return min(confidence, 1.0)

    @classmethod
    def _is_getter_pattern(cls, data: bytes) -> bool:
        """Check if data matches a getter pattern.

        May have operands between the opcodes.

        data: P-code data to check

        True if matches getter pattern
        """
        if len(data) < 2:
            return False

        # Check if starts with PUSH_PROPERTY
        if data[0] != 0x2D:
            return False

        # Check if ends with RETURN (0x00)
        # RETURN could be last byte or have an operand after it
        for i in range(len(data) - 1, 0, -1):
            if data[i] == 0x00:
                logger.debug("Detected getter pattern: PUSH_PROPERTY + RETURN")
                return True

        return False

    @classmethod
    def _is_setter_pattern(cls, data: bytes) -> bool:
        """Check if data matches a setter pattern.

        May have operands between the opcodes.

        data: P-code data to check

        True if matches setter pattern
        """
        if len(data) < 2:
            return False

        # Check if starts with POP_PROPERTY
        if data[0] != 0x2E:
            return False

        # Check if ends with RETURN (0x00)
        for i in range(len(data) - 1, 0, -1):
            if data[i] == 0x00:
                logger.debug("Detected setter pattern: POP_PROPERTY + RETURN")
                return True

        return False

    @classmethod
    def _is_const_return(cls, data: bytes) -> bool:
        """Check if data matches a constant return pattern.

        data: P-code data to check

        True if matches constant return pattern
        """
        if len(data) < 2:
            return False

        # Check if starts with PUSH_CONST opcode
        const_opcodes = {0x32, 0x33, 0x34, 0x35, 0x3A, 0x3B, 0x3C}
        if data[0] not in const_opcodes:
            return False

        # Check if contains RETURN (0x00)
        for i in range(1, len(data)):
            if data[i] == 0x00:
                logger.debug("Detected const return pattern: PUSH_CONST_* + RETURN")
                return True

        return False

    @classmethod
    def _calculate_small_section_confidence(cls, data: bytes) -> float:
        """Calculate confidence for small P-code sections (2-9 bytes).

        - Simple getter: PUSH_PROPERTY, RETURN (could be 2-6 bytes)
        - Simple setter: POP_PROPERTY, RETURN (could be 2-6 bytes)
        - Constant return: PUSH_CONST, RETURN (could be 2-4 bytes)

        data: P-code data (2-9 bytes)

        Confidence score from 0.0 to 1.0
        """
        # Check for recognized patterns first
        if cls._is_getter_pattern(data) or cls._is_setter_pattern(data):
            return 0.9

        if cls._is_const_return(data):
            return 0.85

        # Extended list of known valid opcodes (same as in main method)
        valid_opcodes = {
            0x00: "RETURN",
            0x01: "STORE_RETURN_VAL",
            0x0B: "PUSH_LOCALVAR",
            0x0C: "PUSH_SHAREDVAR",
            0x0D: "PUSH_GLOBALVAR",
            0x11: "POP_LOCALVAR",
            0x12: "POP_SHAREDVAR",
            0x13: "POP_GLOBALVAR",
            0x2D: "PUSH_PROPERTY",
            0x2E: "POP_PROPERTY",
            0x2F: "DUP",
            0x30: "POP",
            0x32: "PUSH_CONST_INT",
            0x33: "PUSH_CONST_LONG",
            0x34: "PUSH_CONST_REAL",
            0x35: "PUSH_CONST_DOUBLE",
            0x3A: "PUSH_CONST_TRUE",
            0x3B: "PUSH_CONST_FALSE",
            0x3C: "PUSH_CONST_NULL",
        }

        # For small sections, check if it forms a valid minimal function
        confidence = 0.0
        valid_opcode_count = 0

        # Special handling for very small sections (2-3 bytes)
        if len(data) == 2:
            # Check for minimal valid patterns
            if (
                data[0] in valid_opcodes and data[1] == 0x00
            ):  # Any valid opcode + operand
                if data[0] == 0x00:  # Just RETURN:
                    logger.debug("Detected minimal RETURN pattern (2 bytes)")
                    return 0.8
                if data[0] in {0x2D, 0x2E}:  # Property access without operand:
                    logger.debug("Detected minimal property pattern (2 bytes)")
                    return 0.7
                if data[0] in {0x32, 0x3A, 0x3B, 0x3C}:  # Push constant:
                    logger.debug("Detected minimal constant pattern (2 bytes)")
                    return 0.75
            return 0.1  # Very low confidence for other 2-byte patterns

        # Check each byte
        for i, byte in enumerate(data):
            if byte in valid_opcodes:
                valid_opcode_count += 1

            # Check for common small function patterns
            if i == 0:
                # First opcode should typically be a PUSH or assignment
                if byte in {
                    0x0B,
                    0x0C,
                    0x0D,
                    0x2D,
                    0x32,
                    0x33,
                    0x34,
                    0x35,
                    0x3A,
                    0x3B,
                    0x3C,
                }:
                    confidence += 0.3
            elif byte == 0x00:  # RETURN:
                # RETURN at end is good
                if i >= len(data) - 2:
                    confidence += 0.3

        # Valid opcode ratio (higher weight for small sections)
        if valid_opcode_count > 0:
            opcode_ratio = valid_opcode_count / len(data)
            confidence += opcode_ratio * 0.4

        # Log the analysis result
        if confidence > 0.3:  # Lower threshold for logging small sections:
            logger.info(
                "Small P-code section detected with confidence %.2f", confidence
            )

        return min(confidence, 1.0)

    @classmethod
    def _verify_pcode_context(cls, data: bytes, offset: int) -> bool:
        """Verify that the context around offset looks like P-code."""
        # Don't just check for non-printable bytes - verify it's not a UTF-16 string
        if cls._is_utf16_string(data, offset):
            return False

        # Check a larger context window
        start = max(0, offset - 10)
        end = min(len(data), offset + 50)
        context = data[start:end]

        # Calculate P-code confidence for the context
        confidence = cls._calculate_pcode_confidence(context)
        return confidence > 0.5

    @classmethod
    def _is_utf16_string(cls, data: bytes, offset: int) -> bool:
        """Check if the data at offset looks like a UTF-16 string.

        UTF-16 strings have alternating null bytes for ASCII characters.
        """
        if offset + 20 > len(data):
            return False

        # Check for UTF-16 LE pattern (common in Windows)
        null_count = 0
        ascii_count = 0

        for i in range(min(20, len(data) - offset)):
            byte = data[offset + i]
            if i % 2 == 1 and byte == 0x00:  # Null byte at odd position
                null_count += 1
            elif i % 2 == 0 and 0x20 <= byte <= 0x7E:  # ASCII at even position
                ascii_count += 1

        # If we have a pattern of ASCII followed by nulls, it's likely UTF-16
        return null_count >= 5 and ascii_count >= 5

    @classmethod
    def _find_text_to_binary_transition(cls, data: bytes) -> int:
        """Find where text/metadata ends and binary P-code begins."""
        # Look for runs of printable ASCII followed by binary data

        in_text = True
        text_run = 0
        binary_run = 0

        for i in range(len(data)):
            if 32 <= data[i] <= 126 or data[i] in [
                9,
                10,
                13,
            ]:  # Printable or whitespace
                if in_text:
                    text_run += 1
                # Transition from binary back to text
                elif binary_run < 4:
                    # Short binary run, probably still in text
                    in_text = True
                    text_run = 1
                    binary_run = 0
            # Non-printable
            elif in_text and text_run > 20:
                # We've had a good run of text, now hitting binary
                in_text = False
                binary_run = 1

                # Check if this looks like P-code start
                if cls._looks_like_pcode(data[i : i + 20]):
                    return i
            elif not in_text:
                binary_run += 1

        return -1

    @classmethod
    def find_pcode_section(
        cls,
        data: bytes,
        object_type: str = "function",
    ) -> tuple[int, int]:
        """Main entry point for P-code detection.

        data: Raw object data
        object_type: Type of object (function, window, etc.)

        Tuple of (offset, length) for P-code section, or (-1, 0) if not found
        """
        # Find all P-code sections
        sections = cls.find_all_pcode_sections(data, object_type)

        if not sections:
            return -1, 0

        # Return the first/main section for backward compatibility
        main_section = sections[0]
        return main_section.offset, main_section.length

    @classmethod
    def find_all_pcode_sections(
        cls, data: bytes, object_type: str = "function"
    ) -> list[PCodeSection]:
        """Find all P-code sections using high-performance O(n) algorithm.

        This method has been optimized to use the high-performance detector
        for significantly improved speed and accuracy.

        Args:
            data: Raw object data
            object_type: Type of object

        Returns:
            List of PCodeSection objects, sorted by offset
        """
        logger.info(
            "High-performance scanning for P-code sections in %d bytes of %s data",
            len(data),
            object_type,
        )

        # Try to use high-performance detector first
        try:
            from .high_performance_detector import HighPerformancePCodeDetector

            detector = HighPerformancePCodeDetector()
            fast_sections = detector.detect_pcode_sections_fast(data)

            # Convert to PCodeSection objects
            sections = []
            for offset, length, confidence in fast_sections:
                sections.append(PCodeSection(offset, length, confidence))

            logger.info(
                "High-performance detector found %d P-code sections (O(n) complexity)",
                len(sections),
            )
            return sections

        except ImportError:
            logger.warning(
                "High-performance detector not available, using legacy O(n²) method"
            )
            return cls._find_all_pcode_sections_legacy(data, object_type)

    @classmethod
    def _find_all_pcode_sections_legacy(
        cls, data: bytes, object_type: str = "function"
    ) -> list[PCodeSection]:
        """Legacy O(n²) method for finding all P-code sections.

        This is the original implementation kept for compatibility.
        """
        logger.info(
            "Legacy scanning for P-code sections in %d bytes of %s data",
            len(data),
            object_type,
        )
        sections = []

        # Handle very small data (2-20 bytes)
        if len(data) < 20:
            if len(data) >= 2:
                # For very small data, analyze the entire thing as one potential section
                confidence = cls._calculate_pcode_confidence(data)
                if confidence > 0.3:  # Lower threshold for small sections
                    sections.append(PCodeSection(0, len(data), confidence))
                    logger.info(
                        "Small data detected as single P-code section with confidence %.2f",
                        confidence,
                    )
            return sections

        # Special handling for export format
        if data.startswith(b"HA$PBExportHeader$"):
            offset, length = cls._handle_export_format(data)
            if offset >= 0:
                sections.append(PCodeSection(offset, length, 1.0))
            return sections

        # Scan entire file for P-code sections with infinite loop protection
        i = 0
        max_iterations = len(data) * 2  # Safety limit to prevent infinite loops
        iterations = 0
        processed_regions = set()  # Track processed regions to avoid re-analysis

        while (
            i <= len(data) - 2 and iterations < max_iterations
        ):  # Need at least 2 bytes for minimal P-code
            iterations += 1

            # Skip UTF-16 strings
            if cls._is_utf16_string(data, i):
                i += 2  # Skip UTF-16 character
                continue

            # Skip regions we've already processed to avoid infinite loops
            if i in processed_regions:
                logger.debug("Skipping already processed region at offset 0x%04x", i)
                i += 4  # Skip ahead by a reasonable amount
                continue

            # Calculate confidence for current position
            # For small data, use all remaining bytes; for large data, use a window
            window_size = min(200, len(data) - i)
            # But ensure we have at least 2 bytes for the confidence calculation
            if window_size < 2:
                break
            confidence = cls._calculate_pcode_confidence(data[i : i + window_size])

            # If we found potential P-code (lower threshold for small sections)
            confidence_threshold = 0.3 if window_size < 10 else 0.6
            if confidence > confidence_threshold:
                # Find the extent of this P-code section
                section_start = i
                section_end = cls._find_pcode_end(data, section_start)
                section_length = section_end - section_start

                # Add this region to processed set
                for offset in range(
                    section_start, min(section_end, section_start + 50)
                ):
                    processed_regions.add(offset)

                # Include sections that are at least 2 bytes (minimum for minimal P-code)
                if section_length >= 2:
                    section = PCodeSection(section_start, section_length, confidence)
                    sections.append(section)
                    logger.info("Found P-code section: %s", section)

                    # Log small sections specifically
                    if section_length < 10:
                        logger.info(
                            "Small P-code section detected: %d bytes at offset 0x%04x",
                            section_length,
                            section_start,
                        )

                    # Ensure we advance past this section by at least 2 bytes
                    i = max(section_end, section_start + 2)
                else:
                    # Section too small, even for minimal P-code
                    logger.debug(
                        "Skipping single-byte section at offset 0x%04x", section_start
                    )
                    # Ensure minimum advance to prevent infinite loop
                    i = max(i + 1, section_start + 2)
            else:
                i += 1

        # Log if we hit the iteration limit (indicates potential infinite loop)
        if iterations >= max_iterations:
            logger.warning(
                "P-code detection hit maximum iteration limit (%d), stopping to prevent infinite loop",
                max_iterations,
            )

        # Sort sections by offset
        sections.sort(key=lambda s: s.offset)

        # Merge adjacent sections if they're close enough
        merged_sections: list[PCodeSection] = []
        for section in sections:
            if (
                merged_sections
                and section.offset
                - (merged_sections[-1].offset + merged_sections[-1].length)
                <= 16
            ):
                # Merge with previous section
                prev = merged_sections[-1]
                prev.length = (section.offset + section.length) - prev.offset
                prev.confidence = max(prev.confidence, section.confidence)
            else:
                merged_sections.append(section)

        logger.info("Found %d P-code sections after merging", len(merged_sections))
        return merged_sections

    def detect_pcode(self, data: bytes, object_name: str) -> PCodeInfo:
        """Detect P-code in raw binary data.

        Args:
            data: Raw binary data from extracted file
            object_name: Name of the object

        Returns:
            PCodeInfo object with detection results
        """
        # Determine object type from name/extension
        object_type = "function"  # Default
        name_lower = object_name.lower()
        if name_lower.endswith(".str"):
            object_type = "structure"
        elif name_lower.endswith((".men", ".srm")):
            object_type = "menu"
        elif name_lower.endswith((".win", ".srw")):
            object_type = "window"
        elif name_lower.endswith((".udo", ".sru")):
            object_type = "userobject"
        elif name_lower.endswith(".sra"):
            object_type = "application"

        # Find all P-code sections
        sections = self.find_all_pcode_sections(data, object_type)

        if not sections:
            logger.warning("No P-code found in %s", object_name)
            return PCodeInfo(
                pcode_offset=-1,
                pcode_length=0,
                object_type=object_type,
                confidence="none",
                sections=[],
            )

        # Calculate overall confidence
        avg_confidence = sum(s.confidence for s in sections) / len(sections)
        if avg_confidence >= 0.8:
            confidence = "high"
        elif avg_confidence >= 0.6:
            confidence = "medium"
        elif avg_confidence >= 0.4:
            confidence = "low"
        else:
            confidence = "none"

        # Use first section as primary for backward compatibility
        main_section = sections[0]

        logger.info(
            "Detected %d P-code sections in %s with %s confidence",
            len(sections),
            object_name,
            confidence,
        )

        return PCodeInfo(
            pcode_offset=main_section.offset,
            pcode_length=main_section.length,
            object_type=object_type,
            confidence=confidence,
            sections=sections,
        )

    @classmethod
    def _find_pcode_end(cls, data: bytes, start_offset: int) -> int:
        """Find the end of executable P-code.

        data: Full data buffer
        start_offset: Where P-code starts

        Offset where P-code ends
        """
        if start_offset < 0 or start_offset >= len(data):
            return len(data)

        i = start_offset
        last_valid_pcode = start_offset
        low_confidence_bytes = 0
        max_scan_length = min(
            2048, len(data) - start_offset
        )  # Limit scan to prevent excessive processing

        while i < len(data) and (i - start_offset) < max_scan_length:
            # Check if we're entering a UTF-16 string region
            if cls._is_utf16_string(data, i):
                # We've hit a string section, P-code ends here
                logger.debug("Found UTF-16 string at 0x%04x, ending P-code section", i)
                return max(
                    last_valid_pcode + 1, start_offset + 1
                )  # Ensure minimum advance

            # Calculate confidence for next chunk
            chunk_size = min(50, len(data) - i)
            if chunk_size < 1:  # Safety check
                break

            confidence = cls._calculate_pcode_confidence(data[i : i + chunk_size])

            if confidence < 0.3:
                low_confidence_bytes += 1
                # If we've had 20+ bytes of low confidence, we're past P-code
                if low_confidence_bytes >= 20:
                    logger.debug(
                        "Low confidence region at 0x%04x, ending P-code section", i
                    )
                    return max(
                        last_valid_pcode + 1, start_offset + 1
                    )  # Ensure minimum advance
            else:
                # Reset counter and update last valid position
                low_confidence_bytes = 0
                last_valid_pcode = i + chunk_size

            # Check for common end-of-code patterns
            if i + 8 <= len(data):
                # Multiple consecutive nulls (but not UTF-16 pattern)
                if data[i : i + 8] == b"\x00" * 8 and not cls._is_utf16_string(data, i):
                    logger.debug("Found null padding at 0x%04x", i)
                    return max(
                        last_valid_pcode + 1, start_offset + 1
                    )  # LOOP SAFETY: Ensure minimum advance

                # Multiple consecutive 0xFF (padding pattern)
                if data[i : i + 8] == b"\xff" * 8:
                    logger.debug("Found 0xFF padding at 0x%04x", i)
                    return max(
                        last_valid_pcode + 1, start_offset + 1
                    )  # LOOP SAFETY: Ensure minimum advance

            # Check for specific end patterns
            # PowerBuilder sometimes uses specific patterns to mark end of code
            end_patterns = [
                b"\x00\x00\x00\x00\xff\xff\xff\xff",  # Common terminator
                b"\xde\xad\xbe\xef",  # Debug marker
                b"END_PCODE",  # Sometimes literal markers
            ]

            for pattern in end_patterns:
                if (
                    i + len(pattern) <= len(data)
                    and data[i : i + len(pattern)] == pattern
                ):
                    logger.debug("Found end pattern %s at 0x%04x", pattern.hex(), i)
                    return max(
                        i, start_offset + 1
                    )  # LOOP SAFETY: Ensure minimum advance

            i += 1

        # FINAL SAFETY: Always return a value greater than start_offset
        # This prevents infinite loops in calling code
        return max(last_valid_pcode + 1, start_offset + 1)

    @classmethod
    def debug_pcode_detection(cls, data: bytes, sections: list[PCodeSection]) -> None:
        """Log detailed information about P-code detection for debugging.

        data: The raw data being analyzed
        sections: Detected P-code sections
        """
        logger.info("=== P-code Detection Debug Info ===")
        logger.info("Total data size: %d bytes (0x%04x)", len(data), len(data))

        if not sections:
            logger.info("No P-code sections detected")

            # Show first 256 bytes for analysis
            logger.debug("First 256 bytes of data:")
            for i in range(0, min(256, len(data)), 16):
                hex_str = " ".join(f"{b:02x}" for b in data[i : i + 16])
                ascii_str = "".join(
                    chr(b) if 32 <= b <= 126 else "." for b in data[i : i + 16]
                )
                logger.debug("  %04x: %-48s  %s", i, hex_str, ascii_str)
        else:
            logger.info("Found %d P-code sections:", len(sections))

            for idx, section in enumerate(sections):
                logger.info(
                    "  Section %d: offset = 0x%04x, length=%d, confidence=%.2f",
                    idx + 1,
                    section.offset,
                    section.length,
                    section.confidence,
                )

                # Show first few bytes of each section
                start = section.offset
                end = min(start + 32, start + section.length, len(data))
                section_data = data[start:end]

                hex_str = " ".join(f"{b:02x}" for b in section_data)
                logger.debug(
                    "    %s%s", hex_str, " ..." if end < start + section.length else ""
                )

                # Try to identify some opcodes
                opcodes_found = []
                for i in range(min(10, len(section_data))):
                    byte = section_data[i]
                    if byte in {0x00, 0x04, 0x05, 0x29, 0x2C, 0x32}:  # Common opcodes
                        opcode_names = {
                            0x00: "RETURN",
                            0x04: "JUMP",
                            0x05: "DBSTART",
                            0x29: "GLOBFUNCCALL",
                            0x2C: "DOTFUNCCALL",
                            0x32: "PUSH_CONST_INT",
                        }
                        opcodes_found.append(
                            f"{opcode_names.get(byte, f'0x{byte:02x}')} at +{i}"
                        )

                if opcodes_found:
                    logger.debug("    Detected opcodes: %s", ", ".join(opcodes_found))

        logger.info("=== End P-code Detection Debug ===")

    @classmethod
    def analyze_data_structure(cls, data: bytes) -> dict[str, object]:
        """Analyze the structure of the data to understand its composition.

        Dictionary with analysis results
        """
        # Initialize counters as integers to avoid type errors
        analysis: dict[str, object] = {
            "total_size": len(data),
            "printable_ascii": 0,
            "utf16_chars": 0,
            "null_bytes": 0,
            "high_bytes": 0,  # bytes > 0x7F
            "potential_opcodes": 0,
            "sections": [],
        }

        # Analyze byte distribution
        byte_stats = cls._analyze_byte_distribution(data)
        analysis.update(byte_stats)

        # Identify major sections
        sections_list = cls._identify_sections(data)
        analysis["sections"] = sections_list
        return analysis

    @classmethod
    def _analyze_byte_distribution(cls, data: bytes) -> dict[str, int]:
        """Analyze the distribution of bytes in the data.

        Dictionary with byte distribution statistics
        """
        stats = {
            "printable_ascii": 0,
            "utf16_chars": 0,
            "null_bytes": 0,
            "high_bytes": 0,
        }
        for i in range(len(data)):
            byte = data[i]

            if byte == 0:
                stats["null_bytes"] += 1
            elif 32 <= byte <= 126:
                stats["printable_ascii"] += 1
            elif byte > 0x7F:
                stats["high_bytes"] += 1

            # Check for UTF-16
            if (
                i % 2 == 0
                and i + 1 < len(data)
                and 32 <= byte <= 126
                and data[i + 1] == 0x00
            ):
                stats["utf16_chars"] += 1

        return stats

    @classmethod
    def _identify_sections(cls, data: bytes) -> list[dict[str, object]]:
        """Identify major sections in the data.

        List of section dictionaries
        """
        current_type: str | None = None
        section_start = 0
        sections_list: list[dict[str, object]] = []

        for i in range(0, len(data), 16):
            chunk = data[i : i + 16]
            chunk_type = cls._determine_chunk_type(data, i, chunk)

            # Track section changes
            if chunk_type != current_type:
                if current_type is not None:
                    sections_list.append(
                        {
                            "type": current_type,
                            "start": section_start,
                            "end": i,
                            "size": i - section_start,
                        }
                    )
                current_type = chunk_type
                section_start = i

        # Add final section
        if current_type is not None:
            sections_list.append(
                {
                    "type": current_type,
                    "start": section_start,
                    "end": len(data),
                    "size": len(data) - section_start,
                }
            )

        return sections_list

    @classmethod
    def _determine_chunk_type(cls, data: bytes, offset: int, chunk: bytes) -> str:
        """Determine the type of a data chunk.

        data: Full data buffer
        offset: Offset of the chunk in data
        chunk: The chunk to analyze

        String identifying the chunk type
        """
        if all(b == 0 for b in chunk):
            return "null_padding"
        if all(b == 0xFF for b in chunk):
            return "ff_padding"
        if cls._is_utf16_string(data, offset):
            return "utf16_string"
        if cls._calculate_pcode_confidence(chunk) > 0.5:
            return "pcode"
        if sum(1 for b in chunk if 32 <= b <= 126) > 12:
            return "ascii_text"
        return "binary_data"
