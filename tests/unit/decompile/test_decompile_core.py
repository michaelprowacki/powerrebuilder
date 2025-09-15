"""Tests for decompile core modules."""

import pytest

from src.model.unified_expressions import reconstructor import ExpressionReconstructor
from src.decompile.core.output import OutputFormatter
from src.decompile.pcode.decoder import DecodedObject, PCodeInstruction
from src.decompile.pcode.decoder import PCodeDecoderV2 as PCodeDecoder
from src.decompile.core.formatter import SimpleFormatter


class TestPCodeDecoder:
    """Test cases for P-code decoder."""

    def setup_method(self):




        """Set up test instances."""
        self.decoder = PCodeDecoder()

    def test_decode_simple_object(self):




        """Test decoding a simple P-code object."""
        # Create a mock file handle
        from io import BytesIO
        pcode_data = b"\x00\x01\x02\x03"  # Simple test data
        mock_handle = BytesIO(pcode_data)

        result = self.decoder.decode_pbd_object(mock_handle, 0, len(pcode_data), "test_object")

        assert isinstance(result, DecodedObject)
        assert result.name == "test_object"
        assert hasattr(result, "instructions")

    def test_decode_empty_object(self):




        """Test decoding empty P-code data."""
        from io import BytesIO
        mock_handle = BytesIO(b"")

        result = self.decoder.decode_pbd_object(mock_handle, 0, 0, "empty_object")

        assert result.name == "empty_object"
        assert len(result.instructions) == 0

    def test_decode_with_error_handling(self):




        """Test decoder error handling."""
        from io import BytesIO
        # Invalid P-code data
        invalid_data = b"\xFF\xFF\xFF\xFF" * 100
        mock_handle = BytesIO(invalid_data)

        # Should handle gracefully
        result = self.decoder.decode_pbd_object(mock_handle, 0, len(invalid_data), "error_object")
        assert result is not None


class TestExpressionReconstructor:
    """Test cases for expression reconstruction."""

    def setup_method(self):




        """Set up test instances."""
        self.reconstructor = ExpressionReconstructor()

    def test_reconstruct_simple_expression(self):




        """Test reconstructing a simple expression."""
        # Mock opcode for simple assignment
        opcode = PCodeInstruction(
            address=0,
            opcode=b"\x01",  # Mock assignment opcode
            opcode_name="ASSIGN",
            operands=b"\x01\x02",
            operand_values=[1, 2],
            text_format="ASSIGN 1, 2",
        )

        expr = self.reconstructor.reconstruct_expression([opcode])
        assert isinstance(expr, str)

    def test_reconstruct_arithmetic_expression(self):




        """Test reconstructing arithmetic expressions."""
        # Mock opcodes for arithmetic
        opcodes = [
            PCodeInstruction(address=0, opcode=b"\x10", opcode_name="LOAD", operands=b"\x01", operand_values=[1], text_format="LOAD 1"),
            PCodeInstruction(address=1, opcode=b"\x11", opcode_name="LOAD", operands=b"\x02", operand_values=[2], text_format="LOAD 2"),
            PCodeInstruction(address=2, opcode=b"\x20", opcode_name="ADD", operands=b"", operand_values=[], text_format="ADD"),
        ]

        expr = self.reconstructor.reconstruct_expression(opcodes)
        assert isinstance(expr, str)

    def test_reconstruct_comparison(self):




        """Test reconstructing comparison expressions."""
        # Mock comparison opcodes
        opcodes = [
            PCodeInstruction(address=0, opcode=b"\x10", opcode_name="LOAD", operands=b"\x01", operand_values=[1], text_format="LOAD 1"),
            PCodeInstruction(address=1, opcode=b"\x10", opcode_name="LOAD", operands=b"\x02", operand_values=[2], text_format="LOAD 2"),
            PCodeInstruction(address=2, opcode=b"\x30", opcode_name="COMPARE", operands=b"", operand_values=[], text_format="COMPARE"),
        ]

        expr = self.reconstructor.reconstruct_expression(opcodes)
        assert isinstance(expr, str)


