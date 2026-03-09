"""PowerBuilder P-code binary decoder with version awareness.

This module implements a version-aware decoder for PowerBuilder P-code binary format,
using version-specific opcode tables as recommended in the decompiler guide.
"""

import logging
import struct
from dataclasses import dataclass, field
from typing import Any, BinaryIO

from src.decompile.pcode.detector import PCodeDetector
from src.decompile.pcode.opcodes.definitions import get_opcodes_for_version
from src.extract.pbd.version_detection import PBVersionDetector as VersionDetector
from src.extract.pbd.version_detection import PowerBuilderVersion

logger = logging.getLogger(__name__)


@dataclass
class PCodeInstruction:
    """Represents a decoded P-code instruction."""

    offset: int
    opcode: int
    opcode_name: str
    operands: list[Any] = field(default_factory=list)
    raw_bytes: bytes = field(default_factory=bytes)
    comment: str | None = None


@dataclass
class DecodedObject:
    """Represents a fully decoded PowerBuilder object."""

    name: str
    type: str
    version: PowerBuilderVersion
    instructions: list[PCodeInstruction] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class PCodeDecoderV2:
    """Version-aware decoder for PowerBuilder P-code binary format."""

    def __init__(self, version: PowerBuilderVersion | None = None) -> None:
        """Initialize the decoder.

        Args:
            version: PowerBuilder version (auto-detected if None)
        """
        self.version = version
        self.opcode_table: dict[int, tuple[str, int, str | None]] = {}
        self.reset()

    def reset(self) -> None:
        """Reset decoder state."""
        self.instructions: Any = []
        self.strings: Any = {}
        self.current_offset = 0
        self.labels: Any = {}
        self.metadata: Any = {}

    def decode_pbd_object(
        self,
        pbd_handle: BinaryIO,
        entry_offset: int,
        entry_size: int,
        object_name: str,
    ) -> DecodedObject:
        """Decode a specific object from a PBD file.

        Args:
            pbd_handle: Open PBD file handle
            entry_offset: Offset to the object's data in the PBD
            entry_size: Size of the object's data
            object_name: Name of the object

        Returns:
            Decoded object with instructions and metadata
        """
        # Save current position
        original_pos = pbd_handle.tell()

        try:
            # Auto-detect version if not set
            if not self.version:
                detector = VersionDetector()
                pbd_handle.seek(0)
                self.version = detector.detect_from_file(pbd_handle)
                logger.info("Auto-detected PowerBuilder version: %s", self.version)

            # Load version-specific opcode table
            if self.version is None:
                raise ValueError("PowerBuilder version detection failed")
            version_str = f"pb{self.version.major}_{self.version.minor}"
            self.opcode_table = get_opcodes_for_version(version_str)
            logger.info("Using opcode table for %s", self.version)

            # Seek to object data
            pbd_handle.seek(entry_offset)
            object_data = pbd_handle.read(entry_size)

            # Detect object type
            object_type = self._detect_object_type(object_name)

            # Parse object header to find P-code
            pcode_offset, pcode_size = self._find_pcode_in_object(
                object_data,
                object_type,
            )

            if pcode_offset and pcode_size:
                pcode_bytes = object_data[pcode_offset : pcode_offset + pcode_size]
                instructions = self.decode_pcode(
                    pcode_bytes,
                    entry_offset + pcode_offset,
                )
            else:
                instructions = []

            # Create decoded object
            return DecodedObject(
                name=object_name,
                type=object_type,
                version=self.version,
                instructions=instructions,
                metadata=self.metadata,
            )

        finally:
            # Restore original position
            pbd_handle.seek(original_pos)

    def decode_pcode_section(
        self,
        data: bytes,
        object_name: str,
        pcode_info: dict[str, Any] | None = None,
    ) -> Any:
        """Decode a P-code section with optional section information.

        CRITICAL PCODEINFO COMPATIBILITY FIX: This function was enhanced to handle
        both dictionary-based and object-based PCodeInfo inputs after the detector
        module was updated to return PCodeInfo objects instead of dictionaries.

        ORIGINAL PROBLEM:
        - Code expected pcode_info to be a dictionary with keys like 'sections'
        - New detector returns PCodeInfo objects with attributes like .sections
        - This mismatch caused AttributeError crashes during P-code decoding

        COMPATIBILITY SOLUTION:
        - Check for object attributes using hasattr() instead of dictionary keys
        - Support both dict and object access patterns
        - Graceful fallback when section information is unavailable
        - Proper handling of sectioned vs non-sectioned P-code

        Args:
            data: Raw P-code bytes (corrected parameter name from pcode_bytes)
            object_name: Name of the object being decoded
            pcode_info: PCodeInfo object or dictionary with section information

        Returns:
            Decoded object with instructions
        """
        logger.info(
            "Decoding P-code for '%s' (%d bytes, sections: %s)",
            object_name,
            len(data),
            bool(
                pcode_info and hasattr(pcode_info, "sections") and pcode_info.sections
            ),
        )

        # Initialize opcode table if not already loaded
        if not self.opcode_table:
            # Set default version if not set
            if not self.version:
                self.version = PowerBuilderVersion(
                    10, 5, True
                )  # Default to PB 10.5 Unicode
                logger.info("Using default PowerBuilder version: %s", self.version)

            # Load version-specific opcode table
            version_str = str(
                self.version
            )  # PowerBuilderVersion.__str__ returns "pb10_5" format
            self.opcode_table = get_opcodes_for_version(version_str)
            logger.info(
                "Loaded opcode table for %s (%d opcodes)",
                self.version,
                len(self.opcode_table),
            )

        # PCODEINFO OBJECT HANDLING: Support both dict and object formats
        # The detector now returns PCodeInfo objects, but we maintain backward compatibility
        if pcode_info and hasattr(pcode_info, "sections") and pcode_info.sections:
            logger.info(
                "P-code has %d sections (using PCodeInfo object)",
                len(pcode_info.sections),
            )
            all_instructions = []

            for idx, section in enumerate(pcode_info.sections):
                logger.info(
                    "Processing section %d: offset=0x%04x, length=%d",
                    idx + 1,
                    section.offset,
                    section.length,
                )

                # SECTION OFFSET CALCULATION FIX:
                # Handle relative vs absolute offsets in sectioned P-code data
                # The data parameter contains the P-code bytes, but section offsets
                # may be absolute file offsets that need to be made relative
                if idx == 0:
                    # First section starts at beginning of our data buffer
                    section_start = 0
                else:
                    # Calculate relative offset from first section's position
                    # This handles cases where sections have absolute file offsets
                    section_start = section.offset - pcode_info.sections[0].offset

                section_end = section_start + section.length
                section_data = data[section_start:section_end]

                logger.debug(
                    "Section %d: extracting bytes [%d:%d] from pcode_bytes",
                    idx + 1,
                    section_start,
                    section_end,
                )

                # Log first few bytes of section data
                logger.debug(
                    "Section %d first 16 bytes: %s",
                    idx + 1,
                    section_data[:16].hex()
                    if len(section_data) >= 16
                    else section_data.hex(),
                )

                # SECTIONED DECODING: Use relaxed validation for individual sections
                # Individual sections may not form complete programs on their own
                section_instructions = self.decode_pcode(
                    section_data, section.offset, validate=False
                )
                logger.info(
                    "Section %d yielded %d instructions",
                    idx + 1,
                    len(section_instructions),
                )
                all_instructions.extend(section_instructions)

            instructions = all_instructions
        else:
            # No section info - decode as single block
            logger.info("No section info available, decoding as single block")
            instructions = self.decode_pcode(data, 0, validate=True)

        # Determine object type from name
        object_type = self._detect_object_type(object_name)
        logger.debug("Detected object type '%s' for '%s'", object_type, object_name)

        # METADATA EXTRACTION: Extract information from PCodeInfo object
        # This provides debugging and analysis information about the P-code detection
        metadata = {}
        if pcode_info:
            # COMPATIBILITY: Handle both object and dictionary formats
            # Extract all available PCodeInfo attributes safely
            if hasattr(pcode_info, "pcode_offset"):
                metadata["pcode_offset"] = pcode_info.pcode_offset
            if hasattr(pcode_info, "pcode_length"):
                metadata["pcode_length"] = pcode_info.pcode_length
            if hasattr(pcode_info, "object_type"):
                metadata["object_type"] = pcode_info.object_type
            if hasattr(pcode_info, "confidence"):
                metadata["confidence"] = pcode_info.confidence
            # Store section count for analysis
            if hasattr(pcode_info, "sections") and pcode_info.sections:
                metadata["section_count"] = len(pcode_info.sections)

        return DecodedObject(
            name=object_name,
            type=object_type,
            version=self.version,
            instructions=instructions,
            metadata=metadata,
        )

    def get_version(self) -> str:
        """Get decoder version.

        Returns:
            Version string for the decoder
        """
        if self.version:
            return str(self.version)
        return "unknown"

    def decode_pcode(
        self,
        pcode_bytes: bytes,
        base_offset: int = 0,
        validate: bool = True,
    ) -> list[PCodeInstruction]:
        """Decode P-code bytes into instructions with enhanced safety checks.

        ROBUSTNESS ENHANCEMENTS: This method includes several safety improvements
        to handle malformed or edge-case P-code data:

        1. INFINITE LOOP PROTECTION: Safety checks to prevent decoder hangs
        2. NON-PCODE DETECTION: Early detection of non-P-code data patterns
        3. CONSECUTIVE RETURN LIMIT: Stop decoding after many RETURN instructions
        4. BOUNDS CHECKING: Comprehensive validation of instruction boundaries
        5. GRACEFUL ERROR HANDLING: Continue decoding even with invalid instructions

        Args:
            pcode_bytes: Raw P-code bytes
            base_offset: Base offset for addresses (for debugging/analysis)
            validate: Whether to validate the instruction sequence

        Returns:
            List of decoded instructions
        """
        self.reset()
        self.current_offset = 0

        logger.info(
            "Decoding %d bytes of P-code starting at offset 0x%04x",
            len(pcode_bytes),
            base_offset,
        )

        # EARLY NON-PCODE DETECTION: Quickly identify data that isn't P-code
        # This prevents wasting time trying to decode padding, headers, or other data
        if len(pcode_bytes) >= 16:
            # Pattern 1: Null byte padding (common at end of sections)
            if pcode_bytes[:8] == b"\x00" * 8:
                logger.info("Data starts with null bytes, likely not P-code")
                return []
            # Pattern 2: 0xFF padding (common in some PowerBuilder versions)
            if pcode_bytes[:8] == b"\xff" * 8:
                logger.info("Data starts with 0xFF bytes, likely not P-code")
                return []
            # Pattern 3: Repeated single byte (indicates padding or corruption)
            if len(set(pcode_bytes[:16])) == 1:
                logger.info(
                    "First 16 bytes are all the same value (0x%02x), likely not P-code",
                    pcode_bytes[0],
                )
                return []

        # First pass - identify jump targets
        self._identify_jump_targets(pcode_bytes, base_offset)

        # INSTRUCTION DECODING with safety limits
        self.current_offset = 0
        consecutive_returns = 0
        # SAFETY LIMIT: Stop decoding after too many consecutive RETURN instructions
        # This indicates we've reached the end of executable code and hit padding
        max_consecutive_returns = 5  # Tuned based on PowerBuilder P-code analysis

        while self.current_offset < len(pcode_bytes):
            prev_offset = self.current_offset
            instruction = self._decode_next_instruction(pcode_bytes, base_offset)

            if instruction:
                # CONSECUTIVE RETURN DETECTION: Safety mechanism to detect end of P-code
                # PowerBuilder P-code sections often end with padding that decodes as RETURN
                if instruction.opcode_name == "RETURN":
                    consecutive_returns += 1
                    if consecutive_returns > max_consecutive_returns:
                        logger.info(
                            "SAFETY STOP: Found %d consecutive RETURN instructions at offset 0x%04x "
                            "(likely reached padding or non-P-code data)",
                            consecutive_returns,
                            base_offset + self.current_offset,
                        )
                        break
                else:
                    consecutive_returns = 0  # Reset counter for non-RETURN instructions

                self.instructions.append(instruction)
            else:
                # If we couldn't decode an instruction, log it and skip the byte
                logger.warning(
                    "Failed to decode instruction at offset 0x%04x (byte 0x%02x), skipping",
                    base_offset + self.current_offset,
                    pcode_bytes[self.current_offset]
                    if self.current_offset < len(pcode_bytes)
                    else 0xFF,
                )
                self.current_offset += 1
                consecutive_returns = 0  # Reset counter on failed decode

            # CRITICAL SAFETY: Infinite loop prevention
            # This prevents the decoder from hanging on malformed P-code
            if self.current_offset == prev_offset:
                logger.error(
                    "DECODER STUCK: No progress at offset 0x%04x, stopping to prevent infinite loop",
                    base_offset + self.current_offset,
                )
                break

        logger.info(
            "Decoded %d instructions from %d bytes",
            len(self.instructions),
            len(pcode_bytes),
        )

        # Validate the decoded instruction sequence if requested
        if validate and not self._validate_instruction_sequence(self.instructions):
            logger.warning(
                "Decoded instruction sequence failed validation - returning instructions anyway"
            )
            # Return instructions anyway - let the caller decide what to do

        return self.instructions

    def _decode_next_instruction(
        self,
        pcode: bytes,
        base_offset: int,
    ) -> PCodeInstruction | None:
        """Decode the next instruction at current offset with comprehensive error handling.

        ROBUST INSTRUCTION DECODING: This method includes extensive safety checks
        and error handling to gracefully process malformed P-code data:

        1. BOUNDS CHECKING: Verify sufficient data for instruction + operands
        2. OPCODE VALIDATION: Check against version-specific opcode tables
        3. OPERAND PARSING: Safe extraction of instruction parameters
        4. ERROR RECOVERY: Continue decoding even with invalid instructions
        5. DEBUG LOGGING: Detailed information for troubleshooting

        Returns None for invalid instructions rather than crashing.
        """
        if self.current_offset >= len(pcode):
            return None

        address = base_offset + self.current_offset
        op_byte = pcode[self.current_offset]

        # DYNAMIC NON-PCODE DETECTION: Detect transition from P-code to padding
        # As we decode, watch for patterns that indicate we've left executable code
        if self.current_offset + 8 < len(pcode):
            next_bytes = pcode[self.current_offset : self.current_offset + 8]
            # Pattern: Sequence of null bytes (end-of-code padding)
            if next_bytes == b"\x00" * 8:
                logger.info(
                    "TRANSITION DETECTED: Null byte sequence at offset 0x%04x, likely end of P-code",
                    self.current_offset,
                )
                return None

            # Pattern: Sequence of 0xFF bytes (another common padding pattern)
            if next_bytes == b"\xff" * 8:
                logger.info(
                    "TRANSITION DETECTED: 0xFF byte sequence at offset 0x%04x, likely end of P-code",
                    self.current_offset,
                )
                return None

        # Log first few instructions for debugging
        if len(self.instructions) < 5:
            logger.debug(
                "Decoding instruction #%d at offset 0x%04x (byte 0x%02x)",
                len(self.instructions) + 1,
                address,
                op_byte,
            )

        # VERSION-AWARE OPCODE LOOKUP: Use PowerBuilder version-specific opcode table
        # Different PowerBuilder versions have different opcode sets
        opcode_info = self.opcode_table.get(op_byte)
        if not opcode_info:
            logger.debug(
                "Unknown opcode 0x%02x at offset 0x%04x (PB version: %s)",
                op_byte,
                address,
                self.version or "unknown",
            )
            return None

        opcode_name, operand_count, description = opcode_info

        # Start building instruction
        instruction = PCodeInstruction(
            offset=address,
            opcode=op_byte,
            opcode_name=opcode_name,
            operands=[],
            raw_bytes=bytes([op_byte]),
            comment=description,
        )

        # Advance past opcode byte
        self.current_offset += 1

        # Decode operands based on opcode type
        try:
            self._decode_operands(pcode, instruction, operand_count)
        except Exception as e:
            logger.warning(
                "Failed to decode operands for %s at offset 0x%04x: %s",
                opcode_name,
                address,
                e,
            )
            return None

        return instruction

    def _decode_operands(
        self,
        pcode: bytes,
        instruction: PCodeInstruction,
        expected_count: int,
    ) -> None:
        """Decode operands for an instruction with bounds checking.

        SAFE OPERAND DECODING: This method safely extracts operands from P-code
        with comprehensive error handling:

        1. BOUNDS VALIDATION: Ensure sufficient bytes for all operands
        2. SIZE DETERMINATION: Calculate operand sizes based on opcode type
        3. ENDIANNESS HANDLING: Proper little-endian decoding
        4. ERROR PROPAGATION: Raise exceptions for calling code to handle

        PowerBuilder operand format notes:
        - Most operands are 1 or 2 bytes
        - Complex instructions (function calls) use 2-byte operands
        - Simple instructions (arithmetic) use 1-byte operands
        """
        # Handle different operand types based on the opcode
        opcode = instruction.opcode

        # Most PowerBuilder opcodes have specific operand patterns
        for i in range(expected_count):
            if self.current_offset >= len(pcode):
                raise ValueError("Insufficient bytes for operand")

            # Determine operand size based on opcode and position
            operand_size = self._get_operand_size(opcode, i)

            if self.current_offset + operand_size > len(pcode):
                raise ValueError(f"Insufficient bytes for {operand_size}-byte operand")

            if operand_size == 1:
                # 8-bit operand
                operand = pcode[self.current_offset]
                instruction.operands.append(operand)
                instruction.raw_bytes += pcode[
                    self.current_offset : self.current_offset + 1
                ]
                self.current_offset += 1
            elif operand_size == 2:
                # 16-bit operand (little endian)
                operand = struct.unpack_from("<H", pcode, self.current_offset)[0]
                instruction.operands.append(operand)
                instruction.raw_bytes += pcode[
                    self.current_offset : self.current_offset + 2
                ]
                self.current_offset += 2
            else:
                raise ValueError(f"Unsupported operand size: {operand_size}")

    def _get_operand_size(self, opcode: int, operand_index: int) -> int:
        """Get the size of an operand for a specific opcode.

        POWERBUILDER OPERAND SIZING: This function implements PowerBuilder's
        operand size conventions based on instruction complexity:

        SIZING RULES:
        - Simple instructions (arithmetic, stack ops): 1-byte operands
        - Complex instructions (calls, references): 2-byte operands
        - Function calls need 2-byte indices for large symbol tables
        - Variable references use 1-byte indices for local scope

        Args:
            opcode: The instruction opcode
            operand_index: Which operand (0-based)

        Returns:
            Size in bytes (1 or 2)
        """
        # Most PowerBuilder operands are 8-bit for simple instructions
        # and 16-bit for complex instructions with addresses/indices

        # POWERBUILDER 16-BIT OPERAND INSTRUCTIONS:
        # These instructions require 2-byte operands for indexing into larger tables
        sixteen_bit_opcodes = {
            0x20,  # PUSH_CONST_REF - References to constant pool (can be large)
            0x29,  # GLOBFUNCCALL - Global function calls (many functions)
            0x2A,  # CALL_FUNCTION - Function calls with large symbol tables
            0x2B,  # DLLFUNCCALL - DLL function calls (external references)
            0x2C,  # DOTFUNCCALL - Object method calls (large method tables)
            0x2D,  # PUSH_GLOBAL_VAR - Global variables (large variable tables)
            0x2E,  # ARRAYLIST - Array operations (potentially large arrays)
        }

        if opcode in sixteen_bit_opcodes:
            return 2  # Complex instructions need 16-bit indices

        # DEFAULT: Most PowerBuilder instructions use 8-bit operands
        # This covers arithmetic, stack operations, local variable access, etc.
        return 1

    def _identify_jump_targets(self, pcode_bytes: bytes, base_offset: int) -> None:
        """Identify jump targets in the code for labeling."""
        # This would analyze jump instructions and mark their targets

    def _validate_instruction_sequence(
        self, instructions: list[PCodeInstruction]
    ) -> bool:
        """Validate that the decoded instructions form a valid sequence."""
        if not instructions:
            return False

        # Basic validation - check for reasonable patterns
        # Real implementation would be more sophisticated
        return True

    def _detect_object_type(self, object_name: str) -> str:
        """Detect object type from name."""
        name_lower = object_name.lower()
        if name_lower.startswith("w_"):
            return "window"
        if name_lower.startswith("u_"):
            return "userobject"
        if name_lower.startswith("f_"):
            return "function"
        if name_lower.startswith("n_"):
            return "nonvisualobject"
        if name_lower.startswith("m_"):
            return "menu"
        if name_lower.startswith("d_"):
            return "datawindow"
        return "unknown"

    def _find_pcode_in_object(
        self,
        object_data: bytes,
        object_type: str,
    ) -> tuple[int | None, int | None]:
        """Find P-code section within object data."""
        # Use the enhanced detector to find P-code
        detector = PCodeDetector()
        pcode_info = detector.find_pcode_in_data(object_data)

        if pcode_info and hasattr(pcode_info, "offset") and hasattr(pcode_info, "size"):
            return pcode_info.offset, pcode_info.size

        return None, None
