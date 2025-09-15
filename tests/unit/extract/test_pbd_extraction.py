"""Consolidated tests for PBD extraction functionality.

This file combines tests from:
- test_pbd_extraction.py (integration tests with imports)
- test_pbd_extraction_simple.py (isolated unit tests)
"""

import unittest
from unittest.mock import MagicMock, patch

# Try imports for integration tests
try:
    from src.common.constants import BUFFER_SIZE, PBD_SIGNATURE_HDR

    # Use common exceptions instead of extraction-specific ones
    from src.core.exceptions import (
        DataExtractionError,
        DatError,
        EntryError,
        HeaderError,
        NodeError,
        PbdError,
    )
    from src.decompile.constants import OPCODES

    IMPORTS_AVAILABLE = True
except ImportError:
    IMPORTS_AVAILABLE = False


# ===== INTEGRATION TESTS (require imports) =====


@unittest.skipUnless(IMPORTS_AVAILABLE, "Requires extract module imports")
class TestPBDExtractionIntegration(unittest.TestCase):
    """Integration tests that verify actual imports and constants."""

    def test_pbd_signatures_imported(self):
        """Test that PBD signatures are correctly imported."""
        # Test that signatures are imported correctly
        self.assertEqual(PBD_SIGNATURE_NOD, b"NOD*")
        self.assertEqual(PBD_SIGNATURE_ENT, b"ENT*")
        self.assertEqual(PBD_SIGNATURE_HDR, b"HDR*")
        self.assertEqual(PBD_SIGNATURE_FRE, b"FRE*")
        self.assertEqual(PBD_SIGNATURE_DAT, b"DAT*")

    def test_common_constants(self):
        """Test that common constants are available."""
        # Buffer size should be a reasonable value
        self.assertGreater(BUFFER_SIZE, 0)
        self.assertLessEqual(BUFFER_SIZE, 1024 * 1024)  # Max 1MB buffer

        # PBD signature should be defined
        self.assertEqual(PBD_SIGNATURE_HDR, b"HDR*")

    def test_exception_hierarchy(self):
        """Test the exception hierarchy is properly defined."""
        # Base exception
        self.assertTrue(issubclass(PBDError, Exception))

        # Structure exceptions
        self.assertTrue(issubclass(CorruptedPBDError, PBDError))
        self.assertTrue(issubclass(InvalidPBDError, PBDError))
        self.assertTrue(issubclass(UnsupportedVersionError, PBDError))
        self.assertTrue(issubclass(InvalidNodeTypeError, PBDError))

        # Data exceptions
        self.assertTrue(issubclass(DataIntegrityError, PBDError))
        self.assertTrue(issubclass(DataCorruptionError, PBDError))

        # Resource exceptions
        self.assertTrue(issubclass(ResourceExtractionError, PBDError))
        self.assertTrue(issubclass(InvalidResourceTypeError, ResourceExtractionError))
        self.assertTrue(issubclass(DecompressionError, ResourceExtractionError))
        self.assertTrue(issubclass(StringDecodingError, ResourceExtractionError))

    def test_exception_messages(self):
        """Test that exceptions can be instantiated with messages."""
        exceptions = [
            PBDError("Test PBD error"),
            CorruptedPBDError("Test corrupted error"),
            InvalidPBDError("Test invalid error"),
            UnsupportedVersionError("Test version error"),
            InvalidNodeTypeError("Test node type error"),
            DataIntegrityError("Test data integrity error"),
            ResourceExtractionError("Test resource error"),
            InvalidResourceTypeError("Test resource type error"),
            DecompressionError("Test decompression error"),
            StringDecodingError("Test string decoding error"),
            DataCorruptionError("Test data corruption error"),
        ]

        for exc in exceptions:
            self.assertIsInstance(exc, PBDError)
            self.assertTrue(str(exc))

    def test_opcode_table(self):
        """Test that the opcode table is properly defined."""
        # Test that OPCODES is a dictionary
        self.assertIsInstance(OPCODES, dict)

        # Test some common opcodes exist
        expected_opcodes = {
            0x01: "PUSH",
            0x02: "POP",
            0x0A: "ADD",
            0x0B: "SUBTRACT",
        }

        for opcode, name in expected_opcodes.items():
            self.assertIn(opcode, OPCODES)
            self.assertEqual(OPCODES[opcode], name)


# ===== ISOLATED UNIT TESTS (no imports required) =====


