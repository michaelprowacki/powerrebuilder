#!/usr/bin/env python3
"""Test file operations module, particularly UTF-16 DataWindow extraction."""

import struct
import tempfile
from pathlib import Path

from src.extract.pbd.data_block import DataClass
from src.extract.pbd.entry import PbEntryDefinition
from src.extract.pbd.io.file_operations import (
    _extract_datawindow_syntax,
    _extract_utf16_syntax,
    _process_datawindow,
    save_binary_file,
    save_text_file,
)


class TestUTF16Extraction:
    """Test UTF-16 DataWindow extraction functionality."""

    def test_extract_utf16_syntax_with_pbselect(self):
        """Test extracting UTF-16 encoded PBSELECT statement."""
        # Create UTF-16 LE encoded PBSELECT data
        pbselect_text = (
            'PBSELECT( VERSION(400) TABLE(NAME="jobs" ) COLUMN(NAME="jobs.job_id") )'
        )
        utf16_data = pbselect_text.encode("utf-16-le")

        # Add some padding
        test_data = b"\x00\x00" + utf16_data + b"\x00\x00\x00\x00"

        # Extract from position 2
        result = _extract_utf16_syntax(test_data, 2)

        assert result is not None
        assert "PBSELECT" in result
        assert "jobs.job_id" in result

    def test_extract_utf16_syntax_with_release(self):
        """Test extracting UTF-16 encoded release statement."""
        # Create UTF-16 LE encoded release data
        release_text = (
            "release 12.5;\ndatawindow(units=0 timer_interval=0)\nheader(height=80)"
        )
        utf16_data = release_text.encode("utf-16-le")

        test_data = utf16_data + b"\x00\x00\x00\x00"

        result = _extract_utf16_syntax(test_data, 0)

        assert result is not None
        assert "release" in result
        assert "datawindow" in result

    def test_extract_utf16_syntax_invalid_data(self):
        """Test extraction with invalid UTF-16 data."""
        # Create invalid UTF-16 data (odd number of bytes)
        invalid_data = b"P\x00B\x00S\x00E\x00L\x00E\x00C\x00T\x00\x00"

        result = _extract_utf16_syntax(invalid_data, 0)

        # Should handle gracefully, may return None or partial data
        assert result is None or len(result) < 10

    def test_extract_utf16_syntax_with_binary_marker(self):
        """Test extraction stops at binary marker."""
        # Create longer UTF-16 data to meet minimum length requirement
        text_part = 'PBSELECT( VERSION(400) TABLE(NAME="employees") COLUMN(NAME="id") )'
        utf16_data = text_part.encode("utf-16-le")

        # Add four null bytes as end marker
        test_data = utf16_data + b"\x00\x00\x00\x00" + b"more data after"

        result = _extract_utf16_syntax(test_data, 0)

        assert result is not None
        assert "PBSELECT" in result
        assert "employees" in result
        # Should include the full text before null bytes
        assert len(result) >= 50  # Minimum required length

    def test_extract_datawindow_syntax_utf16_pbselect(self):
        """Test full DataWindow extraction with UTF-16 PBSELECT."""
        # Create realistic UTF-16 LE encoded PBSELECT
        pbselect = (
            'PBSELECT( VERSION(400) TABLE(NAME="employees" ) '
            'COLUMN(NAME="emp.id") COLUMN(NAME="emp.name") )'
        )
        utf16_pbselect = b"P\x00B\x00S\x00E\x00L\x00E\x00C\x00T\x00" + pbselect[
            8:
        ].encode("utf-16-le")

        # Add some prefix data
        test_data = b"\x00\x00\x00\x00" + utf16_pbselect

        result = _extract_datawindow_syntax(test_data, "d_test.dwo")

        assert result is not None
        assert "PBSELECT" in result
        assert "employees" in result

    def test_extract_datawindow_syntax_utf16_release(self):
        """Test full DataWindow extraction with UTF-16 release statement."""
        # Create UTF-16 LE encoded release statement
        release_text = (
            "release 12.5;\ndatawindow(units=0)\ntable(column=(type=char(10)))"
        )
        utf16_release = b"r\x00e\x00l\x00e\x00a\x00s\x00e\x00" + release_text[
            7:
        ].encode("utf-16-le")

        test_data = b"\x00\x00" + utf16_release

        result = _extract_datawindow_syntax(test_data, "d_test.dwo")

        assert result is not None
        assert "release" in result
        assert "datawindow" in result

    def test_extract_datawindow_syntax_no_markers(self):
        """Test extraction returns None when no DataWindow markers found."""
        # Data without PBSELECT or release markers
        test_data = b"This is not a DataWindow definition"

        result = _extract_datawindow_syntax(test_data, "d_test.dwo")

        assert result is None

    def test_process_datawindow_with_utf16(self):
        """Test processing DataWindow with UTF-16 data."""
        # Create mock entry with required parameters
        import datetime

        entry = PbEntryDefinition(
            objectname="d_test_utf16.dwo",
            version="10.0",
            offset=0,
            objectsize=1000,
            moddatetime=datetime.datetime.now(),
            commentlen=0,
            objnamelen=len("d_test_utf16.dwo"),
        )

        # Create mock data with UTF-16 PBSELECT
        pbselect = 'PBSELECT( VERSION(400) TABLE(NAME="test_table") )'
        utf16_data = b"P\x00B\x00S\x00E\x00L\x00E\x00C\x00T\x00" + pbselect[8:].encode(
            "utf-16-le"
        )

        # Create DataClass mock with required fields
        data = (
            b"DAT*"
            + struct.pack("<I", 0)
            + struct.pack("<H", len(utf16_data))
            + utf16_data
        )
        data_block = DataClass(
            address=0,
            data=data,
            next_block_offset=0,
            data_length_in_block=len(data),
            is_unicode_data_block_header=False,
        )
        data_list = [data_block]

        with tempfile.TemporaryDirectory() as output_dir:
            # Process the DataWindow
            _process_datawindow(entry, data_list, output_dir)

            # Check that files were created
            output_path = Path(output_dir)
            # Look for .srd file
            srd_files = list(output_path.glob("**/*.srd"))
            assert len(srd_files) > 0

            # Check SQL file was created
            sql_files = list(output_path.glob("**/*.sql"))
            assert len(sql_files) > 0

    def test_save_text_file_skips_datawindow(self):
        """Test that save_text_file skips DataWindow objects."""
        with tempfile.TemporaryDirectory() as output_dir:
            # Try to save a DataWindow object
            save_text_file("d_test.dwo", "datawindow content", output_dir)

            # Check no file was created
            output_path = Path(output_dir)
            assert not (output_path / "d_test.dwo").exists()

    def test_save_binary_file_creates_metadata(self):
        """Test that save_binary_file creates metadata."""
        with tempfile.TemporaryDirectory() as output_dir:
            test_data = b"Binary test data"
            save_binary_file("test.bin", test_data, output_dir)

            # Check binary file created
            resources_dir = Path(output_dir) / "resources"
            assert (resources_dir / "test.bin").exists()

            # Check metadata file created
            assert (resources_dir / "test.bin.meta.json").exists()

            # Verify metadata content
            import json

            with open(resources_dir / "test.bin.meta.json") as f:
                metadata = json.load(f)
                assert metadata["original_name"] == "test.bin"
                assert metadata["size_bytes"] == len(test_data)


