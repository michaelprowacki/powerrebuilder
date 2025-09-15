"""PowerBuilder opcode variant handling.

This module handles opcodes that have different behaviors based on context or variant bytes.
Some opcodes like DBFETCH (0x0E) and DBINSERT (0x0F) have variant bytes that modify their behavior.
"""

import logging
import struct
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class OpcodeVariant:
    """Represents an opcode variant with its specific behavior."""

    base_opcode: int
    variant_byte: int | None
    name: str
    operand_count: int
    description: str


# Known opcode variants from analysis
OPCODE_VARIANTS: dict[int, list[OpcodeVariant]] = {
    # DBFETCH (0x0E) variants
    0x0E: [
        OpcodeVariant(0x0E, 0x00, "DBFETCH", 4, "Standard DBFETCH"),
        OpcodeVariant(0x0E, 0x04, "DBFETCH_VAR_04", 4, "DBFETCH variant 04"),
        OpcodeVariant(0x0E, 0x09, "DBFETCH_VAR_09", 4, "DBFETCH variant 09"),
        OpcodeVariant(0x0E, 0x14, "DBFETCH_VAR_14", 4, "DBFETCH variant 14"),
        OpcodeVariant(0x0E, 0x1A, "DBFETCH_VAR_1A", 4, "DBFETCH variant 1A"),
        OpcodeVariant(0x0E, 0x40, "DBFETCH_VAR_40", 4, "DBFETCH variant 40"),
        OpcodeVariant(0x0E, 0x44, "DBFETCH_VAR_44", 4, "DBFETCH variant 44"),
        OpcodeVariant(0x0E, 0x49, "DBFETCH_VAR_49", 4, "DBFETCH variant 49"),
        OpcodeVariant(0x0E, 0x4E, "DBFETCH_VAR_4E", 4, "DBFETCH variant 4E"),
        OpcodeVariant(0x0E, 0x4F, "DBFETCH_VAR_4F", 4, "DBFETCH variant 4F"),
        OpcodeVariant(0x0E, 0x54, "DBFETCH_VAR_54", 4, "DBFETCH variant 54"),
        OpcodeVariant(0x0E, 0x59, "DBFETCH_VAR_59", 4, "DBFETCH variant 59"),
        OpcodeVariant(0x0E, 0x5E, "DBFETCH_VAR_5E", 4, "DBFETCH variant 5E"),
        OpcodeVariant(0x0E, 0x5F, "DBFETCH_VAR_5F", 4, "DBFETCH variant 5F"),
        OpcodeVariant(0x0E, 0x80, "DBFETCH_VAR_80", 4, "DBFETCH variant 80"),
        OpcodeVariant(0x0E, 0x84, "DBFETCH_VAR_84", 4, "DBFETCH variant 84"),
        OpcodeVariant(0x0E, 0x89, "DBFETCH_VAR_89", 4, "DBFETCH variant 89"),
        OpcodeVariant(0x0E, 0x8E, "DBFETCH_VAR_8E", 4, "DBFETCH variant 8E"),
        OpcodeVariant(0x0E, 0x8F, "DBFETCH_VAR_8F", 4, "DBFETCH variant 8F"),
        OpcodeVariant(0x0E, 0x94, "DBFETCH_VAR_94", 4, "DBFETCH variant 94"),
        OpcodeVariant(0x0E, 0x99, "DBFETCH_VAR_99", 4, "DBFETCH variant 99"),
        OpcodeVariant(0x0E, 0x9E, "DBFETCH_VAR_9E", 4, "DBFETCH variant 9E"),
        OpcodeVariant(0x0E, 0x9F, "DBFETCH_VAR_9F", 4, "DBFETCH variant 9F"),
        OpcodeVariant(0x0E, 0xC0, "DBFETCH_VAR_C0", 4, "DBFETCH variant C0"),
        OpcodeVariant(0x0E, 0xC4, "DBFETCH_VAR_C4", 4, "DBFETCH variant C4"),
        OpcodeVariant(0x0E, 0xC5, "DBFETCH_VAR_C5", 4, "DBFETCH variant C5"),
        OpcodeVariant(0x0E, 0xC6, "DBFETCH_VAR_C6", 4, "DBFETCH variant C6"),
    ],  # DBINSERT (0x0F) variants
    0x0F: [
        OpcodeVariant(0x0F, 0x00, "DBINSERT", 4, "Standard DBINSERT"),
        OpcodeVariant(0x0F, 0x04, "DBINSERT_VAR_04", 4, "DBINSERT variant 04"),
        OpcodeVariant(0x0F, 0x09, "DBINSERT_VAR_09", 4, "DBINSERT variant 09"),
        OpcodeVariant(0x0F, 0x14, "DBINSERT_VAR_14", 4, "DBINSERT variant 14"),
        OpcodeVariant(0x0F, 0x40, "DBINSERT_VAR_40", 4, "DBINSERT variant 40"),
        OpcodeVariant(0x0F, 0x44, "DBINSERT_VAR_44", 4, "DBINSERT variant 44"),
        OpcodeVariant(0x0F, 0x49, "DBINSERT_VAR_49", 4, "DBINSERT variant 49"),
        OpcodeVariant(0x0F, 0x4E, "DBINSERT_VAR_4E", 4, "DBINSERT variant 4E"),
        OpcodeVariant(0x0F, 0x4F, "DBINSERT_VAR_4F", 4, "DBINSERT variant 4F"),
        OpcodeVariant(0x0F, 0x54, "DBINSERT_VAR_54", 4, "DBINSERT variant 54"),
        OpcodeVariant(0x0F, 0x59, "DBINSERT_VAR_59", 4, "DBINSERT variant 59"),
        OpcodeVariant(0x0F, 0x5E, "DBINSERT_VAR_5E", 4, "DBINSERT variant 5E"),
        OpcodeVariant(0x0F, 0x5F, "DBINSERT_VAR_5F", 4, "DBINSERT variant 5F"),
        OpcodeVariant(0x0F, 0x80, "DBINSERT_VAR_80", 4, "DBINSERT variant 80"),
        OpcodeVariant(0x0F, 0x84, "DBINSERT_VAR_84", 4, "DBINSERT variant 84"),
        OpcodeVariant(0x0F, 0x89, "DBINSERT_VAR_89", 4, "DBINSERT variant 89"),
        OpcodeVariant(0x0F, 0x8E, "DBINSERT_VAR_8E", 4, "DBINSERT variant 8E"),
        OpcodeVariant(0x0F, 0x8F, "DBINSERT_VAR_8F", 4, "DBINSERT variant 8F"),
        OpcodeVariant(0x0F, 0x94, "DBINSERT_VAR_94", 4, "DBINSERT variant 94"),
        OpcodeVariant(0x0F, 0x99, "DBINSERT_VAR_99", 4, "DBINSERT variant 99"),
        OpcodeVariant(0x0F, 0x9E, "DBINSERT_VAR_9E", 4, "DBINSERT variant 9E"),
        OpcodeVariant(0x0F, 0x9F, "DBINSERT_VAR_9F", 4, "DBINSERT variant 9F"),
        OpcodeVariant(0x0F, 0xC0, "DBINSERT_VAR_C0", 4, "DBINSERT variant C0"),
        OpcodeVariant(0x0F, 0xC4, "DBINSERT_VAR_C4", 4, "DBINSERT variant C4"),
        OpcodeVariant(0x0F, 0xC5, "DBINSERT_VAR_C5", 4, "DBINSERT variant C5"),
        OpcodeVariant(0x0F, 0xC6, "DBINSERT_VAR_C6", 4, "DBINSERT variant C6"),
    ],
}


