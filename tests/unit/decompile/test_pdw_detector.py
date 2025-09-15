"""Tests for PDW format detection."""

from src.decompile.pdw.pdw_detector import PDW_SIGNATURES, PDWInfo, detect_pdw_format


class TestPDWDetector:
    """Test cases for PDW format detection."""

    def test_detect_pdw_format_with_signature(self):
        """Test detection of PDW format with known signature."""
        # Test PowerBuilder 10.0 PDW signature
        data = b"PDW1000" + b"\x00" * 100
        result = detect_pdw_format(data)

        assert result is not None
        assert result.is_compiled is True
        assert result.version == "PowerBuilder 10.0"
        assert result.signature == b"PDW1000"

    def test_detect_pdw_format_multiple_versions(self):
        """Test detection of different PowerBuilder versions."""
        test_cases = [
            (b"PDW600", "PowerBuilder 6.0"),
            (b"PDW700", "PowerBuilder 7.0"),
            (b"PDW800", "PowerBuilder 8.0"),
            (b"PDW900", "PowerBuilder 9.0"),
            (b"PDW1000", "PowerBuilder 10.0"),
            (b"PDW1050", "PowerBuilder 10.5"),
            (b"PDW1100", "PowerBuilder 11.0"),
            (b"PDW1150", "PowerBuilder 11.5"),
            (b"PDW1200", "PowerBuilder 12.0"),
            (b"PDW1250", "PowerBuilder 12.5"),
            (b"PDW1260", "PowerBuilder 12.6"),
            (b"PDW1700", "PowerBuilder 17.0"),
            (b"PDW1900", "PowerBuilder 19.0"),
            (b"PDW2100", "PowerBuilder 21.0"),
            (b"PDW2200", "PowerBuilder 22.0"),
        ]

        for signature, expected_version in test_cases:
            data = signature + b"\x00" * 100
            result = detect_pdw_format(data)

            assert result is not None
            assert result.is_compiled is True
            assert result.version == expected_version
            assert result.signature == signature

    def test_detect_pdw_format_no_signature(self):
        """Test detection when no PDW signature is present."""
        # Data without PDW signature
        data = b"PBSELECT(VERSION(400)..." + b"\x00" * 100
        result = detect_pdw_format(data)

        assert result is not None
        assert result.is_compiled is False
        assert result.version is None
        assert result.signature is None

    def test_detect_pdw_format_empty_data(self):
        """Test detection with empty data."""
        result = detect_pdw_format(b"")

        assert result is not None
        assert result.is_compiled is False
        assert result.version is None
        assert result.signature is None

    def test_detect_pdw_format_short_data(self):
        """Test detection with data shorter than signature length."""
        result = detect_pdw_format(b"PDW")

        assert result is not None
        assert result.is_compiled is False
        assert result.version is None
        assert result.signature is None

    def test_pdw_signatures_completeness(self):
        """Test that PDW_SIGNATURES contains expected entries."""
        # Check some key signatures exist
        assert b"PDW600" in PDW_SIGNATURES
        assert b"PDW1000" in PDW_SIGNATURES
        assert b"PDW2200" in PDW_SIGNATURES

        # Check values are strings
        for key, value in PDW_SIGNATURES.items():
            assert isinstance(key, bytes)
            assert isinstance(value, str)
            assert "PowerBuilder" in value

    def test_detect_pdw_format_with_null_bytes(self):
        """Test detection with null bytes in data."""
        # PDW signature followed by null bytes (common pattern)
        data = b"PDW1200" + b"\x00" * 1000
        result = detect_pdw_format(data)

        assert result is not None
        assert result.is_compiled is True
        assert result.version == "PowerBuilder 12.0"

    def test_detect_pdw_format_case_sensitivity(self):
        """Test that detection is case sensitive."""
        # Lower case should not match
        data = b"pdw1000" + b"\x00" * 100
        result = detect_pdw_format(data)

        assert result is not None
        assert result.is_compiled is False  # Should not detect as compiled
        assert result.version is None

    def test_pdw_info_class(self):
        """Test PDWInfo class behavior."""
        # Test default initialization
        info = PDWInfo()
        assert info.is_compiled is False
        assert info.version is None
        assert info.signature is None
        assert info.file_size == 0
        assert info.metadata == {}

        # Test setting fields
        info.is_compiled = True
        info.version = "PowerBuilder 10.0"
        info.signature = b"PDW1000"
        info.file_size = 1000
        info.metadata = {"key": "value"}

        assert info.is_compiled is True
        assert info.version == "PowerBuilder 10.0"
        assert info.signature == b"PDW1000"
        assert info.file_size == 1000
        assert info.metadata == {"key": "value"}
