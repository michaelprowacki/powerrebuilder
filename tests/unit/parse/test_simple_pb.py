"""Very simple PowerBuilder grammar tests."""

import pytest
from lark import Lark

# Define a minimal grammar string
SIMPLE_GRAMMAR = r"""
start: statements

statements: statement+

statement: var_decl
         | assignment
         | if_statement
         | for_loop

var_decl: NAME ":" type ";"
type: "integer" | "string" | "boolean"

assignment: NAME "=" value ";"
value: NAME | NUMBER | STRING | expr
expr: value "+" value

if_statement: "if" condition "then" statements "end" "if"
            | "if" condition "then" statements "else" statements "end" "if"

for_loop: "for" NAME "=" NUMBER "to" NUMBER statement+ "next" [NAME]
        | "for" NAME "=" NUMBER "to" NUMBER "step" NUMBER statement+ "next" [NAME]

condition: NAME compare NUMBER
compare: ">" | "<" | ">=" | "<=" | "=" | "<>"

NAME: /[a-zA-Z][a-zA-Z0-9_]*/
NUMBER: /[0-9]+/
STRING: /"[^"]*"/

%import common.WS
%ignore WS
"""


@pytest.fixture
def simple_parser():
    """Create a simple parser for PowerBuilder grammar."""
    return Lark(SIMPLE_GRAMMAR, parser="earley")


class TestSimplePB:
    """Test simple PowerBuilder grammar."""

    def test_var_declaration(self, simple_parser):
        """Test variable declarations."""
        code = "x: integer;"
        tree = simple_parser.parse(code)
        assert tree is not None

        code = "name: string;"
        tree = simple_parser.parse(code)
        assert tree is not None

    def test_assignment(self, simple_parser):
        """Test assignment statements."""
        code = "x = 10;"
        tree = simple_parser.parse(code)
        assert tree is not None

        code = 'name = "John";'
        tree = simple_parser.parse(code)
        assert tree is not None

        code = "sum = a + b;"
        tree = simple_parser.parse(code)
        assert tree is not None

    def test_if_statement(self, simple_parser):
        """Test if statements."""
        code = """
        if x > 5 then
            y = 10;
        end if
        """
        tree = simple_parser.parse(code.strip())
        assert tree is not None

        code = """
        if x > 5 then
            y = 10;
        else
            y = 0;
        end if
        """
        tree = simple_parser.parse(code.strip())
        assert tree is not None

    def test_for_loop(self, simple_parser):
        """Test for loops."""
        code = """
        for i = 1 to 10
            sum = 0;
        next i
        """
        tree = simple_parser.parse(code.strip())
        assert tree is not None

        code = """
        for i = 10 to 1 step 2
            count = count + 1;
        next
        """
        tree = simple_parser.parse(code.strip())
        assert tree is not None

    def test_combined(self, simple_parser):
        """Test combined statements."""
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
        tree = simple_parser.parse(code.strip())
        assert tree is not None
