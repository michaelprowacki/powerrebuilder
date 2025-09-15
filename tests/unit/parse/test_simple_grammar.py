"""Tests for a simple PowerBuilder grammar.

This module contains tests for parsing basic PowerBuilder statements.
"""

from __future__ import annotations

import pytest
from lark import Lark

# Define a very simple grammar for basic PowerBuilder statements
SIMPLE_GRAMMAR = r"""
start: statement+

statement: var_declaration | assignment | if_statement

var_declaration: NAME ":" type ";"
type: "integer" | "string" | "boolean"

assignment: NAME "=" value ";"
value: NAME | NUMBER | STRING

if_statement: "if" condition "then"
              statement+
              ["else" statement+]
              "end if"

condition: NAME comp_op NUMBER
comp_op: ">" | "<" | ">=" | "<=" | "=" | "<>"

NAME: /[a-zA-Z_][a-zA-Z0-9_]*/
NUMBER: /[0-9]+/
STRING: /"[^"]*"/

%import common.WS
%ignore WS
"""


@pytest.fixture
def simple_parser():
    """Create a very simple parser for basic PowerBuilder grammar."""
    return Lark(SIMPLE_GRAMMAR)


class TestSimpleGrammar:
    """Test cases for a simple PowerBuilder grammar."""

    def test_variable_declarations(self, simple_parser):
        """Test parsing of variable declarations."""
        # Basic variable declaration
        code = "x: integer;"
        tree = simple_parser.parse(code)
        assert tree is not None

        # Multiple variable declarations
        code = """
        x: integer;
        y: string;
        flag: boolean;
        """
        tree = simple_parser.parse(code.strip())
        assert tree is not None

    def test_assignments(self, simple_parser):
        """Test parsing of assignment statements."""
        # Simple assignment to number
        code = "x = 10;"
        tree = simple_parser.parse(code)
        assert tree is not None

        # Assignment to string
        code = 'message = "Hello";'
        tree = simple_parser.parse(code)
        assert tree is not None

        # Assignment to variable
        code = "x = y;"
        tree = simple_parser.parse(code)
        assert tree is not None

    def test_if_statements(self, simple_parser):
        """Test parsing of IF statements."""
        # Simple IF
        code = """
        if x > 5 then
            y = 10;
        end if
        """
        tree = simple_parser.parse(code.strip())
        assert tree is not None

        # IF with ELSE
        code = """
        if x > 5 then
            y = 10;
        else
            y = 0;
        end if
        """
        tree = simple_parser.parse(code.strip())
        assert tree is not None

    def test_combined_statements(self, simple_parser):
        """Test parsing of combined statements."""
        code = """
        x: integer;
        y: integer;

        x = 5;

        if x > 3 then
            y = 10;
        else
            y = 0;
        end if
        """
        tree = simple_parser.parse(code.strip())
        assert tree is not None
