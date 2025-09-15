#!/usr/bin/env python3
"""Test output format validation in decompiler."""

import pytest

from src.decompile.coordinator import (
    SUPPORTED_OUTPUT_FORMATS,
    ExtractedFileDecompiler,
    PowerBuilderDecompiler,
)


class TestOutputFormatValidation:
    """Test output format validation in decompiler."""

    def test_valid_output_formats(self, tmp_path):
        """Test that valid output formats are accepted."""
        for format in SUPPORTED_OUTPUT_FORMATS:
            # ExtractedFileDecompiler
            decompiler = ExtractedFileDecompiler(tmp_path, output_format=format)
            assert decompiler.output_format == format

            # PowerBuilderDecompiler
            pb_decompiler = PowerBuilderDecompiler(tmp_path, output_format=format)
            assert pb_decompiler.output_format == format

    def test_invalid_output_format_extracted(self, tmp_path):
        """Test that invalid output formats raise ValueError for ExtractedFileDecompiler."""
        with pytest.raises(ValueError) as exc_info:
            ExtractedFileDecompiler(tmp_path, output_format="invalid")

        assert "Unsupported output format: invalid" in str(exc_info.value)
        assert "Supported formats: pb, txt, md" in str(exc_info.value)

    def test_invalid_output_format_powerbuilder(self, tmp_path):
        """Test that invalid output formats raise ValueError for PowerBuilderDecompiler."""
        with pytest.raises(ValueError) as exc_info:
            PowerBuilderDecompiler(tmp_path, output_format="invalid")

        assert "Unsupported output format: invalid" in str(exc_info.value)
        assert "Supported formats: pb, txt, md" in str(exc_info.value)

    def test_default_output_format(self, tmp_path):
        """Test that default output format is 'pb'."""
        # ExtractedFileDecompiler
        decompiler = ExtractedFileDecompiler(tmp_path)
        assert decompiler.output_format == "pb"

        # PowerBuilderDecompiler
        pb_decompiler = PowerBuilderDecompiler(tmp_path)
        assert pb_decompiler.output_format == "pb"

    def test_format_output_pb(self, tmp_path):
        """Test PowerBuilder format output (unchanged)."""
        decompiler = ExtractedFileDecompiler(tmp_path, output_format="pb")

        content = "function integer test()\nreturn 0\nend function"
        formatted = decompiler._format_output(content, "test", ".fun")

        assert formatted == content  # Should be unchanged

    def test_format_output_txt(self, tmp_path):
        """Test plain text format output."""
        decompiler = ExtractedFileDecompiler(tmp_path, output_format="txt")

        content = "function integer test()\nreturn 0\nend function"
        formatted = decompiler._format_output(content, "test", ".fun")

        assert (
            "============================================================" in formatted
        )
        assert "Function/User Object: test" in formatted
        assert content in formatted

    def test_format_output_md(self, tmp_path):
        """Test markdown format output."""
        decompiler = ExtractedFileDecompiler(tmp_path, output_format="md")

        content = "function integer test()\nreturn 0\nend function"
        formatted = decompiler._format_output(content, "test", ".fun")

        assert "# Function/User Object: test" in formatted
        assert "```powerbuilder" in formatted
        assert content in formatted
        assert "```" in formatted

    def test_file_extensions(self):
        """Test that output format extensions are correct."""
        from src.decompile.coordinator import OUTPUT_FORMAT_EXTENSIONS

        assert OUTPUT_FORMAT_EXTENSIONS["pb"] == ".pb"
        assert OUTPUT_FORMAT_EXTENSIONS["txt"] == ".txt"
        assert OUTPUT_FORMAT_EXTENSIONS["md"] == ".md"