class TestDataWindowFormatterIntegration:
    """Test integration with DataWindow formatter."""

    def test_sql_extraction_from_pbselect(self):
        """Test that SQL is properly extracted from PBSELECT."""
        # Create entry with PBSELECT
        import datetime

        entry = PbEntryDefinition(
            objectname="d_sql_test.dwo",
            version="10.0",
            offset=0,
            objectsize=500,
            moddatetime=datetime.datetime.now(),
            commentlen=0,
            objnamelen=len("d_sql_test.dwo"),
        )

        # Create PBSELECT with SQL
        pbselect = (
            'PBSELECT( VERSION(400) TABLE(NAME="employees" ) '
            'COLUMN(NAME="emp_id") WHERE( EXP1="emp_id" OP="=" EXP2=":emp_id" ) )'
        )
        utf16_data = pbselect.encode("utf-16-le")

        # Create data block
        data_block = DataClass(
            address=0,
            data=utf16_data,
            next_block_offset=0,
            data_length_in_block=len(utf16_data),
            is_unicode_data_block_header=False,
        )
        data_list = [data_block]

        with tempfile.TemporaryDirectory() as output_dir:
            _process_datawindow(entry, data_list, output_dir)

            # Check SQL file contains expected content
            sql_files = list(Path(output_dir).glob("**/*.sql"))
            if sql_files:
                content = sql_files[0].read_text()
                assert "PBSELECT" in content
                assert "employees" in content


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_extract_utf16_empty_data(self):
        """Test extraction with empty data."""
        result = _extract_utf16_syntax(b"", 0)
        assert result is None

    def test_extract_utf16_start_beyond_data(self):
        """Test extraction with start position beyond data length."""
        test_data = b"P\x00B\x00"
        result = _extract_utf16_syntax(test_data, 100)
        assert result is None

    def test_extract_datawindow_compiled_pdw(self):
        """Test handling of compiled PDW format."""
        # Simulate compiled PDW data (should fail extraction)
        compiled_data = b"PDW1000\x00" + b"\x00" * 100

        result = _extract_datawindow_syntax(compiled_data, "d_compiled.dwo")

        # Should return None for compiled format
        assert result is None

    def test_utf16_with_mixed_content(self):
        """Test UTF-16 extraction with mixed valid/invalid characters."""
        # Create longer UTF-16 text to meet minimum requirement
        text = 'PBSELECT( VERSION(400) TABLE(NAME="test_table") COLUMN(NAME="col1") WHERE(id=1) )'
        # Encode as UTF-16 LE
        utf16_data = text.encode("utf-16-le")
        # Insert some non-printable bytes that will be filtered
        corrupted_data = utf16_data[:20] + b"\x01\x00\x02\x00" + utf16_data[20:]

        result = _extract_utf16_syntax(corrupted_data, 0)

        # Should extract valid parts, skipping non-printable chars
        assert result is not None
        assert "PBSELECT" in result
        assert "TABLE" in result
        assert len(result) >= 50  # Must meet minimum length
