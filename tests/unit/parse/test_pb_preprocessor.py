"""Unit tests for PowerBuilder preprocessor."""

from pathlib import Path

import pytest

from src.parse.preprocessor.preprocessor import PowerBuilderPreprocessor


class TestPowerBuilderPreprocessor:
    """Test PowerBuilder preprocessor functionality."""

    def test_preprocessor_init(self):
        """Test preprocessor initialization."""
        pp = PowerBuilderPreprocessor(Path())
        assert pp is not None
        assert hasattr(pp, "preprocess")
        assert hasattr(pp, "add_define")
        assert hasattr(pp, "add_macro")
        assert pp.base_path == Path()
        assert pp.defines == set()
        assert pp.macros == {}

    def test_process_header(self):
        """Test processing PowerBuilder file headers."""
        pp = PowerBuilderPreprocessor(Path())

        # Test with export header
        code = "$PBExportHeader$test.sru\n$PBExportComments$Test\nrelease 12;\ninteger i = 1"
        result = pp.preprocess(code)
        assert "integer i = 1" in result
        assert "$PBExportHeader$" not in result

        # Test without header
        code = "integer i = 1"
        result = pp.preprocess(code)
        assert result == "integer i = 1"

    def test_process_comments(self):
        """Test comment processing."""
        pp = PowerBuilderPreprocessor(Path())

        # Test single line comment
        code = "integer i = 1 // this is a comment"
        result = pp.preprocess(code)
        assert "integer i = 1" in result
        # Comments are replaced with spaces
        assert "this is a comment" not in result or result.endswith(
            "                   ",
        )

        # Test multi-line comment
        code = "integer i /* comment */ = 1"
        result = pp.preprocess(code)
        assert "integer i" in result
        assert "= 1" in result
        assert "comment" not in result or "         " in result

    def test_string_preservation(self):
        """Test that strings are preserved."""
        pp = PowerBuilderPreprocessor(Path())

        # Test string with comment-like content
        code = 'string s = "// not a comment"'
        result = pp.preprocess(code)
        assert '"// not a comment"' in result

        # Test string with special chars
        code = 'string s = "test /* string */ content"'
        result = pp.preprocess(code)
        assert '"test /* string */ content"' in result

    def test_espelette_newlines(self):
        """Test Espelette newline handling (line continuations)."""
        pp = PowerBuilderPreprocessor(Path())

        # Test basic continuation
        code = "integer i = 1 + &\n  2"
        result = pp.preprocess(code)
        # The & and newline should be replaced with spaces
        assert "1 +" in result
        assert "2" in result

    def test_binary_section(self):
        """Test binary data section handling."""
        pp = PowerBuilderPreprocessor(Path())

        # Test binary section detection
        code = "integer i = 1\nStart of PowerBuilder Binary Data Section\n0x00 0x01"
        result = pp.preprocess(code)
        assert "integer i = 1" in result
        # Binary section causes rest to be skipped

    def test_add_define(self):
        """Test adding preprocessor defines."""
        pp = PowerBuilderPreprocessor(Path())

        pp.add_define("DEBUG")
        assert "DEBUG" in pp.defines

        pp.add_define("RELEASE")
        assert "RELEASE" in pp.defines
        assert len(pp.defines) == 2

    def test_add_macro(self):
        """Test adding macro definitions."""
        pp = PowerBuilderPreprocessor(Path())

        pp.add_macro("MAX_SIZE", "100")
        assert pp.macros["MAX_SIZE"] == "100"

        pp.add_macro("VERSION", '"1.0.0"')
        assert pp.macros["VERSION"] == '"1.0.0"'

    def test_expand_macros(self):
        """Test macro expansion."""
        pp = PowerBuilderPreprocessor(Path())

        pp.add_macro("MAX_SIZE", "100")
        code = "integer size = MAX_SIZE"
        result = pp.preprocess(code)
        assert "integer size = 100" in result

        # Test multiple macros
        pp.add_macro("MIN_SIZE", "10")
        code = "integer min = MIN_SIZE, max = MAX_SIZE"
        result = pp.preprocess(code)
        assert "10" in result
        assert "100" in result

    def test_conditional_compilation(self):
        """Test conditional compilation directives."""
        pp = PowerBuilderPreprocessor(Path())

        # Test ifdef with defined symbol
        pp.add_define("DEBUG")
        code = """$ifdef DEBUG
integer debug_level = 1
$endif"""
        result = pp.preprocess(code)
        assert "integer debug_level = 1" in result

        # Test ifdef with undefined symbol
        code = """$ifdef RELEASE
integer release = 1
$endif"""
        result = pp.preprocess(code)
        assert "integer release = 1" not in result

    def test_ifndef_directive(self):
        """Test ifndef directive."""
        pp = PowerBuilderPreprocessor(Path())

        # Test ifndef with undefined symbol
        code = "$ifndef DEBUG\ninteger production = 1\n$endif"
        result = pp.preprocess(code)
        assert "integer production = 1" in result

        # Test ifndef with defined symbol
        pp.add_define("DEBUG")
        code = "$ifndef DEBUG\ninteger production = 1\n$endif"
        result = pp.preprocess(code)
        assert "integer production = 1" not in result

    def test_else_directive(self):
        """Test else directive."""
        pp = PowerBuilderPreprocessor(Path())

        pp.add_define("DEBUG")
        code = "$ifdef DEBUG\ninteger debug = 1\n$else\ninteger release = 1\n$endif"
        result = pp.preprocess(code)
        assert "integer debug = 1" in result
        assert "integer release = 1" not in result

        # Test with undefined symbol
        code = "$ifdef RELEASE\ninteger release = 1\n$else\ninteger debug = 1\n$endif"
        result = pp.preprocess(code)
        assert "integer release = 1" not in result
        assert "integer debug = 1" in result

    def test_nested_conditionals(self):
        """Test nested conditional compilation."""
        pp = PowerBuilderPreprocessor(Path())

        pp.add_define("DEBUG")
        pp.add_define("VERBOSE")

        code = """$ifdef DEBUG
integer debug = 1
$ifdef VERBOSE
integer verbose = 1
$endif
$endif"""

        result = pp.preprocess(code)
        assert "integer debug = 1" in result
        assert "integer verbose = 1" in result

    def test_error_conditions(self):
        """Test error handling."""
        pp = PowerBuilderPreprocessor(Path())

        # Test unmatched endif
        with pytest.raises(ValueError, match="without matching"):
            pp.preprocess("$endif")

        # Test unmatched else
        with pytest.raises(ValueError, match="without matching"):
            pp.preprocess("$else")

        # Test unclosed ifdef
        with pytest.raises(ValueError, match="Unclosed"):
            pp.preprocess("$ifdef DEBUG\ninteger i = 1")

    def test_empty_input(self):
        """Test empty input handling."""
        pp = PowerBuilderPreprocessor(Path())

        result = pp.preprocess("")
        assert result == ""

        result = pp.preprocess("   \n  \n  ")
        assert result == "   \n  \n  "


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