class TestOutputFormatter:
    """Test cases for output formatting."""

    def setup_method(self):




        """Set up test instances."""
        self.formatter = OutputFormatter()

    def test_format_simple_object(self):




        """Test formatting a simple decoded object."""
        decoded_obj = DecodedObject(
            name="test_function",
            type="function",
            version=None,
            instructions=[],
            metadata={"returns": "integer"},
        )

        output = self.formatter.format_object(decoded_obj)
        assert isinstance(output, list)
        assert any("test_function" in line for line in output)

    def test_format_with_control_blocks(self):




        """Test formatting with control flow blocks."""
        decoded_obj = DecodedObject(
            name="test_method",
            type="function",
            version=None,
            instructions=[],
        )

        control_blocks = [
            {"type": "if", "start": 0, "end": 10},
            {"type": "loop", "start": 20, "end": 30},
        ]

        output = self.formatter.format_object(decoded_obj, control_blocks)
        assert isinstance(output, list)

    def test_format_header_generation(self):




        """Test header comment generation."""
        header = self.formatter._generate_header(
            "w_main",
            "window",
            "main.pbl",
        )

        assert isinstance(header, list)
        assert any("w_main" in line for line in header)
        assert any("window" in line for line in header)

    def test_format_metadata_handling(self):




        """Test metadata formatting."""
        decoded_obj = DecodedObject(
            name="dw_list",
            type="datawindow",
            version=None,
            instructions=[],
            metadata={
                "sql": "SELECT * FROM customers",
                "columns": ["id", "name", "balance"],
            },
        )

        output = self.formatter.format_object(decoded_obj)
        assert isinstance(output, list)
        # Should include SQL information
        assert any("SELECT" in line for line in output)


class TestSimpleFormatter:
    """Test cases for simple formatter."""

    def setup_method(self):




        """Set up test instances."""
        self.formatter = SimpleFormatter()

    def test_format_opcode(self):




        """Test formatting individual opcodes."""
        opcode = PCodeInstruction(
            address=100,
            opcode=b"\x01",
            opcode_name="OPCODE_01",
            operands=b"\x0a\x14",
            operand_values=[10, 20],
            text_format="OPCODE_01 10, 20",
        )

        result = self.formatter.format_opcode(opcode)
        assert isinstance(result, str)
        assert "0x01" in result or "01" in result

    def test_format_opcode_with_mnemonic(self):




        """Test formatting with mnemonic names."""
        opcode = PCodeInstruction(
            address=0,
            opcode=b"\x10",  # Assume this is LOAD
            opcode_name="LOAD",
            operands=b"\x05",
            operand_values=[5],
            text_format="LOAD 5",
        )

        result = self.formatter.format_opcode(opcode)
        assert "LOAD" in result

    def test_format_special_opcodes(self):




        """Test formatting special opcodes."""
        # Test jump opcode
        jump_opcode = PCodeInstruction(
            address=100,
            opcode=b"\x50",  # Assume jump
            opcode_name="JMP",
            operands=b"\xc8",  # Jump target = 200
            operand_values=[200],
            text_format="JMP 200",
        )

        result = self.formatter.format_opcode(jump_opcode)
        assert isinstance(result, str)

    def test_format_with_indentation(self):




        """Test formatting with indentation."""
        opcodes = [
            PCodeInstruction(address=0, opcode=b"\x01", opcode_name="OP1", operands=b"", operand_values=[], text_format="OP1"),
            PCodeInstruction(address=1, opcode=b"\x02", opcode_name="OP2", operands=b"", operand_values=[], text_format="OP2"),
        ]

        result = self.formatter.format_opcodes(opcodes, indent_level=2)
        assert all(line.startswith("    ") or line == "" for line in result)


class TestDecompileIntegration:
    """Integration tests for decompile components."""

    def test_full_decompile_flow(self):




        """Test the full decompile flow."""
        from io import BytesIO
        # Create test P-code data
        test_data = b"\x10\x01\x11\x02\x20\x00"  # Load 1, Load 2, Add
        mock_handle = BytesIO(test_data)

        # Decode
        decoder = PCodeDecoder()
        decoded = decoder.decode_pbd_object(mock_handle, 0, len(test_data), "test_add")

        # Format
        formatter = OutputFormatter()
        output = formatter.format_object(decoded)

        assert isinstance(output, list)
        assert len(output) > 0

    def test_error_recovery(self):




        """Test error recovery in decompile flow."""
        from io import BytesIO
        # Invalid data that should trigger error recovery
        bad_data = b"\xFF" * 1000
        mock_handle = BytesIO(bad_data)

        decoder = PCodeDecoder()
        decoded = decoder.decode_pbd_object(mock_handle, 0, len(bad_data), "bad_object")

        # Should still produce some output
        formatter = OutputFormatter()
        output = formatter.format_object(decoded)

        assert isinstance(output, list)
        # Should include error information
        assert any("error" in line.lower() or "failed" in line.lower()
                  for line in output)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
