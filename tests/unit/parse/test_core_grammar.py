"""Test core PowerBuilder grammar parsing functionality.

This module tests that powerbuilder_core.lark can parse
a core subset of PowerBuilder statements including:
- Variable declarations
- Assignments
- If statements
- Functions
- Basic expressions
"""

from pathlib import Path

import pytest
from lark import Lark

# Load grammar files
GRAMMAR_DIR = Path(__file__).parent.parent.parent / "parse" / "grammar"


@pytest.fixture
def pb_parser():
    """Create PowerBuilder parser from core grammar file."""
    # Read powerbuilder_core.lark
    pb_grammar = (GRAMMAR_DIR / "powerbuilder_core.lark").read_text()

    # Create parser
    return Lark(pb_grammar, start="start", parser="lalr")


class TestCoreGrammar:
    """Test core PowerBuilder grammar functionality."""

    def test_variable_declaration(self, pb_parser):
        """Test parsing of variable declarations."""
        code = "myvar: integer;"
        tree = pb_parser.parse(code)
        assert tree is not None

    def test_string_variable_declaration(self, pb_parser):
        """Test parsing of string variable declarations."""
        code = "name: string;"
        tree = pb_parser.parse(code)
        assert tree is not None

    def test_assignment(self, pb_parser):
        """Test parsing of assignments."""
        code = "x = 42;"
        tree = pb_parser.parse(code)
        assert tree is not None

    def test_string_assignment(self, pb_parser):
        """Test parsing of string assignments."""
        code = 'message = "Hello World";'
        tree = pb_parser.parse(code)
        assert tree is not None

    def test_simple_if_statement(self, pb_parser):
        """Test parsing of simple if statements."""
        code = """
        if x > 10 then
            y = 20;
        end if
        """
        tree = pb_parser.parse(code)
        assert tree is not None

    def test_if_else_statement(self, pb_parser):
        """Test parsing of if-else statements."""
        code = """
        if x > 10 then
            y = 20;
        else
            y = 5;
        end if
        """
        tree = pb_parser.parse(code)
        assert tree is not None

    def test_simple_function(self, pb_parser):
        """Test parsing of simple function declaration."""
        code = """
        function integer add(x: integer, y: integer)
            return x + y;
        end function
        """
        tree = pb_parser.parse(code)
        assert tree is not None

    def test_for_loop(self, pb_parser):
        """Test parsing of for loop."""
        code = """
        for i = 1 to 10
            sum = sum + i;
        next i
        """
        tree = pb_parser.parse(code)
        assert tree is not None

    def test_for_loop_with_step(self, pb_parser):
        """Test parsing of for loop with step."""
        code = """
        for i = 0 to 20 step 2
            sum = sum + i;
        next i
        """
        tree = pb_parser.parse(code)
        assert tree is not None

    def test_arithmetic_expression(self, pb_parser):
        """Test parsing of arithmetic expressions."""
        code = "result = (x + y) * 2 - z / 3;"
        tree = pb_parser.parse(code)
        assert tree is not None

    def test_multiple_statements(self, pb_parser):
        """Test parsing of multiple statements."""
        code = """
        x: integer;
        y: integer;
        x = 10;
        y = 20;
        if x < y then
            result = y - x;
        else
            result = x - y;
        end if
        """
        tree = pb_parser.parse(code)
        assert tree is not None

    @pytest.mark.parametrize(
        "type_name",
        [
            "integer",
            "string",
            "boolean",
            "date",
            "decimal",
            "long",
            "real",
            "char",
        ],
    )
    def test_type_declarations(self, pb_parser, type_name):
        """Test parsing of various type declarations."""
        code = f"myvar: {type_name};"
        tree = pb_parser.parse(code)
        assert tree is not None

    def test_comparison_operators(self, pb_parser):
        """Test parsing of comparison operators."""
        comparisons = [
            "if x > y then z = 1; end if",
            "if x < y then z = 1; end if",
            "if x >= y then z = 1; end if",
            "if x <= y then z = 1; end if",
            "if x = y then z = 1; end if",
            "if x <> y then z = 1; end if",
        ]
        for code in comparisons:
            tree = pb_parser.parse(code)
            assert tree is not None

    def test_function_with_no_params(self, pb_parser):
        """Test parsing of function with no parameters."""
        code = """
        function integer getCount()
            return 42;
        end function
        """
        tree = pb_parser.parse(code)
        assert tree is not None

    def test_nested_expressions(self, pb_parser):
        """Test parsing of nested expressions."""
        code = "result = ((a + b) * (c - d)) / (e + f);"
        tree = pb_parser.parse(code)
        assert tree is not None

    def test_logical_expressions(self, pb_parser):
        """Test parsing of logical expressions."""
        code = """
        if x > 0 and y < 100 then
            valid = 1;
        end if
        """
        tree = pb_parser.parse(code)
        assert tree is not None

    def test_function_calls(self, pb_parser):
        """Test parsing of function calls."""
        code = "result = add(10, 20);"
        tree = pb_parser.parse(code)
        assert tree is not None

    def test_empty_program(self, pb_parser):
        """Test parsing of empty program."""
        code = ""
        tree = pb_parser.parse(code)
        assert tree is not None
