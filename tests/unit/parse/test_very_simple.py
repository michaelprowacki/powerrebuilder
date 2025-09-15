"""Very simple grammar tests for PowerBuilder."""

import pytest
from lark import Lark


@pytest.fixture
def simple_pb_parser():
    """Create a minimal parser for PowerBuilder core statements."""
    grammar = r"""
    start: statements
    statements: statement statements | statement

    statement: var_decl | assignment | if_stmt | for_loop

    var_decl: NAME ":" type ";"
    type: "integer" | "string" | "boolean"

    assignment: NAME "=" value ";"
    value: NAME | NUMBER | STRING

    if_stmt: "if" condition "then"
             statements
             ["else" statements]
             "end if"

    condition: NAME compare NUMBER
    compare: ">" | "<" | ">=" | "<=" | "=" | "<>"

    for_loop: "for" NAME "=" NUMBER "to" NUMBER ["step" NUMBER]
              statements
              "next" [NAME]

    NAME: /[a-zA-Z][a-zA-Z0-9_]*/
    NUMBER: /[0-9]+/
    STRING: /"[^"]*"/

    %import common.WS
    %ignore WS
    """
    return Lark(grammar, parser="earley")


class TestSimpleGrammar:
    """Tests for simple PowerBuilder grammar."""

    def test_var_declaration(self, simple_pb_parser):
        """Test parsing variable declarations."""
        code = "x: integer;"
        tree = simple_pb_parser.parse(code)
        assert tree is not None

        code = "name: string;"
        tree = simple_pb_parser.parse(code)
        assert tree is not None

    def test_assignment(self, simple_pb_parser):
        """Test parsing assignment statements."""
        code = "x = 10;"
        tree = simple_pb_parser.parse(code)
        assert tree is not None

        code = 'name = "John";'
        tree = simple_pb_parser.parse(code)
        assert tree is not None

    def test_if_statement(self, simple_pb_parser):
        """Test parsing if statements."""
        code = """
        if x > 10 then
            y = 20;
        end if
        """
        tree = simple_pb_parser.parse(code.strip())
        assert tree is not None

        code = """
        if x > 10 then
            y = 20;
        else
            y = 0;
        end if
        """
        tree = simple_pb_parser.parse(code.strip())
        assert tree is not None

    def test_for_loop(self, simple_pb_parser):
        """Test parsing for loops."""
        code = """
        for i = 1 to 10
            sum = 0;
        next i
        """
        tree = simple_pb_parser.parse(code.strip())
        assert tree is not None

        code = """
        for i = 10 to 1 step 2
            count = count + 1;
        next
        """
        tree = simple_pb_parser.parse(code.strip())
        assert tree is not None

    def test_combined(self, simple_pb_parser):
        """Test parsing combined statements."""
        code = """
        x: integer;
        y: integer;
        x = 5;
        if x > 3 then
            y = 10;
        else
            y = 0;
        end if

        for i = 1 to 5
            x = x + i;
        next i
        """
        tree = simple_pb_parser.parse(code.strip())
        assert tree is not None
