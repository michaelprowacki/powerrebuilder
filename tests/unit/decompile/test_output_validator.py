#!/usr/bin/env python3
"""Test output format validation for decompiled code."""

from src.decompile.core.validator import OutputValidator, ValidationError


class TestOutputValidator:
    """Test the output validator."""

    def test_valid_function(self):
        """Test validation of a valid function."""
        lines = [
            "function integer calculate_sum(integer a, integer b)",
            "    integer result",
            "    ",
            "    result = a + b",
            "    return result",
            "end function",
        ]

        validator = OutputValidator()
        is_valid, errors = validator.validate(lines)

        assert is_valid
        assert len(errors) == 0

    def test_unclosed_block(self):
        """Test detection of unclosed blocks."""
        lines = [
            "function integer test()",
            "    if a > 0 then",
            "        return 1",
            "    // Missing 'end if'",
            "end function",
        ]

        validator = OutputValidator()
        is_valid, errors = validator.validate(lines)

        assert not is_valid
        assert any("Expected 'end if'" in e.message for e in errors)

    def test_mismatched_blocks(self):
        """Test detection of mismatched block endings."""
        lines = [
            "function test()",
            "    if condition then",
            "        do_something()",
            "    end function  // Should be 'end if'",
            "end if  // Should be 'end function'",
        ]

        validator = OutputValidator()
        is_valid, errors = validator.validate(lines)

        assert not is_valid
        assert len(errors) >= 1

    def test_nested_blocks(self):
        """Test validation of properly nested blocks."""
        lines = [
            "function process_data()",
            "    integer i",
            "    ",
            "    for i = 1 to 10",
            "        if i > 5 then",
            "            do_something(i)",
            "        else",
            "            do_other(i)",
            "        end if",
            "    next",
            "end function",
        ]

        validator = OutputValidator()
        is_valid, errors = validator.validate(lines)

        # Debug output
        if not is_valid or errors:
            print("\nValidation errors:")
            print(validator.format_errors(errors))

        assert is_valid
        assert len(errors) == 0

    def test_choose_case_validation(self):
        """Test validation of choose case blocks."""
        lines = [
            "choose case option",
            "    case 1",
            "        process_option1()",
            "    case 2",
            "        process_option2()",
            "    case else",
            "        process_default()",
            "end choose",
        ]

        validator = OutputValidator()
        is_valid, errors = validator.validate(lines)

        assert is_valid
        assert len(errors) == 0

    def test_indentation_warning(self):
        """Test indentation consistency warnings."""
        lines = [
            "function test()",
            "    integer a",
            "   integer b  // 3 spaces instead of 4",
            "    return a + b",
            "end function",
        ]

        validator = OutputValidator()
        is_valid, errors = validator.validate(lines)

        # Should be valid but with warnings
        assert is_valid
        warnings = [e for e in errors if e.severity == "warning"]
        assert len(warnings) > 0
        assert any("indentation" in w.message.lower() for w in warnings)

    def test_unbalanced_parentheses(self):
        """Test detection of unbalanced parentheses."""
        lines = [
            "function test()",
            "    result = calculate(a, b, c  // Missing closing paren",
            "    return result",
            "end function",
        ]

        validator = OutputValidator()
        is_valid, errors = validator.validate(lines)

        assert not is_valid
        assert any("parentheses" in e.message.lower() for e in errors)

    def test_trailing_comma_warning(self):
        """Test detection of trailing commas."""
        lines = [
            "function test()",
            "    integer a, b, c,",  # Trailing comma at end of line
            "    return 0",
            "end function",
        ]

        validator = OutputValidator()
        is_valid, errors = validator.validate(lines)

        # Should be valid but with warnings
        assert is_valid
        warnings = [e for e in errors if e.severity == "warning"]
        assert any("comma" in w.message.lower() for w in warnings)

    def test_comment_formatting(self):
        """Test comment formatting validation."""
        lines = [
            "function test()",
            "    integer a//No space before comment",
            "    integer b // Proper comment",
            "    return a + b",
            "end function",
        ]

        validator = OutputValidator()
        is_valid, errors = validator.validate(lines)

        assert is_valid
        warnings = [e for e in errors if e.severity == "warning"]
        assert any(
            "comment" in w.message.lower() and "whitespace" in w.message.lower()
            for w in warnings
        )

    def test_format_errors_output(self):
        """Test error formatting."""
        validator = OutputValidator()

        errors = [
            ValidationError(10, "Unclosed if block", "error"),
            ValidationError(15, "Inconsistent indentation", "warning"),
            ValidationError(20, "Consider using descriptive names", "info"),
        ]

        formatted = validator.format_errors(errors)

        assert "Errors (1):" in formatted
        assert "Line 10: Unclosed if block" in formatted
        assert "Warnings (1):" in formatted
        assert "Line 15: Inconsistent indentation" in formatted
        assert "Info (1):" in formatted
        assert "Line 20: Consider using descriptive names" in formatted

    def test_empty_lines_ignored(self):
        """Test that empty lines and comments are properly ignored."""
        lines = [
            "// This is a header comment",
            "",
            "function test()",
            "    // Implementation",
            "    ",
            "    return 0",
            "end function",
            "",
        ]

        validator = OutputValidator()
        is_valid, errors = validator.validate(lines)

        assert is_valid
        assert len(errors) == 0

    def test_do_while_vs_do_until(self):
        """Test proper handling of different do loop types."""
        lines_do_while = [
            "do while condition",
            "    process()",
            "loop",
        ]

        lines_do_until = [
            "do",
            "    process()",
            "loop until condition",
        ]

        validator = OutputValidator()

        # Test do while
        is_valid, errors = validator.validate(lines_do_while)
        assert is_valid
        assert len(errors) == 0

        # Test do until
        is_valid, errors = validator.validate(lines_do_until)
        assert is_valid
        assert len(errors) == 0

    def test_try_catch_validation(self):
        """Test validation of try-catch blocks."""
        lines = [
            "try",
            "    risky_operation()",
            "catch (Exception e)",
            "    handle_error(e)",
            "finally",
            "    cleanup()",
            "end try",
        ]

        validator = OutputValidator()
        is_valid, errors = validator.validate(lines)

        assert is_valid
        assert len(errors) == 0
