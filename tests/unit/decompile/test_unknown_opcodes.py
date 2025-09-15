"""Tests for unknown opcode handling."""

from src.decompile.opcodes.unknown import (
    UNKNOWN_OPCODE_DEFINITIONS,
    UNKNOWN_OPCODES,
    get_unknown_opcode_info,
    is_known_unknown,
)


class TestUnknownOpcodes:
    """Test cases for unknown opcode handling."""

    def test_get_unknown_opcode_info_known(self):
        """Test getting info for known unknown opcodes."""
        # Test a few known unknown opcodes
        test_cases = [
            (0x19, "DATA_19", 0, "Unknown data operation"),
            (0x1A, "DATA_1A", 0, "Unknown data operation"),
            (0xC4, "OP_C4", 1, "Unknown operation (1 byte operand)"),
            (0xC6, "VAR_C6", 2, "Unknown variable reference (2 byte operand)"),
            (0xEB, "OP_EB", 0, "Unknown operation"),
        ]

        for opcode, expected_name, expected_operands, expected_desc in test_cases:
            result = get_unknown_opcode_info(opcode)
            assert result is not None
            name, operand_count, description = result
            assert name == expected_name
            assert operand_count == expected_operands
            assert description == expected_desc

    def test_get_unknown_opcode_info_unknown(self):
        """Test getting info for truly unknown opcodes."""
        # Test some opcodes that are not in the unknown list
        unknown_opcodes = [0x00, 0x01, 0xFF, 0x50, 0x60]

        for opcode in unknown_opcodes:
            result = get_unknown_opcode_info(opcode)
            assert result is None

    def test_is_known_unknown_true(self):
        """Test identifying known unknown opcodes."""
        known_unknowns = [
            0x19,
            0x1A,
            0x1B,
            0x1E,
            0x8A,
            0x8B,
            0x90,
            0xC4,
            0xC5,
            0xC6,
            0xC7,
            0xDC,
            0xEA,
            0xEB,
            0xED,
        ]

        for opcode in known_unknowns:
            assert is_known_unknown(opcode) is True

    def test_is_known_unknown_false(self):
        """Test identifying truly unknown opcodes."""
        truly_unknown = [0x00, 0x01, 0xFF, 0x50, 0x60]

        for opcode in truly_unknown:
            assert is_known_unknown(opcode) is False

    def test_unknown_opcodes_structure(self):
        """Test the structure of UNKNOWN_OPCODES dictionary."""
        assert isinstance(UNKNOWN_OPCODES, dict)

        for opcode, name in UNKNOWN_OPCODES.items():
            # Check key is int
            assert isinstance(opcode, int)
            assert 0 <= opcode <= 255  # Valid byte range

            # Check value is string
            assert isinstance(name, str)
            assert name.startswith("UNK_")

    def test_unknown_opcode_definitions_structure(self):
        """Test the structure of UNKNOWN_OPCODE_DEFINITIONS dictionary."""
        assert isinstance(UNKNOWN_OPCODE_DEFINITIONS, dict)

        for opcode, info in UNKNOWN_OPCODE_DEFINITIONS.items():
            # Check key is int
            assert isinstance(opcode, int)
            assert 0 <= opcode <= 255  # Valid byte range

            # Check value is tuple with 3 elements
            assert isinstance(info, tuple)
            assert len(info) == 3

            mnemonic, operand_count, description = info

            # Check mnemonic
            assert isinstance(mnemonic, str)

            # Check operand count
            assert isinstance(operand_count, int)
            assert operand_count >= 0

            # Check description
            assert isinstance(description, str)

    def test_operand_counts(self):
        """Test that operand counts match documented values."""
        expected_operand_counts = {
            0x19: 0,
            0x1A: 0,
            0x1B: 0,
            0x1E: 0,
            0x8A: 1,
            0x8B: 1,
            0x90: 0,
            0xC4: 1,
            0xC5: 1,
            0xC6: 2,
            0xC7: 2,
            0xDC: 0,
            0xEA: 0,
            0xEB: 0,
            0xED: 0,
        }

        for opcode, expected_count in expected_operand_counts.items():
            info = get_unknown_opcode_info(opcode)
            assert info is not None
            _, operand_count, _ = info
            assert operand_count == expected_count

    def test_edge_cases(self):
        """Test edge cases for opcode values."""
        # Test boundary values
        assert is_known_unknown(0x00) is False  # Minimum byte value
        assert is_known_unknown(0xFF) is False  # Maximum byte value

        # Test with invalid types
        # Since the function uses 'in' operator with a dict, None will simply return False
        assert is_known_unknown(None) is False
        assert get_unknown_opcode_info(None) is None

    def test_consistency(self):
        """Test consistency between dictionaries."""
        # All opcodes in UNKNOWN_OPCODES should have definitions
        for opcode in UNKNOWN_OPCODES:
            assert opcode in UNKNOWN_OPCODE_DEFINITIONS
            assert get_unknown_opcode_info(opcode) is not None

        # All opcodes in UNKNOWN_OPCODE_DEFINITIONS should be in UNKNOWN_OPCODES
        for opcode in UNKNOWN_OPCODE_DEFINITIONS:
            assert opcode in UNKNOWN_OPCODES
            assert is_known_unknown(opcode) is True
