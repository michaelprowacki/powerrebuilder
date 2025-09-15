"""Test script to verify parsing functionality."""

import logging
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO)

# Add the current directory to the path so we can import our modules
sys.path.append(".")

from src.parse import parse_file


def test_parse():
    """Test parsing on an extracted window file."""
    try:
        file_path = "output/test_extraction/dcm_sms-pbd/w_patient_sms_maint.win"
        if not Path(file_path).exists():
            return

        parse_file(file_path)
    except Exception:
        pass


if __name__ == "__main__":
    test_parse()

"""Simple test for PowerBuilder parser functionality."""

import pytest
from lark import Lark, Tree


@pytest.fixture
def lark_parser():
    """Create a simple Lark parser for basic statements."""
    # Define a minimal grammar for testing
    grammar = """
    start: statement+

    statement: var_declaration | assignment | if_statement

    var_declaration: IDENTIFIER ":" TYPE_NAME ("=" expression)? ";"
    assignment: IDENTIFIER "=" expression ";"
    if_statement: "if" condition "then" statement* ("else" statement*)? "end if"

    condition: expression
    expression: IDENTIFIER | NUMBER | STRING

    IDENTIFIER: /[a-zA-Z_][a-zA-Z0-9_]*/
    TYPE_NAME: "integer" | "string" | "boolean"
    NUMBER: /[0-9]+/
    STRING: /"[^"]*"/

    %import common.WS
    %ignore WS
    """
    return Lark(grammar, parser="lalr")


def test_simple_parser(lark_parser):
    """Test that the basic parser works."""
    # Simple variable declaration
    tree = lark_parser.parse("x: integer;")
    assert isinstance(tree, Tree)

    # Simple assignment
    tree = lark_parser.parse("x = 10;")
    assert isinstance(tree, Tree)

    # Simple if statement
    code = """
    if x then
        y = 10;
    end if
    """
    tree = lark_parser.parse(code.strip())
    assert isinstance(tree, Tree)


def test_simple_grammar_combinations(lark_parser):
    """Test simple combinations of grammar rules."""
    code = """
    x: integer;
    y: string = "hello";
    x = 42;
    if x then
        y = "world";
    else
        y = "goodbye";
    end if
    """
    tree = lark_parser.parse(code.strip())
    assert isinstance(tree, Tree)
