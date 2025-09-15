"""Tests for the PowerBuilder grammar."""

import os

import pytest
from lark import Lark


@pytest.fixture
def pb_parser():
    """Create a parser for the PowerBuilder grammar."""
    grammar_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "parse",
        "grammar",
        "powerbuilder.lark",
    )
    with open(grammar_path, encoding="utf-8") as f:
        grammar = f.read()
    # Add import_paths for grammar imports
    import_paths = [os.path.dirname(grammar_path)]
    return Lark(grammar, parser="earley", import_paths=import_paths)


class TestPowerBuilderGrammar:
    """Tests for the PowerBuilder grammar."""

    def test_variable_declaration(self, pb_parser):
        """Test variable declarations."""
        code = "x: integer;"
        tree = pb_parser.parse(code)
        assert tree is not None

        code = "name: string;"
        tree = pb_parser.parse(code)
        assert tree is not None

        code = "customer_id: long;"
        tree = pb_parser.parse(code)
        assert tree is not None

    def test_assignment(self, pb_parser):
        """Test assignment statements."""
        code = "x = 10;"
        tree = pb_parser.parse(code)
        assert tree is not None

        code = 'name = "John";'
        tree = pb_parser.parse(code)
        assert tree is not None

        code = "sum = a + b;"
        tree = pb_parser.parse(code)
        assert tree is not None

    def test_if_statement(self, pb_parser):
        """Test if statements."""
        code = """
        if x > 5 then
            y = 10;
        end if
        """
        tree = pb_parser.parse(code.strip())
        assert tree is not None

        code = """
        if x > 5 then
            y = 10;
        else
            y = 0;
        end if
        """
        tree = pb_parser.parse(code.strip())
        assert tree is not None

    def test_for_loop(self, pb_parser):
        """Test for loops."""
        code = """
        for i = 1 to 10
            sum = 0;
        next i
        """
        tree = pb_parser.parse(code.strip())
        assert tree is not None

        code = """
        for i = 10 to 1 step 2
            count = count + 1;
        next
        """
        tree = pb_parser.parse(code.strip())
        assert tree is not None

    def test_function_declaration(self, pb_parser):
        """Test function declarations."""
        code = """
        function integer calculate_sum(a: integer, b: integer)
            return_val = a + b;
        end function
        """
        tree = pb_parser.parse(code.strip())
        assert tree is not None

        code = """
        function void process_data()
            x = 10;
            y = 20;
        end function
        """
        tree = pb_parser.parse(code.strip())
        assert tree is not None

    def test_comments(self, pb_parser):
        """Test comments."""
        code = """
        // This is a comment
        x = 10; // End of line comment
        """
        tree = pb_parser.parse(code.strip())
        assert tree is not None
