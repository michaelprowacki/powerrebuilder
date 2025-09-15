#!/usr/bin/env python3
"""Test entry parsing functionality in PBD extraction."""

import datetime
import struct
from pathlib import Path

from src.extract.pbd.data_block import extract_data_from_entry
from src.extract.pbd.entry import (
    PbEntryDefinition,
    extract_entry_def,
    extract_entry_def_unicode,
    read_and_parse_entry_def,
)


class TestEntryParsing:
    """Test entry definition extraction and parsing."""

    def test_extract_entry_def_valid(self):
        """Test extracting valid entry definition."""
        # Create valid ENT* entry data
        entry_data = b"ENT*"  # Signature
        entry_data += b"10.0"  # Version (4 bytes)
        entry_data += struct.pack("<I", 1000)  # Offset
        entry_data += struct.pack("<I", 2000)  # Object size
        entry_data += struct.pack("<I", 1234567890)  # Modification time
        entry_data += struct.pack("<H", 10)  # Comment length
        entry_data += struct.pack("<H", 8)  # Object name length
        entry_data += b"n_test.u"  # Object name

        result = extract_entry_def(entry_data)

        assert result is not None
        assert result.objectname == "n_test.u"
        assert result.version == "10.0"
        assert result.offset == 1000
        assert result.objectsize == 2000
        assert result.commentlen == 10
        assert result.objnamelen == 8

    def test_extract_entry_def_invalid_signature(self):
        """Test extraction with invalid signature."""
        # Create entry with wrong signature
        entry_data = b"BAD*"  # Wrong signature
        entry_data += b"10.0" + b"\x00" * 20

        result = extract_entry_def(entry_data)

        assert result is None

    def test_extract_entry_def_short_data(self):
        """Test extraction with data too short."""
        # Less than 24 bytes (FIXED_PART_LEN)
        entry_data = b"ENT*" + b"10.0"

        result = extract_entry_def(entry_data)

        assert result is None

    def test_extract_entry_def_truncated_name(self):
        """Test extraction with truncated object name."""
        # Create entry claiming name is longer than available data
        entry_data = b"ENT*"  # Signature
        entry_data += b"10.0"  # Version
        entry_data += struct.pack("<I", 1000)  # Offset
        entry_data += struct.pack("<I", 2000)  # Object size
        entry_data += struct.pack("<I", 1234567890)  # Modification time
        entry_data += struct.pack("<H", 10)  # Comment length
        entry_data += struct.pack("<H", 20)  # Object name length (claims 20 bytes)
        entry_data += b"short"  # But only 5 bytes available

        result = extract_entry_def(entry_data)

        # Should still parse but mark as truncated
        assert result is not None
        assert "<TRUNCATED>" in result.objectname

    def test_extract_entry_def_unicode_valid(self):
        """Test extracting valid Unicode entry definition."""
        # Create valid Unicode ENT* entry (48 bytes fixed part)
        entry_data = b"E\x00N\x00T\x00*\x00"  # Unicode signature (8 bytes)
        # Version string must be exactly 8 bytes, pad with nulls
        version_bytes = b"1\x000\x00.\x000\x00"  # "10.0" in UTF-16 LE
        entry_data += version_bytes.ljust(8, b"\x00")  # Pad to 8 bytes
        entry_data += struct.pack("<Q", 1000)  # Offset (8 bytes, 64-bit)
        entry_data += struct.pack("<Q", 2000)  # Object size (8 bytes, 64-bit)
        entry_data += struct.pack("<Q", 1234567890)  # Mod time (8 bytes, 64-bit)
        entry_data += struct.pack("<I", 10)  # Comment length (4 bytes)
        entry_data += struct.pack("<I", 8)  # Object name length in CHARACTERS (4 bytes)
        # Total: 48 bytes
        # Add Unicode object name (8 characters = 16 bytes)
        entry_data += b"n\x00_\x00t\x00e\x00s\x00t\x00.\x00u\x00"

        result = extract_entry_def_unicode(entry_data)

        assert result is not None
        assert result.objectname == "n_test.u"
        assert result.version == "10.0"

    def test_extract_entry_def_unicode_with_ascii_signature(self):
        """Test Unicode entry with ASCII signature (fallback)."""
        # Import the specific function for ASCII sig with Unicode data
        from src.extract.pbd.entry import (
            extract_entry_def_ascii_sig_unicode_data,
        )

        # Some Unicode PBD files use ASCII signatures
        # This format is 28 bytes header + Unicode name
        entry_data = b"ENT*"  # ASCII signature (4 bytes)
        # Version must be exactly 8 bytes
        version_bytes = b"1\x000\x00.\x000\x00"  # "10.0" in UTF-16 LE
        entry_data += version_bytes.ljust(8, b"\x00")  # Pad to 8 bytes
        entry_data += struct.pack("<I", 1000)  # Offset (4 bytes)
        entry_data += struct.pack("<I", 2000)  # Object size (4 bytes)
        entry_data += struct.pack("<I", 1234567890)  # Modification time (4 bytes)
        entry_data += struct.pack("<H", 0)  # Comment length in bytes (2 bytes)
        entry_data += struct.pack("<H", 16)  # Object name length in bytes (2 bytes)
        # Total: 28 bytes
        entry_data += (
            b"n\x00_\x00t\x00e\x00s\x00t\x00.\x00u\x00"  # Unicode name (16 bytes)
        )

        result = extract_entry_def_ascii_sig_unicode_data(entry_data)

        assert result is not None
        assert result.objectname == "n_test.u"
        assert result.version == "10.0"
        assert result.offset == 1000
        assert result.objectsize == 2000

    def test_extract_entry_def_invalid_data(self):
        """Test extraction with corrupted data."""
        # Create entry with invalid structure
        entry_data = b"ENT*"
        entry_data += b"10.0"
        entry_data += b"\xff" * 16  # Invalid binary data

        result = extract_entry_def(entry_data)

        # Should handle gracefully
        assert result is None or isinstance(result, PbEntryDefinition)