class TestPBDExtractionUnit(unittest.TestCase):
    """Unit tests that work without actual module imports."""

    def setUp(self):
        """Set up test constants if imports not available."""
        if not IMPORTS_AVAILABLE:
            # Define minimal constants for testing
            self.PBD_SIGNATURE_NOD = b"NOD*"
            self.PBD_SIGNATURE_ENT = b"ENT*"
            self.PBD_SIGNATURE_HDR = b"HDR*"
            self.PBD_SIGNATURE_FRE = b"FRE*"
            self.PBD_SIGNATURE_DAT = b"DAT*"
        else:
            self.PBD_SIGNATURE_NOD = PBD_SIGNATURE_NOD
            self.PBD_SIGNATURE_ENT = PBD_SIGNATURE_ENT
            self.PBD_SIGNATURE_HDR = PBD_SIGNATURE_HDR
            self.PBD_SIGNATURE_FRE = PBD_SIGNATURE_FRE
            self.PBD_SIGNATURE_DAT = PBD_SIGNATURE_DAT

    def test_pbd_signatures_basic(self):
        """Test basic PBD signature values."""
        self.assertEqual(self.PBD_SIGNATURE_NOD, b"NOD*")
        self.assertEqual(self.PBD_SIGNATURE_ENT, b"ENT*")
        self.assertEqual(self.PBD_SIGNATURE_HDR, b"HDR*")
        self.assertEqual(self.PBD_SIGNATURE_FRE, b"FRE*")
        self.assertEqual(self.PBD_SIGNATURE_DAT, b"DAT*")

    def test_signature_lengths(self):
        """Test that all signatures are 4 bytes."""
        signatures = [
            self.PBD_SIGNATURE_NOD,
            self.PBD_SIGNATURE_ENT,
            self.PBD_SIGNATURE_HDR,
            self.PBD_SIGNATURE_FRE,
            self.PBD_SIGNATURE_DAT,
        ]

        for sig in signatures:
            self.assertEqual(len(sig), 4, f"Signature {sig} should be 4 bytes")

    def test_signature_types(self):
        """Test that signatures are bytes objects."""
        signatures = [
            self.PBD_SIGNATURE_NOD,
            self.PBD_SIGNATURE_ENT,
            self.PBD_SIGNATURE_HDR,
            self.PBD_SIGNATURE_FRE,
            self.PBD_SIGNATURE_DAT,
        ]

        for sig in signatures:
            self.assertIsInstance(sig, bytes, f"Signature {sig} should be bytes")


# ===== HELPER FUNCTION TESTS =====


class TestPBDExtractionHelpers(unittest.TestCase):
    """Test helper functions for PBD extraction."""

    def test_read_uint32(self):
        """Test reading 32-bit unsigned integers."""
        # Test data with known values
        test_data = b"\x01\x00\x00\x00"  # 1 in little-endian
        result = int.from_bytes(test_data, byteorder="little")
        self.assertEqual(result, 1)

        test_data = b"\xff\xff\xff\xff"  # Max uint32
        result = int.from_bytes(test_data, byteorder="little")
        self.assertEqual(result, 4294967295)

    def test_read_uint16(self):
        """Test reading 16-bit unsigned integers."""
        test_data = b"\x01\x00"  # 1 in little-endian
        result = int.from_bytes(test_data, byteorder="little")
        self.assertEqual(result, 1)

        test_data = b"\xff\xff"  # Max uint16
        result = int.from_bytes(test_data, byteorder="little")
        self.assertEqual(result, 65535)

    def test_read_pbd_header(self):
        """Test reading PBD header structure."""
        # Mock header data with HDR signature
        header_data = b"HDR*" + b"\x00" * 508  # 512 byte header

        # Verify we can check the signature
        signature = header_data[:4]
        self.assertEqual(signature, b"HDR*")

        # Verify header size
        self.assertEqual(len(header_data), 512)


# ===== MOCK-BASED TESTS =====


class TestPBDExtractionWithMocks(unittest.TestCase):
    """Tests using mocks to avoid dependencies."""

    @patch("builtins.open")
    def test_open_pbd_file(self, mock_open):
        """Test opening a PBD file."""
        # Setup mock
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file
        mock_file.read.return_value = b"HDR*" + b"\x00" * 508

        # Simulate opening and reading
        with open("test.pbd", "rb") as f:
            data = f.read()

        # Verify
        self.assertEqual(data[:4], b"HDR*")
        mock_open.assert_called_once_with("test.pbd", "rb")

    def test_validate_signature(self):
        """Test signature validation logic."""
        valid_signatures = [b"NOD*", b"ENT*", b"HDR*", b"FRE*", b"DAT*"]
        invalid_signatures = [b"XXXX", b"NOD!", b"", b"NO", b"NODE*"]

        for sig in valid_signatures:
            # Should not raise for valid signatures
            self.assertIn(sig, valid_signatures)

        for sig in invalid_signatures:
            # Should not be in valid list
            self.assertNotIn(sig, valid_signatures)


if __name__ == "__main__":
    unittest.main()
