#!/usr/bin/env python3
"""Comprehensive tests for the simple formatter."""

from src.decompile.core.formatter import SimpleFormatter
from src.decompile.pcode.decoder import DecodedObject, PCodeInstruction


class TestSimpleFormatter:
    """Test the simple formatter."""

    def test_format_function_basic(self):
        """Test formatting a basic function."""
        formatter = SimpleFormatter()

        # Create a decoded object for a function
        decoded_obj = DecodedObject(
            name="calculate",
            type="function",
            instructions=[
                PCodeInstruction(
                    offset=0, opcode=0x01, opcode_name="PUSH", operands=[]
                ),
                PCodeInstruction(
                    offset=2, opcode=0x99, opcode_name="RETURN", operands=[]
                ),
            ],
        )

        result = formatter.format_object(decoded_obj, "test.fun")

        # Verify structure
        assert "// Source: test.fun" in result
        assert "// Object: calculate" in result
        assert "// Type: function" in result
        assert "global function integer calculate()" in result
        assert "end function" in result
        assert "return 0" in result

    def test_format_function_with_arithmetic(self):
        """Test formatting a function with arithmetic operations."""
        formatter = SimpleFormatter()

        decoded_obj = DecodedObject(
            name="compute",
            type="function",
            instructions=[
                PCodeInstruction(offset=0, opcode=0x10, opcode_name="ADD", operands=[]),
                PCodeInstruction(offset=2, opcode=0x11, opcode_name="SUB", operands=[]),
                PCodeInstruction(
                    offset=4, opcode=0x99, opcode_name="RETURN", operands=[]
                ),
            ],
        )

        result = formatter.format_object(decoded_obj)
        formatted = "\n".join(result)

        assert "// Arithmetic operations detected" in formatted
        assert "integer li_result = 0" in formatted
        assert "// TODO: Implement calculation logic" in formatted
        assert "return li_result" in formatted

    def test_format_function_with_database(self):
        """Test formatting a function with database operations."""
        formatter = SimpleFormatter()

        decoded_obj = DecodedObject(
            name="fetch_data",
            type="function",
            instructions=[
                PCodeInstruction(
                    offset=0, opcode=0x50, opcode_name="DBSELECT", operands=[]
                ),
                PCodeInstruction(
                    offset=2, opcode=0x51, opcode_name="DBFETCH", operands=[]
                ),
                PCodeInstruction(
                    offset=4, opcode=0x99, opcode_name="RETURN", operands=[]
                ),
            ],
        )

        result = formatter.format_object(decoded_obj)
        formatted = "\n".join(result)

        assert "// Database operations detected" in formatted
        assert "integer li_result = 0" in formatted
        assert "// TODO: Implement database logic" in formatted
        assert "return li_result" in formatted

    def test_format_window_basic(self):
        """Test formatting a basic window."""
        formatter = SimpleFormatter()

        decoded_obj = DecodedObject(
            name="w_main",
            type="window",
            instructions=[
                PCodeInstruction(
                    offset=0, opcode=0x99, opcode_name="RETURN", operands=[]
                ),
            ],
        )

        result = formatter.format_object(decoded_obj)
        formatted = "\n".join(result)

        assert "global type w_main from window" in formatted
        assert "end type" in formatted
        assert "global w_main w_main" in formatted
        assert "on w_main.create" in formatted
        assert "end on" in formatted
        assert "on w_main.destroy" in formatted

    def test_format_window_with_events(self):
        """Test formatting a window with detected events."""
        formatter = SimpleFormatter()

        decoded_obj = DecodedObject(
            name="w_dialog",
            type="window",
            instructions=[
                PCodeInstruction(
                    offset=0, opcode=0x80, opcode_name="EVENTCALL", operands=[]
                ),
                PCodeInstruction(
                    offset=2, opcode=0x99, opcode_name="RETURN", operands=[]
                ),
            ],
        )

        result = formatter.format_object(decoded_obj)
        formatted = "\n".join(result)

        # Should detect events
        assert "event clicked()" in formatted or "event constructor()" in formatted
        assert "// Event implementation" in formatted
        assert "return 0" in formatted
        assert "end event" in formatted

    def test_format_userobject_basic(self):
        """Test formatting a basic user object."""
        formatter = SimpleFormatter()

        decoded_obj = DecodedObject(
            name="u_custom",
            type="userobject",
            instructions=[
                PCodeInstruction(
                    offset=0, opcode=0x99, opcode_name="RETURN", operands=[]
                ),
            ],
        )

        result = formatter.format_object(decoded_obj)
        formatted = "\n".join(result)

        assert "global type u_custom from userobject" in formatted
        assert "end type" in formatted
        assert "global u_custom u_custom" in formatted
        assert "on u_custom.create" in formatted
        assert "on u_custom.destroy" in formatted

    def test_format_userobject_with_functions(self):
        """Test formatting a user object with detected functions."""
        formatter = SimpleFormatter()

        # Many calls should detect multiple functions
        instructions = []
        for i in range(12):
            instructions.append(
                PCodeInstruction(
                    offset=i * 2, opcode=0x30, opcode_name="CALL", operands=[]
                ),
            )
        instructions.append(
            PCodeInstruction(offset=24, opcode=0x99, opcode_name="RETURN", operands=[]),
        )

        decoded_obj = DecodedObject(
            name="u_processor",
            type="userobject",
            instructions=instructions,
        )

        result = formatter.format_object(decoded_obj)
        formatted = "\n".join(result)

        # Should detect multiple functions based on call count > 10
        assert "public function integer initialize()" in formatted
        assert "public function integer process()" in formatted
        assert "public function integer validate()" in formatted
        assert "// Function implementation" in formatted

    def test_format_menu(self):
        """Test formatting a menu object."""
        formatter = SimpleFormatter()

        decoded_obj = DecodedObject(
            name="m_main",
            type="menu",
            instructions=[
                PCodeInstruction(
                    offset=0, opcode=0x99, opcode_name="RETURN", operands=[]
                ),
            ],
        )

        result = formatter.format_object(decoded_obj)
        formatted = "\n".join(result)

        assert "global type m_main from menu" in formatted
        assert "end type" in formatted
        assert "global m_main m_main" in formatted
        assert "on m_main.create" in formatted
        assert "m_main = this" in formatted
        assert "on m_main.destroy" in formatted

    def test_format_application(self):
        """Test formatting an application object."""
        formatter = SimpleFormatter()

        decoded_obj = DecodedObject(
            name="app",
            type="application",
            instructions=[
                PCodeInstruction(
                    offset=0, opcode=0x99, opcode_name="RETURN", operands=[]
                ),
            ],
        )

        result = formatter.format_object(decoded_obj)
        formatted = "\n".join(result)

        assert "global type app from application" in formatted
        assert "end type" in formatted
        assert "global app app" in formatted
        assert "event open()" in formatted
        assert "// Application initialization" in formatted
        assert "event close()" in formatted
        assert "// Application cleanup" in formatted

    def test_format_unknown_type_defaults_to_function(self):
        """Test that unknown types default to function formatting."""
        formatter = SimpleFormatter()

        decoded_obj = DecodedObject(
            name="unknown",
            type="datastore",  # Unknown type
            instructions=[
                PCodeInstruction(
                    offset=0, opcode=0x99, opcode_name="RETURN", operands=[]
                ),
            ],
        )

        result = formatter.format_object(decoded_obj)
        formatted = "\n".join(result)

        # Should format as function
        assert "global function integer unknown()" in formatted
        assert "end function" in formatted

    def test_object_name_with_extension(self):
        """Test handling object names with extensions."""
        formatter = SimpleFormatter()

        decoded_obj = DecodedObject(
            name="calculate.fun",  # Name with extension
            type="function",
            instructions=[
                PCodeInstruction(
                    offset=0, opcode=0x99, opcode_name="RETURN", operands=[]
                ),
            ],
        )

        result = formatter.format_object(decoded_obj)
        formatted = "\n".join(result)

        # Should strip extension
        assert "global function integer calculate()" in formatted
        assert (
            "calculate.fun" not in formatted.split("//")[2]
        )  # Not in function declaration

    def test_empty_instructions(self):
        """Test formatting with no instructions."""
        formatter = SimpleFormatter()

        decoded_obj = DecodedObject(
            name="empty",
            type="function",
            instructions=[],
        )

        result = formatter.format_object(decoded_obj)
        formatted = "\n".join(result)

        # Should still generate valid structure
        assert "global function integer empty()" in formatted
        assert "// TODO: Implementation" in formatted
        assert "return 0" in formatted
        assert "end function" in formatted

    def test_detect_functions_various_call_counts(self):
        """Test function detection with various call counts."""
        formatter = SimpleFormatter()

        # Test with 0 calls
        decoded_obj = DecodedObject(
            name="test",
            type="userobject",
            instructions=[],
        )
        functions = formatter._detect_functions(decoded_obj)
        assert len(functions) == 0

        # Test with 3 calls (>0)
        decoded_obj.instructions = [
            PCodeInstruction(offset=i * 2, opcode=0x30, opcode_name="CALL", operands=[])
            for i in range(3)
        ]
        functions = formatter._detect_functions(decoded_obj)
        assert "initialize" in functions
        assert len(functions) == 1

        # Test with 7 calls (>5)
        decoded_obj.instructions = [
            PCodeInstruction(offset=i * 2, opcode=0x30, opcode_name="CALL", operands=[])
            for i in range(7)
        ]
        functions = formatter._detect_functions(decoded_obj)
        assert "initialize" in functions
        assert "process" in functions
        assert len(functions) == 2

        # Test with different call types
        decoded_obj.instructions = [
            PCodeInstruction(offset=0, opcode=0x30, opcode_name="CALL", operands=[]),
            PCodeInstruction(offset=2, opcode=0x31, opcode_name="CALLEXT", operands=[]),
            PCodeInstruction(
                offset=4, opcode=0x32, opcode_name="CALLVIRT", operands=[]
            ),
        ]
        functions = formatter._detect_functions(decoded_obj)
        assert "initialize" in functions  # Should detect CALL variants

    def test_detect_events_no_events(self):
        """Test event detection with no event calls."""
        formatter = SimpleFormatter()

        decoded_obj = DecodedObject(
            name="test",
            type="window",
            instructions=[
                PCodeInstruction(
                    offset=0, opcode=0x01, opcode_name="PUSH", operands=[]
                ),
                PCodeInstruction(
                    offset=2, opcode=0x99, opcode_name="RETURN", operands=[]
                ),
            ],
        )

        events = formatter._detect_events(decoded_obj)
        assert len(events) == 0

    def test_minimal_body_no_special_ops(self):
        """Test minimal body generation with no special operations."""
        formatter = SimpleFormatter()

        decoded_obj = DecodedObject(
            name="test",
            type="function",
            instructions=[
                PCodeInstruction(
                    offset=0, opcode=0x01, opcode_name="PUSH", operands=[]
                ),
                PCodeInstruction(offset=2, opcode=0x02, opcode_name="POP", operands=[]),
            ],
        )

        body = formatter._generate_minimal_body(decoded_obj)
        formatted = "\n".join(body)

        assert "// TODO: Implementation" in formatted
        assert "return 0" in formatted
        assert "Database operations" not in formatted
        assert "Arithmetic operations" not in formatted