class TestReadAndParseEntry:
    """Test read_and_parse_entry_def function."""

    def test_read_and_parse_entry_def_ascii(self):
        """Test reading and parsing ASCII entry from file."""
        import tempfile

        # Create temp file with entry at offset 100
        temp_file = tempfile.NamedTemporaryFile(delete=False)
        temp_file.write(b"\x00" * 100)  # Padding

        # Write ASCII entry
        entry_data = b"ENT*"
        entry_data += b"10.5"
        entry_data += struct.pack("<I", 2000)  # Offset
        entry_data += struct.pack("<I", 1500)  # Object size
        entry_data += struct.pack("<I", 1234567890)  # Mod time
        entry_data += struct.pack("<H", 5)  # Comment length
        entry_data += struct.pack("<H", 10)  # Name length
        entry_data += b"w_main.win"  # Object name

        temp_file.write(entry_data)
        temp_file.close()

        try:
            with open(temp_file.name, "rb") as f:
                file_size = Path(temp_file.name).stat().st_size
                result = read_and_parse_entry_def(
                    f,
                    100,
                    False,
                    512,
                    file_size,
                )

            assert result is not None
            assert result.objectname == "w_main.win"
            assert result.version == "10.5"
            assert result.offset == 2000
            assert result.objectsize == 1500
        finally:
            Path(temp_file.name).unlink()

    def test_read_and_parse_entry_def_unicode(self):
        """Test reading and parsing Unicode entry from file."""
        import tempfile

        temp_file = tempfile.NamedTemporaryFile(delete=False)
        temp_file.write(b"\x00" * 200)  # Padding

        # Write Unicode entry
        entry_data = b"E\x00N\x00T\x00*\x00"  # Unicode signature (8 bytes)
        # Version string must be exactly 8 bytes
        version_bytes = b"1\x000\x00.\x005\x00"  # "10.5" in UTF-16 LE
        entry_data += version_bytes.ljust(8, b"\x00")  # Pad to 8 bytes
        entry_data += struct.pack("<Q", 3000)  # Offset (8 bytes, 64-bit)
        entry_data += struct.pack("<Q", 2500)  # Object size (8 bytes, 64-bit)
        entry_data += struct.pack("<Q", 1234567890)  # Mod time (8 bytes, 64-bit)
        entry_data += struct.pack("<I", 0)  # Comment length (4 bytes)
        entry_data += struct.pack("<I", 10)  # Name length in CHARACTERS (4 bytes)
        # Total: 48 bytes
        entry_data += b"w\x00_\x00m\x00a\x00i\x00n\x00.\x00w\x00i\x00n\x00"

        temp_file.write(entry_data)
        temp_file.close()

        try:
            with open(temp_file.name, "rb") as f:
                file_size = Path(temp_file.name).stat().st_size
                result = read_and_parse_entry_def(
                    f,
                    200,
                    True,
                    512,
                    file_size,
                )

            assert result is not None
            assert result.objectname == "w_main.win"
            assert result.version == "10.5"
        finally:
            Path(temp_file.name).unlink()

    def test_read_and_parse_entry_def_beyond_file(self):
        """Test reading entry that extends beyond file size."""
        import tempfile

        temp_file = tempfile.NamedTemporaryFile(delete=False)
        # Only write partial entry
        temp_file.write(b"ENT*" + b"10.0")
        temp_file.close()

        try:
            with open(temp_file.name, "rb") as f:
                file_size = Path(temp_file.name).stat().st_size
                result = read_and_parse_entry_def(
                    f,
                    0,
                    False,
                    512,
                    file_size,
                )

            # Should return None for incomplete entry
            assert result is None
        finally:
            Path(temp_file.name).unlink()


