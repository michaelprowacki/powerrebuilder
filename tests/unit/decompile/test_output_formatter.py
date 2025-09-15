"""Unit tests for output formatter."""

import pytest

from src.decompile.analysis.control import BlockType, ControlBlock
from src.decompile.core.output import OutputFormatter
from src.decompile.pcode.decoder import DecodedObject


class TestOutputFormatter:
    """Test output formatting functionality."""

    @pytest.fixture
    def formatter(self):
        """Create a fresh formatter instance."""
        return OutputFormatter()

    def test_format_empty_object(self, formatter):
        """Test formatting empty decoded object."""
        decoded_obj = DecodedObject(
            name="test.fun",
            type="function",
            version="pb80_0",
            instructions=[],
            metadata={},
        )

        lines = formatter.format_object(decoded_obj, [], "test.pbd")

        assert "// Source: test.pbd" in lines
        assert "// Object: test.fun" in lines
        assert "// Type: function" in lines
        assert "function test()" in lines
        assert "end function" in lines

    def test_format_function_with_statements(self, formatter):
        """Test formatting function with statements."""
        decoded_obj = DecodedObject(
            name="calculate.fun",
            type="function",
            version="pb80_0",
            instructions=[],
            metadata={},
        )

        block = ControlBlock(BlockType.BASIC, 0x100, 0x200, [])
        block.statements = [
            "local_1 = 10",
            "local_2 = 20",
            "return local_1 + local_2",
        ]

        lines = formatter.format_object(decoded_obj, [block], "test.pbd")

        assert "    local_1 = 10" in lines
        assert "    local_2 = 20" in lines
        assert "    return local_1 + local_2" in lines

    def test_format_label_no_indent(self, formatter):
        """Test that labels are not indented."""
        decoded_obj = DecodedObject(
            name="test.fun",
            type="function",
            version="pb80_0",
            instructions=[],
            metadata={},
        )

        block = ControlBlock(BlockType.BASIC, 0x100, 0x200, [])
        block.statements = [
            "local_1 = 10",
            "L_B2A0E:",  # Label should not be indented
            "return local_1",
        ]

        lines = formatter.format_object(decoded_obj, [block], "test.pbd")

        # Find the label line
        label_line = next(line for line in lines if "L_B2A0E:" in line)
        assert label_line == "L_B2A0E:"  # No indentation

    def test_format_if_block(self, formatter):
        """Test formatting if-then-else block."""
        if_block = ControlBlock(BlockType.IF, 0x100, 0x200, [])
        if_block.metadata = {"condition": "local_1 > 0"}

        # Then block
        then_block = ControlBlock(BlockType.BASIC, 0x110, 0x120, [])
        then_block.statements = ["return true"]
        if_block.then_block = then_block

        # Else block
        else_block = ControlBlock(BlockType.BASIC, 0x130, 0x140, [])
        else_block.statements = ["return false"]
        if_block.else_block = else_block

        lines = formatter._format_if_block(if_block)

        assert "if local_1 > 0 then" in lines[0]
        assert "    return true" in lines
        assert "else" in lines
        assert "    return false" in lines
        assert "end if" in lines[-1]

    def test_format_while_loop(self, formatter):
        """Test formatting while loop."""
        while_block = ControlBlock(BlockType.WHILE, 0x100, 0x200, [])
        while_block.metadata = {"condition": "counter < 10"}

        body_block = ControlBlock(BlockType.BASIC, 0x110, 0x120, [])
        body_block.statements = ["counter = counter + 1"]
        while_block.body = body_block

        lines = formatter._format_while_block(while_block)

        assert "do while counter < 10" in lines[0]
        assert "    counter = counter + 1" in lines
        assert "loop" in lines[-1]

    def test_format_for_loop(self, formatter):
        """Test formatting for loop."""
        for_block = ControlBlock(BlockType.FOR, 0x100, 0x200, [])
        for_block.metadata = {
            "variable": "i",
            "start": "1",
            "end": "10",
            "step": "1",
        }

        body_block = ControlBlock(BlockType.BASIC, 0x110, 0x120, [])
        body_block.statements = ["total = total + i"]
        for_block.body = body_block

        lines = formatter._format_for_block(for_block)

        assert "for i = 1 to 10" in lines[0]
        assert "    total = total + i" in lines
        assert "next" in lines[-1]

    def test_format_window_object(self, formatter):
        """Test formatting window object."""
        decoded_obj = DecodedObject(
            name="w_main.win",
            type="window",
            version="pb80_0",
            instructions=[],
            metadata={},
        )

        event_block = ControlBlock(BlockType.EVENT, 0x100, 0x200, [])
        event_block.metadata = {"name": "open"}
        event_block.statements = ["MessageBox('Welcome', 'Hello')"]

        lines = formatter.format_object(decoded_obj, [event_block], "test.pbd")

        assert "window w_main" in lines
        assert "event open()" in lines
        assert "    MessageBox('Welcome', 'Hello')" in lines
        assert "end event" in lines
        assert "end window" in lines

    def test_indent_management(self, formatter):
        """Test indentation level management."""
        # Initial indent
        assert formatter.indent_level == 0

        # Test indenting
        formatter.indent_level = 2
        indented = formatter._indent("statement")
        assert indented == "        statement"  # 2 levels = 8 spaces

        # Test empty line handling
        assert formatter._indent("") == ""
        assert formatter._indent("   ") == "   "

    def test_format_try_block(self, formatter):
        """Test formatting try-catch block."""
        try_block = ControlBlock(BlockType.TRY, 0x100, 0x200, [])

        # Try body
        try_body = ControlBlock(BlockType.BASIC, 0x110, 0x120, [])
        try_body.statements = ["file = FileOpen('data.txt')"]
        try_block.try_body = try_body

        # Catch block
        try_block.catch_blocks = [
            {
                "type": "IOException",
                "variable": "ex",
                "body": ControlBlock(BlockType.BASIC, 0x130, 0x140, []),
            },
        ]
        try_block.catch_blocks[0]["body"].statements = [
            "MessageBox('Error', ex.getMessage())",
        ]

        lines = formatter._format_try_block(try_block)

        assert "try" in lines[0]
        assert "    file = FileOpen('data.txt')" in lines
        assert "catch (IOException ex)" in lines
        assert "    MessageBox('Error', ex.getMessage())" in lines
        assert "end try" in lines[-1]

    def test_format_choose_case(self, formatter):
        """Test formatting choose case block."""
        choose_block = ControlBlock(BlockType.CHOOSE_CASE, 0x100, 0x200, [])
        choose_block.metadata = {"expression": "option"}

        # Case 1
        case1_body = ControlBlock(BlockType.BASIC, 0x110, 0x120, [])
        case1_body.statements = ["result = 'Option A'"]

        # Case 2
        case2_body = ControlBlock(BlockType.BASIC, 0x130, 0x140, [])
        case2_body.statements = ["result = 'Option B'"]

        choose_block.cases = [
            {"value": "1", "body": case1_body},
            {"value": "2", "body": case2_body},
        ]

        # Default case
        default_body = ControlBlock(BlockType.BASIC, 0x150, 0x160, [])
        default_body.statements = ["result = 'Unknown'"]
        choose_block.default_case = default_body

        lines = formatter._format_choose_case_block(choose_block)

        assert "choose case option" in lines[0]
        assert "    case 1" in lines
        assert "        result = 'Option A'" in lines
        assert "    case 2" in lines
        assert "        result = 'Option B'" in lines
        assert "    case else" in lines
        assert "        result = 'Unknown'" in lines
        assert "end choose" in lines[-1]
