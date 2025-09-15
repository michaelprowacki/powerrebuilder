"""Tests for PowerBuilder grammar with directly embedded grammar."""

import pytest
from lark import Lark

# Define the grammar directly in the test file
PB_GRAMMAR = r"""
start: statements

statements: statement+

statement: var_decl
         | assignment
         | if_statement
         | for_loop
         | function_decl

var_decl: NAME ":" type ";"
type: "integer" | "string" | "boolean" | "date" | "datetime" | "decimal" | "real" | "long" | "char"
     | NAME

assignment: NAME "=" value ";"
value: NAME | NUMBER | STRING | expr
expr: value "+" value
     | value "-" value
     | value "*" value
     | value "/" value

if_statement: "if" condition "then" statements "end" "if"
            | "if" condition "then" statements "else" statements "end" "if"

for_loop: "for" NAME "=" NUMBER "to" NUMBER statement+ "next" [NAME]
        | "for" NAME "=" NUMBER "to" NUMBER "step" NUMBER statement+ "next" [NAME]

function_decl: "function" return_type NAME "(" [parameter_list] ")" statements "end" "function"
return_type: type | "void"
parameter_list: parameter ("," parameter)*
parameter: NAME ":" type

condition: NAME compare NUMBER
         | NAME compare STRING
         | NAME compare NAME
compare: ">" | "<" | ">=" | "<=" | "=" | "<>"

NAME: /[a-zA-Z][a-zA-Z0-9_]*/
NUMBER: /[0-9]+(\.[0-9]+)?/
STRING: /"[^"]*"/

%import common.WS
%ignore WS
"""


@pytest.fixture
def pb_parser():
    """Create a parser for PowerBuilder grammar."""
    return Lark(PB_GRAMMAR, parser="earley")


class TestPowerBuilderDirect:
    """Tests for PowerBuilder grammar with directly embedded grammar."""

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