class TestDataExtraction:
    """Test extracting data blocks from entries."""

    def test_extract_data_from_entry_single_block(self):
        """Test extracting data from entry with single DAT block."""
        import tempfile

        # Create temp file with DAT block
        temp_file = tempfile.NamedTemporaryFile(delete=False)

        # Write DAT block at offset 100
        temp_file.write(b"\x00" * 100)  # Padding to offset
        temp_file.write(b"DAT*")  # Signature
        temp_file.write(struct.pack("<I", 0))  # No next block
        temp_file.write(struct.pack("<H", 20))  # Data length
        temp_file.write(b"This is test data!!!")  # 20 bytes
        temp_file.close()

        # Create entry pointing to this data
        entry = PbEntryDefinition(
            objectname="test.txt",
            version="10.0",
            offset=100,
            objectsize=30,  # DAT header + data
            moddatetime=datetime.datetime.now(),
            commentlen=0,
            objnamelen=8,
        )

        try:
            with open(temp_file.name, "rb") as f:
                file_size = Path(temp_file.name).stat().st_size
                result = extract_data_from_entry(
                    f,
                    entry,
                    False,
                    512,
                    file_size,
                )

            data_blocks, is_partial = result  # Unpack tuple
            assert len(data_blocks) == 1
            assert is_partial is False
            assert data_blocks[0].data == b"This is test data!!!"
            assert data_blocks[0].address == 100
            assert data_blocks[0].next_block_offset == 0
        finally:
            Path(temp_file.name).unlink()

    def test_extract_data_from_entry_multiple_blocks(self):
        """Test extracting data from entry with chained DAT blocks."""
        import tempfile

        temp_file = tempfile.NamedTemporaryFile(delete=False)

        # First DAT block at offset 100
        temp_file.write(b"\x00" * 100)
        temp_file.write(b"DAT*")
        temp_file.write(struct.pack("<I", 200))  # Next block at 200
        temp_file.write(struct.pack("<H", 10))
        temp_file.write(b"First part")

        # Second DAT block at offset 200
        temp_file.seek(200)
        temp_file.write(b"DAT*")
        temp_file.write(struct.pack("<I", 0))  # No more blocks
        temp_file.write(struct.pack("<H", 11))
        temp_file.write(b"Second part")
        temp_file.close()

        entry = PbEntryDefinition(
            objectname="test.txt",
            version="10.0",
            offset=100,
            objectsize=50,
            moddatetime=datetime.datetime.now(),
            commentlen=0,
            objnamelen=8,
        )

        try:
            with open(temp_file.name, "rb") as f:
                file_size = Path(temp_file.name).stat().st_size
                result = extract_data_from_entry(
                    f,
                    entry,
                    False,
                    512,
                    file_size,
                )

            data_blocks, is_partial = result  # Unpack tuple
            assert len(data_blocks) == 2
            assert is_partial is False
            assert data_blocks[0].data == b"First part"
            assert data_blocks[0].next_block_offset == 200
            assert data_blocks[1].data == b"Second part"
            assert data_blocks[1].next_block_offset == 0
        finally:
            Path(temp_file.name).unlink()

    def test_extract_data_from_entry_unicode_blocks(self):
        """Test extracting Unicode DAT blocks."""
        import tempfile

        temp_file = tempfile.NamedTemporaryFile(delete=False)

        # Unicode DAT block
        temp_file.write(b"\x00" * 100)
        temp_file.write(b"D\x00A\x00T\x00*\x00")  # Unicode signature
        temp_file.write(struct.pack("<I", 0))
        temp_file.write(struct.pack("<H", 16))
        temp_file.write(b"T\x00e\x00s\x00t\x00 \x00d\x00a\x00t\x00")
        temp_file.close()

        entry = PbEntryDefinition(
            objectname="test.txt",
            version="10.0",
            offset=100,
            objectsize=30,
            moddatetime=datetime.datetime.now(),
            commentlen=0,
            objnamelen=8,
        )

        try:
            with open(temp_file.name, "rb") as f:
                file_size = Path(temp_file.name).stat().st_size
                result = extract_data_from_entry(
                    f,
                    entry,
                    True,
                    512,
                    file_size,  # Unicode = True
                )

            data_blocks, is_partial = result  # Unpack tuple
            assert len(data_blocks) >= 1
            assert data_blocks[0].is_unicode_data_block_header is True
        finally:
            Path(temp_file.name).unlink()


