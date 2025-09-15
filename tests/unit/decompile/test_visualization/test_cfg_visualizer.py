"""Tests for Control Flow Graph visualization."""

import tempfile
from pathlib import Path

from src.decompile.cfg_visualizer import (
    CFGVisualizer,
    VisualizationLevel,
    VisualizationOptions,
)
from src.decompile.pcode.decoder import PCodeInstruction


class TestCFGVisualizer:
    """Test CFG visualization functionality."""

    def test_basic_visualization(self):
        """Test basic CFG visualization."""
        # Create sample instructions
        instructions = [
            PCodeInstruction(
                address=0x00,
                opcode=b"\x10",
                opcode_name="PUSHCONST",
                operands=b"\x0a",
                operand_values=[10],
                text_format="PUSHCONST 10",
                opcode_value=0x10,
            ),
            PCodeInstruction(
                address=0x02,
                opcode=b"\x11",
                opcode_name="PUSHVAR",
                operands=b"\x01",
                operand_values=[1],
                text_format="PUSHVAR 1",
                opcode_value=0x11,
            ),
            PCodeInstruction(
                address=0x04,
                opcode=b"\x30",
                opcode_name="GT",
                operands=b"",
                operand_values=[],
                text_format="GT",
                opcode_value=0x30,
            ),
            PCodeInstruction(
                address=0x06,
                opcode=b"\x41",
                opcode_name="JUMPFALSE",
                operands=b"\x10",
                operand_values=[0x10],
                text_format="JUMPFALSE 0x10",
                opcode_value=0x41,
            ),
            PCodeInstruction(
                address=0x08,
                opcode=b"\x50",
                opcode_name="CALL",
                operands=b"process",
                operand_values=["process"],
                text_format="CALL process",
                opcode_value=0x50,
            ),
            PCodeInstruction(
                address=0x0A,
                opcode=b"\x42",
                opcode_name="JUMP",
                operands=b"\x12",
                operand_values=[0x12],
                text_format="JUMP 0x12",
                opcode_value=0x42,
            ),
            PCodeInstruction(
                address=0x10,
                opcode=b"\x51",
                opcode_name="CALL",
                operands=b"skip",
                operand_values=["skip"],
                text_format="CALL skip",
                opcode_value=0x51,
            ),
            PCodeInstruction(
                address=0x12,
                opcode=b"\x60",
                opcode_name="RETURN",
                operands=b"",
                operand_values=[],
                text_format="RETURN",
                opcode_value=0x60,
            ),
        ]

        # Create visualizer
        visualizer = CFGVisualizer()

        # Generate visualization
        dot_content = visualizer.visualize_method("test_method", instructions)

        # Verify DOT content
        assert 'digraph "test_method_cfg"' in dot_content
        assert "Entry" in dot_content
        assert "Exit" in dot_content
        assert "GT" in dot_content  # The comparison operation
        assert "[IF]" in dot_content  # The IF block type
        assert "process" in dot_content

    def test_visualization_options(self):
        """Test visualization with custom options."""
        instructions = [
            PCodeInstruction(
                address=0x00,
                opcode=b"\x10",
                opcode_name="PUSHCONST",
                operands=b"\x05",
                operand_values=[5],
                text_format="PUSHCONST 5",
                opcode_value=0x10,
            ),
            PCodeInstruction(
                address=0x02,
                opcode=b"\x60",
                opcode_name="RETURN",
                operands=b"",
                operand_values=[],
                text_format="RETURN",
                opcode_value=0x60,
            ),
        ]

        # Test with different options
        options = VisualizationOptions(
            level=VisualizationLevel.METHOD,
            show_instructions=False,
            show_addresses=False,
            font_name="Arial",
            font_size=12,
            direction="LR",
        )

        visualizer = CFGVisualizer(options)
        dot_content = visualizer.visualize_method("simple", instructions)

        # Verify options are applied
        assert "Arial" in dot_content
        assert "fontsize=12" in dot_content
        assert "rankdir=LR" in dot_content  # Left-to-right direction
        # Instructions should not be shown when show_instructions=False
        assert "PUSHCONST" not in dot_content
        assert "RETURN" not in dot_content

    def test_if_else_visualization(self):
        """Test visualization of if-else structure."""
        instructions = [
            # If condition
            PCodeInstruction(
                address=0x00,
                opcode=b"\x11",
                opcode_name="PUSHVAR",
                operands=b"\x01",
                operand_values=[1],
                text_format="PUSHVAR 1",
                opcode_value=0x11,
            ),
            PCodeInstruction(
                address=0x02,
                opcode=b"\x41",
                opcode_name="JUMPFALSE",
                operands=b"\x08",
                operand_values=[0x08],
                text_format="JUMPFALSE 0x08",
                opcode_value=0x41,
            ),
            # Then branch
            PCodeInstruction(
                address=0x04,
                opcode=b"\x50",
                opcode_name="CALL",
                operands=b"then_func",
                operand_values=["then_func"],
                text_format="CALL then_func",
                opcode_value=0x50,
            ),
            PCodeInstruction(
                address=0x06,
                opcode=b"\x42",
                opcode_name="JUMP",
                operands=b"\x0a",
                operand_values=[0x0A],
                text_format="JUMP 0x0A",
                opcode_value=0x42,
            ),
            # Else branch
            PCodeInstruction(
                address=0x08,
                opcode=b"\x50",
                opcode_name="CALL",
                operands=b"else_func",
                operand_values=["else_func"],
                text_format="CALL else_func",
                opcode_value=0x50,
            ),
            # After if
            PCodeInstruction(
                address=0x0A,
                opcode=b"\x60",
                opcode_name="RETURN",
                operands=b"",
                operand_values=[],
                text_format="RETURN",
                opcode_value=0x60,
            ),
        ]

        visualizer = CFGVisualizer()
        dot_content = visualizer.visualize_method("if_else_test", instructions)

        # Check for conditional structure
        assert "[IF]" in dot_content  # IF block detected
        assert "then_func" in dot_content
        assert "else_func" in dot_content

    def test_loop_visualization(self):
        """Test visualization of loop structures."""
        instructions = [
            # Initialize counter
            PCodeInstruction(
                address=0x00,
                opcode=b"\x10",
                opcode_name="PUSHCONST",
                operands=b"\x00",
                operand_values=[0],
                text_format="PUSHCONST 0",
                opcode_value=0x10,
            ),
            PCodeInstruction(
                address=0x02,
                opcode=b"\x20",
                opcode_name="POPVAR",
                operands=b"\x01",
                operand_values=[1],
                text_format="POPVAR 1",
                opcode_value=0x20,
            ),
            # Loop condition
            PCodeInstruction(
                address=0x04,
                opcode=b"\x11",
                opcode_name="PUSHVAR",
                operands=b"\x01",
                operand_values=[1],
                text_format="PUSHVAR 1",
                opcode_value=0x11,
            ),
            PCodeInstruction(
                address=0x06,
                opcode=b"\x10",
                opcode_name="PUSHCONST",
                operands=b"\x0a",
                operand_values=[10],
                text_format="PUSHCONST 10",
                opcode_value=0x10,
            ),
            PCodeInstruction(
                address=0x08,
                opcode=b"\x31",
                opcode_name="LT",
                operands=b"",
                operand_values=[],
                text_format="LT",
                opcode_value=0x31,
            ),
            PCodeInstruction(
                address=0x0A,
                opcode=b"\x41",
                opcode_name="JUMPFALSE",
                operands=b"\x14",
                operand_values=[0x14],
                text_format="JUMPFALSE 0x14",
                opcode_value=0x41,
            ),
            # Loop body
            PCodeInstruction(
                address=0x0C,
                opcode=b"\x50",
                opcode_name="CALL",
                operands=b"process",
                operand_values=["process"],
                text_format="CALL process",
                opcode_value=0x50,
            ),
            # Increment
            PCodeInstruction(
                address=0x0E,
                opcode=b"\x11",
                opcode_name="PUSHVAR",
                operands=b"\x01",
                operand_values=[1],
                text_format="PUSHVAR 1",
                opcode_value=0x11,
            ),
            PCodeInstruction(
                address=0x10,
                opcode=b"\x10",
                opcode_name="PUSHCONST",
                operands=b"\x01",
                operand_values=[1],
                text_format="PUSHCONST 1",
                opcode_value=0x10,
            ),
            PCodeInstruction(
                address=0x11,
                opcode=b"\x33",
                opcode_name="ADD",
                operands=b"",
                operand_values=[],
                text_format="ADD",
                opcode_value=0x33,
            ),
            PCodeInstruction(
                address=0x12,
                opcode=b"\x20",
                opcode_name="POPVAR",
                operands=b"\x01",
                operand_values=[1],
                text_format="POPVAR 1",
                opcode_value=0x20,
            ),
            # Jump back
            PCodeInstruction(
                address=0x13,
                opcode=b"\x42",
                opcode_name="JUMP",
                operands=b"\x04",
                operand_values=[0x04],
                text_format="JUMP 0x04",
                opcode_value=0x42,
            ),
            # After loop
            PCodeInstruction(
                address=0x14,
                opcode=b"\x60",
                opcode_name="RETURN",
                operands=b"",
                operand_values=[],
                text_format="RETURN",
                opcode_value=0x60,
            ),
        ]

        visualizer = CFGVisualizer()
        dot_content = visualizer.visualize_method("loop_test", instructions)

        # Check for loop structure
        assert "[FOR]" in dot_content  # FOR loop detected
        # Note: Control flow analyzer may restructure loops

    def test_class_visualization(self):
        """Test visualization of an entire class."""
        methods = {
            "method1": [
                PCodeInstruction(
                    address=0x00,
                    opcode=b"\x10",
                    opcode_name="PUSHCONST",
                    operands=b"\x01",
                    operand_values=[1],
                    text_format="PUSHCONST 1",
                    opcode_value=0x10,
                ),
                PCodeInstruction(
                    address=0x02,
                    opcode=b"\x60",
                    opcode_name="RETURN",
                    operands=b"",
                    operand_values=[],
                    text_format="RETURN",
                    opcode_value=0x60,
                ),
            ],
            "method2": [
                PCodeInstruction(
                    address=0x00,
                    opcode=b"\x11",
                    opcode_name="PUSHVAR",
                    operands=b"\x01",
                    operand_values=[1],
                    text_format="PUSHVAR 1",
                    opcode_value=0x11,
                ),
                PCodeInstruction(
                    address=0x02,
                    opcode=b"\x41",
                    opcode_name="JUMPFALSE",
                    operands=b"\x06",
                    operand_values=[0x06],
                    text_format="JUMPFALSE 0x06",
                    opcode_value=0x41,
                ),
                PCodeInstruction(
                    address=0x04,
                    opcode=b"\x50",
                    opcode_name="CALL",
                    operands=b"helper",
                    operand_values=["helper"],
                    text_format="CALL helper",
                    opcode_value=0x50,
                ),
                PCodeInstruction(
                    address=0x06,
                    opcode=b"\x60",
                    opcode_name="RETURN",
                    operands=b"",
                    operand_values=[],
                    text_format="RETURN",
                    opcode_value=0x60,
                ),
            ],
        }

        visualizer = CFGVisualizer()
        dot_content = visualizer.visualize_class("TestClass", methods)

        # Check for subgraphs
        assert 'subgraph "cluster_method1"' in dot_content
        assert 'subgraph "cluster_method2"' in dot_content
        assert 'label="TestClass Control Flow"' in dot_content
        assert 'label="method1"' in dot_content
        assert 'label="method2"' in dot_content

    def test_save_to_file(self):
        """Test saving visualization to file."""
        instructions = [
            PCodeInstruction(
                address=0x00,
                opcode=b"\x10",
                opcode_name="PUSHCONST",
                operands=b"\x2a",
                operand_values=[42],
                text_format="PUSHCONST 42",
                opcode_value=0x10,
            ),
            PCodeInstruction(
                address=0x02,
                opcode=b"\x60",
                opcode_name="RETURN",
                operands=b"",
                operand_values=[],
                text_format="RETURN",
                opcode_value=0x60,
            ),
        ]

        visualizer = CFGVisualizer()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_cfg.dot"

            # Generate and save
            dot_content = visualizer.visualize_method(
                "save_test",
                instructions,
                output_path,
            )

            # Verify file was created
            assert output_path.exists()

            # Verify content
            saved_content = output_path.read_text()
            assert saved_content == dot_content
            assert "save_test_cfg" in saved_content

    def test_dark_color_scheme(self):
        """Test dark color scheme."""
        instructions = [
            PCodeInstruction(
                address=0x00,
                opcode=b"\x10",
                opcode_name="PUSHCONST",
                operands=b"\x01",
                operand_values=[1],
                text_format="PUSHCONST 1",
                opcode_value=0x10,
            ),
            PCodeInstruction(
                address=0x02,
                opcode=b"\x60",
                opcode_name="RETURN",
                operands=b"",
                operand_values=[],
                text_format="RETURN",
                opcode_value=0x60,
            ),
        ]

        options = VisualizationOptions(color_scheme="dark")
        visualizer = CFGVisualizer(options)

        dot_content = visualizer.visualize_method("dark_test", instructions)

        # Check for dark colors
        assert "#37474F" in dot_content  # Dark basic block color
        assert "#1B5E20" in dot_content  # Dark entry color

    def test_summary_stats(self):
        """Test CFG summary statistics generation."""
        # Create a more complex set of instructions
        instructions = [
            # If-else structure
            PCodeInstruction(
                address=0x00,
                opcode=b"\x11",
                opcode_name="PUSHVAR",
                operands=b"\x01",
                operand_values=[1],
                text_format="PUSHVAR 1",
                opcode_value=0x11,
            ),
            PCodeInstruction(
                address=0x02,
                opcode=b"\x41",
                opcode_name="JUMPFALSE",
                operands=b"\x08",
                operand_values=[0x08],
                text_format="JUMPFALSE 0x08",
                opcode_value=0x41,
            ),
            PCodeInstruction(
                address=0x04,
                opcode=b"\x50",
                opcode_name="CALL",
                operands=b"func1",
                operand_values=["func1"],
                text_format="CALL func1",
                opcode_value=0x50,
            ),
            PCodeInstruction(
                address=0x06,
                opcode=b"\x42",
                opcode_name="JUMP",
                operands=b"\x0a",
                operand_values=[0x0A],
                text_format="JUMP 0x0A",
                opcode_value=0x42,
            ),
            PCodeInstruction(
                address=0x08,
                opcode=b"\x50",
                opcode_name="CALL",
                operands=b"func2",
                operand_values=["func2"],
                text_format="CALL func2",
                opcode_value=0x50,
            ),
            # Loop
            PCodeInstruction(
                address=0x0A,
                opcode=b"\x11",
                opcode_name="PUSHVAR",
                operands=b"\x02",
                operand_values=[2],
                text_format="PUSHVAR 2",
                opcode_value=0x11,
            ),
            PCodeInstruction(
                address=0x0C,
                opcode=b"\x41",
                opcode_name="JUMPFALSE",
                operands=b"\x12",
                operand_values=[0x12],
                text_format="JUMPFALSE 0x12",
                opcode_value=0x41,
            ),
            PCodeInstruction(
                address=0x0E,
                opcode=b"\x50",
                opcode_name="CALL",
                operands=b"loop_body",
                operand_values=["loop_body"],
                text_format="CALL loop_body",
                opcode_value=0x50,
            ),
            PCodeInstruction(
                address=0x10,
                opcode=b"\x42",
                opcode_name="JUMP",
                operands=b"\x0a",
                operand_values=[0x0A],
                text_format="JUMP 0x0A",
                opcode_value=0x42,
            ),
            PCodeInstruction(
                address=0x12,
                opcode=b"\x60",
                opcode_name="RETURN",
                operands=b"",
                operand_values=[],
                text_format="RETURN",
                opcode_value=0x60,
            ),
        ]

        from src.decompile.analysis.control import ControlFlowAnalyzer

        # Analyze control flow
        analyzer = ControlFlowAnalyzer()
        blocks = analyzer.analyze(instructions)

        # Generate stats
        visualizer = CFGVisualizer()
        stats = visualizer.generate_summary_stats(blocks, analyzer.block_graph)

        # Verify stats
        assert stats["total_blocks"] > 0
        # Note: structured blocks may have fewer instructions due to control flow merging
        assert stats["total_instructions"] > 0
        assert stats["total_edges"] > 0
        assert stats["cyclomatic_complexity"] > 1  # Has branches

    def test_max_instructions_limit(self):
        """Test limiting instructions per node."""
        # Create many instructions
        instructions = []
        for i in range(20):
            instructions.append(
                PCodeInstruction(
                    address=i * 2,
                    opcode=b"\x10",
                    opcode_name="PUSHCONST",
                    operands=bytes([i]),
                    operand_values=[i],
                    text_format=f"PUSHCONST {i}",
                    opcode_value=0x10,
                ),
            )
        instructions.append(
            PCodeInstruction(
                address=40,
                opcode=b"\x60",
                opcode_name="RETURN",
                operands=b"",
                operand_values=[],
                text_format="RETURN",
                opcode_value=0x60,
            ),
        )

        options = VisualizationOptions(max_instructions_per_node=5)
        visualizer = CFGVisualizer(options)

        dot_content = visualizer.visualize_method("many_instructions", instructions)

        # Should show truncation message
        assert "... +" in dot_content
        assert "more" in dot_content

    def test_empty_method(self):
        """Test visualization of empty method."""
        visualizer = CFGVisualizer()

        # Empty instructions
        dot_content = visualizer.visualize_method("empty_method", [])

        # Should still create valid DOT
        assert 'digraph "empty_method_cfg"' in dot_content
        # But no entry/exit nodes
        assert "Entry" not in dot_content

    def test_nested_control_structures(self):
        """Test visualization of nested control structures."""
        instructions = [
            # Outer if
            PCodeInstruction(
                address=0x00,
                opcode=b"\x11",
                opcode_name="PUSHVAR",
                operands=b"\x01",
                operand_values=[1],
                text_format="PUSHVAR 1",
                opcode_value=0x11,
            ),
            PCodeInstruction(
                address=0x02,
                opcode=b"\x41",
                opcode_name="JUMPFALSE",
                operands=b"\x14",
                operand_values=[0x14],
                text_format="JUMPFALSE 0x14",
                opcode_value=0x41,
            ),
            # Inner loop in then branch
            PCodeInstruction(
                address=0x04,
                opcode=b"\x10",
                opcode_name="PUSHCONST",
                operands=b"\x00",
                operand_values=[0],
                text_format="PUSHCONST 0",
                opcode_value=0x10,
            ),
            PCodeInstruction(
                address=0x06,
                opcode=b"\x20",
                opcode_name="POPVAR",
                operands=b"\x02",
                operand_values=[2],
                text_format="POPVAR 2",
                opcode_value=0x20,
            ),
            PCodeInstruction(
                address=0x08,
                opcode=b"\x11",
                opcode_name="PUSHVAR",
                operands=b"\x02",
                operand_values=[2],
                text_format="PUSHVAR 2",
                opcode_value=0x11,
            ),
            PCodeInstruction(
                address=0x0A,
                opcode=b"\x10",
                opcode_name="PUSHCONST",
                operands=b"\x05",
                operand_values=[5],
                text_format="PUSHCONST 5",
                opcode_value=0x10,
            ),
            PCodeInstruction(
                address=0x0C,
                opcode=b"\x31",
                opcode_name="LT",
                operands=b"",
                operand_values=[],
                text_format="LT",
                opcode_value=0x31,
            ),
            PCodeInstruction(
                address=0x0E,
                opcode=b"\x41",
                opcode_name="JUMPFALSE",
                operands=b"\x14",
                operand_values=[0x14],
                text_format="JUMPFALSE 0x14",
                opcode_value=0x41,
            ),
            PCodeInstruction(
                address=0x10,
                opcode=b"\x50",
                opcode_name="CALL",
                operands=b"inner_loop",
                operand_values=["inner_loop"],
                text_format="CALL inner_loop",
                opcode_value=0x50,
            ),
            PCodeInstruction(
                address=0x12,
                opcode=b"\x42",
                opcode_name="JUMP",
                operands=b"\x08",
                operand_values=[0x08],
                text_format="JUMP 0x08",
                opcode_value=0x42,
            ),
            # End
            PCodeInstruction(
                address=0x14,
                opcode=b"\x60",
                opcode_name="RETURN",
                operands=b"",
                operand_values=[],
                text_format="RETURN",
                opcode_value=0x60,
            ),
        ]

        visualizer = CFGVisualizer()
        dot_content = visualizer.visualize_method("nested_test", instructions)

        # Should handle nested structures
        assert "[IF]" in dot_content  # Outer IF structure
        assert "THEN:" in dot_content  # Shows nested content
        # Should show some of the nested instructions
        assert "PUSHCONST 0" in dot_content or "POPVAR 2" in dot_content
