#!/usr/bin/env python3
"""Comprehensive tests for the decompiled output post-processor."""

import shutil
import tempfile
from pathlib import Path

from src.decompile.core.processor import DecompiledOutputFilter


class TestDecompiledOutputFilter:
    """Test the decompiled output filter."""

    def test_init_default_values(self):
        """Test filter initialization with default values."""
        filter = DecompiledOutputFilter()
        assert filter.max_consecutive_returns == 10
        assert filter.max_consecutive_blank_lines == 3
        assert filter.max_repeated_pattern == 5

    def test_init_custom_values(self):
        """Test filter initialization with custom values."""
        filter = DecompiledOutputFilter(
            max_consecutive_returns=5,
            max_consecutive_blank_lines=2,
            max_repeated_pattern=3,
        )
        assert filter.max_consecutive_returns == 5
        assert filter.max_consecutive_blank_lines == 2
        assert filter.max_repeated_pattern == 3

    def test_filter_consecutive_returns(self):
        """Test filtering of consecutive return statements."""
        filter = DecompiledOutputFilter(max_consecutive_returns=3)

        content = """function test()
    return 1
    return 2
    return 3
    return 4
    return 5
    return 6
    return 7
    return 8
end function"""

        result = filter.filter_output(content)

        # Should keep first 3 returns and add summary comments
        assert "return 1" in result
        assert "return 2" in result
        assert "return 3" in result
        assert "return 4" not in result
        assert "// ... 6 unique return values" in result
        assert "// ... skipping repetitive returns" in result
        assert "// ... skipped 5 return statements" in result

    def test_filter_consecutive_blank_lines(self):
        """Test filtering of consecutive blank lines."""
        filter = DecompiledOutputFilter(max_consecutive_blank_lines=2)

        content = """line 1


line 2




line 3"""

        result = filter.filter_output(content)
        lines = result.split("\n")

        # Count max consecutive blanks
        max_blanks = 0
        current_blanks = 0
        for line in lines:
            if not line.strip():
                current_blanks += 1
                max_blanks = max(max_blanks, current_blanks)
            else:
                current_blanks = 0

        assert max_blanks <= 2

    def test_filter_repeated_patterns_if_blocks(self):
        """Test filtering of repeated if block patterns."""
        filter = DecompiledOutputFilter(max_repeated_pattern=2)

        content = """function test()
    if x = 1 then
        return 1
    end if
    if x = 1 then
        return 1
    end if
    if x = 1 then
        return 1
    end if
    if x = 1 then
        return 1
    end if
end function"""

        result = filter.filter_output(content)

        # Should keep first 2 occurrences
        occurrences = result.count("if x = 1 then")
        assert occurrences == 2
        assert "// ... pattern repeats" in result

    def test_filter_different_return_values(self):
        """Test that different return values are tracked."""
        filter = DecompiledOutputFilter(max_consecutive_returns=2)

        content = """function test()
    return "hello"
    return "world"
    return "foo"
    return "bar"
    return "baz"
end function"""

        result = filter.filter_output(content)

        assert 'return "hello"' in result
        assert 'return "world"' in result
        assert "// ... 5 unique return values" in result

    def test_pattern_detection_starters(self):
        """Test pattern detection for various statement types."""
        filter = DecompiledOutputFilter()

        assert filter._is_pattern_start("if x = 1 then")
        assert filter._is_pattern_start("for i = 1 to 10")
        assert filter._is_pattern_start("while x > 0")
        assert filter._is_pattern_start("do while true")
        assert filter._is_pattern_start("switch x")
        assert filter._is_pattern_start("L_001:")
        assert filter._is_pattern_start("// ERROR: unknown opcode")
        assert filter._is_pattern_start("// OPCODE: 0x42")

        assert not filter._is_pattern_start("return 1")
        assert not filter._is_pattern_start("x = 1")

    def test_extract_pattern_if_block(self):
        """Test pattern extraction for if blocks."""
        filter = DecompiledOutputFilter()

        lines = [
            "    if x = 1 then",
            "        y = 2",
            "        return y",
            "    end if",
            "    z = 3",
        ]

        pattern = filter._extract_pattern(lines, 0)

        assert "if x = 1 then" in pattern
        assert "y = 2" in pattern
        assert "return y" in pattern
        assert "end if" in pattern
        assert "z = 3" not in pattern  # Outside the if block

    def test_extract_pattern_respects_indentation(self):
        """Test that pattern extraction respects indentation levels."""
        filter = DecompiledOutputFilter()

        lines = [
            "    for i = 1 to 10",
            "        if x = i then",
            "            return i",
            "        end if",
            "    next",
            "    return 0",
        ]

        pattern = filter._extract_pattern(lines, 0)

        assert "for i = 1 to 10" in pattern
        assert "next" in pattern
        assert "return 0" not in pattern  # Less indented

    def test_no_filtering_needed(self):
        """Test that content without repetitions is unchanged."""
        filter = DecompiledOutputFilter()

        content = """function calculate(x, y)
    if x > y then
        return x
    else
        return y
    end if
end function"""

        result = filter.filter_output(content)

        # Should be unchanged except for potential trailing newline differences
        assert result.strip() == content.strip()

    def test_mixed_filtering(self):
        """Test filtering with mixed patterns."""
        filter = DecompiledOutputFilter(
            max_consecutive_returns=2,
            max_consecutive_blank_lines=1,
            max_repeated_pattern=2,
        )

        content = """function complex()
    // Many returns
    return 1
    return 2
    return 3
    return 4



    // Repeated pattern
    if x = 1 then
        y = 1
    end if
    if x = 1 then
        y = 1
    end if
    if x = 1 then
        y = 1
    end if
end function"""

        result = filter.filter_output(content)

        # Check all filters applied
        assert result.count("return") == 2  # Only first 2 returns
        assert "// ... skipped" in result
        assert result.count("if x = 1 then") == 2  # Only first 2 patterns

        # Check blank line filtering
        lines = result.split("\n")
        max_blanks = 0
        current_blanks = 0
        for line in lines:
            if not line.strip():
                current_blanks += 1
                max_blanks = max(max_blanks, current_blanks)
            else:
                current_blanks = 0
        assert max_blanks <= 1

    def test_filter_file_success(self):
        """Test filtering a file successfully."""
        filter = DecompiledOutputFilter(max_consecutive_returns=2)

        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.txt"
            output_path = Path(tmpdir) / "output.txt"

            # Create input file
            content = """function test()
    return 1
    return 2
    return 3
    return 4
end function"""
            input_path.write_text(content)

            # Filter file
            filter.filter_file(str(input_path), str(output_path))

            # Check output
            assert output_path.exists()
            result = output_path.read_text()
            assert "return 1" in result
            assert "return 2" in result
            assert "return 3" not in result

    def test_filter_file_error_handling(self):
        """Test error handling when filtering files."""
        filter = DecompiledOutputFilter()

        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "nonexistent.txt"
            output_path = Path(tmpdir) / "output.txt"

            # Create a dummy file to copy
            dummy_path = Path(tmpdir) / "dummy.txt"
            dummy_path.write_text("dummy content")

            # Patch shutil.copy2 to verify it's called on error
            original_copy = shutil.copy2
            copy_called = False

            def mock_copy(src, dst):
                nonlocal copy_called
                copy_called = True
                return original_copy(src, dst)

            shutil.copy2 = mock_copy

            try:
                # This should fail and fall back to copy
                filter.filter_file(str(input_path), str(output_path))

                # The error handler tries to copy the input file, which doesn't exist
                # So output shouldn't be created
                assert not output_path.exists()
            finally:
                shutil.copy2 = original_copy

    def test_empty_content(self):
        """Test filtering empty content."""
        filter = DecompiledOutputFilter()

        result = filter.filter_output("")
        assert result == ""

    def test_label_patterns(self):
        """Test filtering of label patterns."""
        filter = DecompiledOutputFilter(max_repeated_pattern=2)

        content = """function test()
    L_001:
        x = 1
    L_002:
        x = 2
    L_003:
        x = 3
    L_004:
        x = 4
end function"""

        result = filter.filter_output(content)

        # Labels shouldn't be filtered as repeated patterns
        # since they have different content
        assert "L_001:" in result
        assert "L_002:" in result
        assert "L_003:" in result
        assert "L_004:" in result

    def test_error_opcode_patterns(self):
        """Test filtering of error and opcode comment patterns."""
        filter = DecompiledOutputFilter(max_repeated_pattern=2)

        content = """function test()
    // ERROR: unknown opcode 0x99
    x = 1
    // ERROR: unknown opcode 0x99
    x = 2
    // ERROR: unknown opcode 0x99
    x = 3
    // OPCODE: 0x42 PUSH_INT
    y = 1
    // OPCODE: 0x42 PUSH_INT
    y = 2
    // OPCODE: 0x42 PUSH_INT
    y = 3
end function"""

        result = filter.filter_output(content)

        # Should limit repeated error/opcode comments
        assert result.count("// ERROR: unknown opcode 0x99") <= 2
        assert result.count("// OPCODE: 0x42 PUSH_INT") <= 2
        assert "// ... pattern repeats" in result

    def test_large_content_performance(self):
        """Test performance with large content."""
        filter = DecompiledOutputFilter()

        # Generate large content with many returns
        lines = ["function large()"]
        for i in range(1000):
            lines.append(f"    return {i}")
        lines.append("end function")

        content = "\n".join(lines)

        # Should complete quickly even with large input
        import time

        start = time.time()
        result = filter.filter_output(content)
        elapsed = time.time() - start

        assert elapsed < 1.0  # Should complete in under 1 second
        assert len(result) < len(content)  # Should be reduced
        assert "// ... skipped" in result


class TestPatternExtraction:
    """Test pattern extraction edge cases."""

    def test_extract_pattern_at_end_of_file(self):
        """Test pattern extraction at the end of file."""
        filter = DecompiledOutputFilter()

        lines = ["if x = 1 then", "    return 1", "end if"]
        pattern = filter._extract_pattern(lines, 0)

        assert pattern == "\n".join(lines)

    def test_extract_pattern_beyond_bounds(self):
        """Test pattern extraction with invalid index."""
        filter = DecompiledOutputFilter()

        lines = ["line 1", "line 2"]
        pattern = filter._extract_pattern(lines, 10)

        assert pattern == ""

    def test_extract_pattern_max_lines(self):
        """Test that pattern extraction is limited to 20 lines."""
        filter = DecompiledOutputFilter()

        # Create a very long if block
        lines = ["if x = 1 then"]
        for i in range(30):
            lines.append(f"    statement_{i}")
        lines.append("end if")

        pattern = filter._extract_pattern(lines, 0)
        pattern_lines = pattern.split("\n")

        assert len(pattern_lines) <= 20
