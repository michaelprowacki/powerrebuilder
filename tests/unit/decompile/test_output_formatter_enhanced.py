#!/usr/bin/env python3
"""Test enhancements to output formatter."""

from src.decompile.core.output import OutputFormatter
from src.decompile.types import BlockType, ControlBlock


class TestRepeatUntilFormatting:
    """Test REPEAT UNTIL block formatting."""

    def test_format_repeat_until_block(self):
        """Test formatting of repeat-until blocks."""
        # Create a repeat-until block
        repeat_block = ControlBlock(
            type=BlockType.REPEAT_UNTIL,
            start_addr=0x00,
            end_addr=0x10,
            metadata={"condition": "x > 10"},
        )

        # Add body
        body_block = ControlBlock(
            type=BlockType.BASIC,
            start_addr=0x00,
            end_addr=0x08,
            statements=["x = x + 1", "Print(x)"],
        )
        repeat_block.body = body_block

        formatter = OutputFormatter()
        lines = formatter._format_block(repeat_block)

        expected = [
            "do",
            "    x = x + 1",
            "    Print(x)",
            "loop until x > 10",
        ]

        assert lines == expected

    def test_format_empty_repeat_until(self):
        """Test formatting of empty repeat-until blocks."""
        repeat_block = ControlBlock(
            type=BlockType.REPEAT_UNTIL,
            start_addr=0x00,
            end_addr=0x10,
            metadata={"condition": "done = true"},
        )

        formatter = OutputFormatter()
        lines = formatter._format_block(repeat_block)

        expected = [
            "do",
            "loop until done = true",
        ]

        assert lines == expected


class TestChooseCaseFormatting:
    """Test CHOOSE CASE block formatting."""

    def test_format_choose_case_block(self):
        """Test formatting of choose-case blocks."""
        # Create a choose-case block
        choose_block = ControlBlock(
            type=BlockType.CHOOSE_CASE,
            start_addr=0x00,
            end_addr=0x30,
            metadata={"expression": "menu_choice"},
        )

        # Add cases
        case1 = ControlBlock(
            type=BlockType.CASE,
            start_addr=0x10,
            end_addr=0x18,
            statements=["Process_Option1()"],
            metadata={"case_value": "1"},
        )

        case2 = ControlBlock(
            type=BlockType.CASE,
            start_addr=0x20,
            end_addr=0x28,
            statements=["Process_Option2()"],
            metadata={"case_value": "2"},
        )

        default_case = ControlBlock(
            type=BlockType.CASE,
            start_addr=0x30,
            end_addr=0x38,
            statements=["Show_Error()"],
            metadata={"is_default": True},
        )

        choose_block.cases = [case1, case2]
        choose_block.default_case = default_case

        formatter = OutputFormatter()
        lines = formatter._format_block(choose_block)

        # Check structure
        assert lines[0] == "choose case menu_choice"
        assert any("case 1" in line for line in lines)
        assert any("case 2" in line for line in lines)
        assert any("case else" in line for line in lines)
        assert lines[-1] == "end choose"

        # Check indentation
        assert "        Process_Option1()" in lines
        assert "        Process_Option2()" in lines
        assert "        Show_Error()" in lines


class TestComplexControlFlow:
    """Test formatting of complex control flow structures."""

    def test_nested_loops(self):
        """Test formatting of nested loop structures."""
        # Create outer repeat-until with inner for loop
        outer_repeat = ControlBlock(
            type=BlockType.REPEAT_UNTIL,
            start_addr=0x00,
            end_addr=0x40,
            metadata={"condition": "finished"},
        )

        # Create body with for loop
        for_loop = ControlBlock(
            type=BlockType.FOR,
            start_addr=0x10,
            end_addr=0x30,
            metadata={
                "variable": "i",
                "start": "1",
                "end": "10",
                "step": "1",
            },
        )

        # For loop body
        for_body = ControlBlock(
            type=BlockType.BASIC,
            start_addr=0x20,
            end_addr=0x28,
            statements=["total = total + i"],
        )
        for_loop.body = for_body

        # Outer body contains the for loop and another statement
        outer_body = ControlBlock(
            type=BlockType.BASIC,
            start_addr=0x10,
            end_addr=0x38,
            instructions=[],
        )
        outer_body.statements = []  # Will be handled by nested block

        outer_repeat.body = for_loop  # Simplified - just the for loop

        formatter = OutputFormatter()
        lines = formatter._format_block(outer_repeat)

        expected = [
            "do",
            "    for i = 1 to 10",
            "        total = total + i",
            "    next",
            "loop until finished",
        ]

        assert lines == expected