def get_opcode_variant(
    base_opcode: int, data: bytes, offset: int
) -> OpcodeVariant | None:
    """Get the opcode variant based on the base opcode and following bytes.

    Args:
        base_opcode: The base opcode value
        data: The full P-code data
        offset: Current offset in the data (pointing to the opcode)

    Returns:
        OpcodeVariant if a variant is found, None otherwise
    """
    if base_opcode not in OPCODE_VARIANTS:
        return None

    # Check if we have enough data for variant byte
    if offset + 1 >= len(data):
        return None

    variant_byte = data[offset + 1]

    # Look for matching variant
    for variant in OPCODE_VARIANTS[base_opcode]:
        if variant.variant_byte == variant_byte:
            return variant

    # Return default variant if no specific match
    for variant in OPCODE_VARIANTS[base_opcode]:
        if variant.variant_byte == 0x00:
            return variant

    return None


def decode_variant_operands(
    variant: OpcodeVariant, operand_bytes: bytes
) -> tuple[str, list[str]] | None:
    """Decode operands for a specific variant.

    Args:
        variant: The opcode variant
        operand_bytes: The operand bytes (excluding the variant byte)

    Returns:
        Tuple of (formatted_string, operand_values) or None if decoding fails
    """
    # The variant byte is typically followed by standard operands
    # For database operations, this is often:
    # - 2 bytes: cursor/statement ID
    # - Additional bytes: column indices or other parameters

    if len(operand_bytes) < 2:
        return None

    values: list[str] = []

    # First 2 bytes are typically the cursor/statement ID
    cursor_id = struct.unpack("<H", operand_bytes[:2])[0]
    values.append(f"cursor={cursor_id}")

    # Remaining bytes depend on the variant
    if len(operand_bytes) > 2:
        remaining = operand_bytes[2:]

        # Variant-specific decoding
        variant_hex = variant.variant_byte if variant.variant_byte is not None else 0

        # Bitfield analysis of variant byte
        if variant_hex & 0x80:  # High bit set
            values.append("HIGH_BIT")
        if variant_hex & 0x40:
            values.append("BIT_6")
        if variant_hex & 0x20:
            values.append("BIT_5")
        if variant_hex & 0x10:
            values.append("BIT_4")

        # Low nibble often indicates data type or operation mode
        low_nibble = variant_hex & 0x0F
        if low_nibble == 0x04:
            values.append("TYPE_4")
        elif low_nibble == 0x09:
            values.append("TYPE_9")
        elif low_nibble == 0x0E:
            values.append("TYPE_E")
        elif low_nibble == 0x0F:
            values.append("TYPE_F")

        # Add remaining bytes as hex
        if remaining:
            values.append(f"data={remaining.hex()}")

    formatted = f"{variant.name}({', '.join(values)})"
    return formatted, values


def handle_variant_opcode(
    opcode: int, data: bytes, offset: int
) -> tuple[str, int, list[str]] | None:
    """Handle an opcode that may have variants.

    Args:
        opcode: The opcode value
        data: The full P-code data
        offset: Current offset in the data

    Returns:
        Tuple of (mnemonic, total_bytes_consumed, operand_values) or None
    """
    variant = get_opcode_variant(opcode, data, offset)
    if variant is None:
        return None

    # Calculate how many bytes to read
    # Variant byte + remaining operands
    total_bytes = 1 + variant.operand_count  # opcode + variant + operands

    if offset + total_bytes > len(data):
        logger.warning(
            "Insufficient data for variant opcode 0x%02X at offset %d",
            opcode,
            offset,
        )
        return None

    # Extract operand bytes (excluding opcode and variant byte)
    operand_bytes = data[offset + 2 : offset + total_bytes]

    # Decode the operands
    result = decode_variant_operands(variant, operand_bytes)
    if result is None:
        return None

    formatted, values = result
    return variant.name, total_bytes, values