class TestFormatterEdgeCases:
    """Test edge cases and error conditions."""

    def test_format_with_mixed_operations(self):
        """Test formatting with both database and arithmetic operations."""
        formatter = SimpleFormatter()

        decoded_obj = DecodedObject(
            name="complex",
            type="function",
            instructions=[
                PCodeInstruction(offset=0, opcode=0x10, opcode_name="ADD", operands=[]),
                PCodeInstruction(
                    offset=2, opcode=0x50, opcode_name="DBSELECT", operands=[]
                ),
                PCodeInstruction(
                    offset=4, opcode=0x99, opcode_name="RETURN", operands=[]
                ),
            ],
        )

        result = formatter.format_object(decoded_obj)
        formatted = "\n".join(result)

        # Database operations should take precedence
        assert "// Database operations detected" in formatted
        assert "// Arithmetic operations detected" not in formatted

    def test_format_very_long_name(self):
        """Test formatting with very long object names."""
        formatter = SimpleFormatter()

        long_name = "a" * 100
        decoded_obj = DecodedObject(
            name=long_name,
            type="function",
            instructions=[
                PCodeInstruction(
                    offset=0, opcode=0x99, opcode_name="RETURN", operands=[]
                ),
            ],
        )

        result = formatter.format_object(decoded_obj)
        formatted = "\n".join(result)

        # Should handle long names
        assert f"global function integer {long_name}()" in formatted

    def test_special_characters_in_name(self):
        """Test handling special characters in object names."""
        formatter = SimpleFormatter()

        decoded_obj = DecodedObject(
            name="test-object.fun",  # Name with special chars
            type="function",
            instructions=[
                PCodeInstruction(
                    offset=0, opcode=0x99, opcode_name="RETURN", operands=[]
                ),
            ],
        )

        result = formatter.format_object(decoded_obj)
        formatted = "\n".join(result)

        # Should handle name (PowerBuilder may have restrictions)
        assert "global function integer test-object()" in formatted