class TestEntryParsingEdgeCases:
    """Test edge cases and error conditions."""

    def test_extract_entry_def_non_ascii_signature(self):
        """Test entry with non-ASCII bytes in signature position."""
        entry_data = b"\xff\xff\xff\xff" + b"\x00" * 20

        result = extract_entry_def(entry_data)

        assert result is None

    def test_extract_entry_def_extreme_values(self):
        """Test entry with extreme field values."""
        entry_data = b"ENT*"
        entry_data += b"99.9"
        entry_data += struct.pack("<I", 0xFFFFFFFF)  # Max offset
        entry_data += struct.pack("<I", 0xFFFFFFFF)  # Max size
        entry_data += struct.pack("<I", 0xFFFFFFFF)  # Max time
        entry_data += struct.pack("<H", 0xFFFF)  # Max comment len
        entry_data += struct.pack("<H", 5)
        entry_data += b"test.u"

        result = extract_entry_def(entry_data)

        # Should handle large values
        assert result is not None
        assert result.offset == 0xFFFFFFFF
        assert result.objectsize == 0xFFFFFFFF

    def test_extract_entry_def_zero_length_name(self):
        """Test entry with zero-length object name."""
        entry_data = b"ENT*"
        entry_data += b"10.0"
        entry_data += struct.pack("<I", 1000)  # Offset
        entry_data += struct.pack("<I", 500)  # Object size
        entry_data += struct.pack("<I", 1234567890)  # Mod time
        entry_data += struct.pack("<H", 0)  # Comment length
        entry_data += struct.pack("<H", 0)  # Zero name length

        result = extract_entry_def(entry_data)

        assert result is not None
        assert result.objectname == ""
        assert result.objnamelen == 0

    def test_extract_data_from_entry_invalid_dat_header(self):
        """Test extracting data when DAT header is invalid."""
        import tempfile

        temp_file = tempfile.NamedTemporaryFile(delete=False)
        temp_file.write(b"\x00" * 100)
        # Write invalid DAT header
        temp_file.write(b"BAD*")  # Wrong signature
        temp_file.write(struct.pack("<I", 0))  # Next block offset
        temp_file.write(struct.pack("<H", 10))  # Data length
        temp_file.write(b"Some data!")
        temp_file.close()

        entry = PbEntryDefinition(
            objectname="test.txt",
            version="10.0",
            offset=100,
            objectsize=20,
            moddatetime=datetime.datetime.now(),
            commentlen=0,
            objnamelen=8,
        )

        try:
            with open(temp_file.name, "rb") as f:
                file_size = Path(temp_file.name).stat().st_size
                result = extract_data_from_entry(
                    f,
                    entry,
                    False,
                    512,
                    file_size,
                )

            data_blocks, is_partial = result  # Unpack tuple
            # With invalid DAT header, extraction should be partial or empty
            assert is_partial is True or len(data_blocks) == 0
        finally:
            Path(temp_file.name).unlink()
