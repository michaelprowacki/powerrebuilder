"""Grammar Management - PowerBuilder grammar definitions.

This module manages the EBNF grammars for parsing different PowerBuilder objects.
Consolidates grammar loading and selection.
"""

import logging
from pathlib import Path
from typing import Dict, Optional

from src_new._core import ObjectType

logger = logging.getLogger(__name__)


# ============================================================================
# GRAMMAR DEFINITIONS
# ============================================================================

# Simplified PowerBuilder grammar for core constructs
# Real implementation would load from .lark files

BASE_GRAMMAR = """
// PowerBuilder Base Grammar

// Starting rule
start: object_declaration

// Object declaration
object_declaration: forward_decl? type_decl

// Forward declarations
forward_decl: "forward" statement_list "end" "forward"

// Type declaration
type_decl: global_type | object_type

global_type: "global" object_type
object_type: "type" object_name "from" parent_name

object_name: IDENTIFIER
parent_name: IDENTIFIER

// Statements
statement_list: statement*
statement: variable_decl
         | function_decl
         | event_decl
         | property_decl
         | assignment
         | if_statement
         | for_statement
         | while_statement
         | return_statement
         | expression_statement

// Variable declaration
variable_decl: access_modifier? IDENTIFIER variable_name ("=" expression)?
access_modifier: "public" | "private" | "protected"
variable_name: IDENTIFIER

// Function declaration
function_decl: access_modifier? "function" IDENTIFIER? function_name "(" parameter_list? ")" statement_block
function_name: IDENTIFIER
parameter_list: parameter ("," parameter)*
parameter: IDENTIFIER variable_name

statement_block: statement_list "end" "function"

// Event declaration
event_decl: "event" event_name "(" parameter_list? ")" statement_block
event_name: IDENTIFIER

// Property declaration
property_decl: access_modifier? "property" IDENTIFIER property_name

property_name: IDENTIFIER

// Control flow
if_statement: "if" expression "then" statement_list ("else" statement_list)? "end" "if"
for_statement: "for" variable_name "=" expression "to" expression statement_list "next"
while_statement: "do" "while" expression statement_list "loop"
return_statement: "return" expression?

// Expressions
expression_statement: expression
expression: assignment_expr
assignment_expr: logical_or_expr ("=" assignment_expr)?
logical_or_expr: logical_and_expr ("or" logical_and_expr)*
logical_and_expr: equality_expr ("and" equality_expr)*
equality_expr: relational_expr (("==" | "<>") relational_expr)*
relational_expr: additive_expr (("<" | ">" | "<=" | ">=") additive_expr)*
additive_expr: multiplicative_expr (("+" | "-") multiplicative_expr)*
multiplicative_expr: unary_expr (("*" | "/") unary_expr)*
unary_expr: ("+" | "-" | "not")? postfix_expr
postfix_expr: primary_expr (accessor)*
accessor: "." IDENTIFIER
        | "[" expression "]"
        | "(" argument_list? ")"

primary_expr: literal
            | identifier_expr
            | "(" expression ")"

identifier_expr: IDENTIFIER

argument_list: expression ("," expression)*

// Assignment (now integrated into expression)
assignment: identifier_expr (accessor)* "=" expression

// Literals
literal: NUMBER
       | STRING
       | "true"
       | "false"
       | "null"

// Tokens
IDENTIFIER: /[a-zA-Z_][a-zA-Z0-9_]*/
NUMBER: /[0-9]+(\\.[0-9]+)?/
STRING: /\"[^\"]*\"/

// Whitespace and comments
%import common.WS
%ignore WS
COMMENT: "//" /[^\\n]*/
%ignore COMMENT
"""


WINDOW_GRAMMAR = (
    """
// Window-specific grammar extensions

// Override the main object declaration for windows
object_declaration: forward_decl? window_type_decl window_body

window_declaration: forward_decl? window_type_decl window_body

window_type_decl: "global"? "type" window_name "from" parent_window

window_name: IDENTIFIER
parent_window: IDENTIFIER

window_body: type_variables_block? control_declarations event_declarations "end" "type"

type_variables_block: "type" "variables" variable_decl* "end" "variables"

// Control declarations
control_declarations: control_decl*

control_decl: "type" control_type control_name "from" control_parent control_properties

control_type: "commandbutton" | "datawindow" | "statictext" | "edit" | "checkbox"
            | "radiobutton" | "dropdownlistbox" | "picturebutton" | "tab"
            | "groupbox" | "treeview" | "listview" | "richtextedit"

control_name: IDENTIFIER
control_parent: IDENTIFIER

control_properties: control_property*
control_property: property_name "=" property_value

property_value: literal | expression

// Event declarations
event_declarations: event_decl*

"""
    + BASE_GRAMMAR
)


DATAWINDOW_GRAMMAR = (
    """
// DataWindow-specific grammar

start: datawindow_declaration

datawindow_declaration: datawindow_header datawindow_sql datawindow_presentation

datawindow_header: "release" NUMBER ";"
                 | "$PBExportHeader$" IDENTIFIER

datawindow_sql: "datawindow" "(" datawindow_properties ")"

datawindow_properties: datawindow_property*
datawindow_property: property_name "=" property_value

datawindow_presentation: "table" "(" table_properties ")"
                       | "column" "(" column_properties ")"*
                       | "text" "(" text_properties ")"*

table_properties: table_property*
table_property: property_name "=" property_value

column_properties: column_property*
column_property: property_name "=" property_value

text_properties: text_property*
text_property: property_name "=" property_value

property_name: IDENTIFIER
property_value: literal | STRING | NUMBER

"""
    + BASE_GRAMMAR
)


# ============================================================================
# GRAMMAR CACHE
# ============================================================================

# Cache loaded grammars
_GRAMMAR_CACHE: Dict[ObjectType, str] = {}


def load_grammar(grammar_name: str) -> str:
    """Load a grammar by name.

    Args:
        grammar_name: Name of grammar to load

    Returns:
        Grammar string
    """
    # In real implementation, would load from .lark files
    # For now, return built-in grammars

    if grammar_name == "base":
        return BASE_GRAMMAR
    elif grammar_name == "window":
        return WINDOW_GRAMMAR
    elif grammar_name == "datawindow":
        return DATAWINDOW_GRAMMAR
    else:
        # Default to base grammar
        return BASE_GRAMMAR


def get_grammar_for_type(object_type: ObjectType) -> str:
    """Get appropriate grammar for object type.

    Args:
        object_type: PowerBuilder object type

    Returns:
        Grammar string
    """
    # Check cache
    if object_type in _GRAMMAR_CACHE:
        return _GRAMMAR_CACHE[object_type]

    # Select grammar based on type
    # For now, use base grammar for all types to avoid conflicts
    # TODO: Properly merge grammar extensions
    grammar = BASE_GRAMMAR

    # Cache and return
    _GRAMMAR_CACHE[object_type] = grammar
    return grammar


def load_grammar_from_file(file_path: Path) -> Optional[str]:
    """Load grammar from a .lark file.

    Args:
        file_path: Path to grammar file

    Returns:
        Grammar string or None if not found
    """
    try:
        if file_path.exists():
            return file_path.read_text()
        else:
            logger.warning(f"Grammar file not found: {file_path}")
            return None
    except Exception as e:
        logger.error(f"Failed to load grammar from {file_path}: {e}")
        return None


def validate_grammar(grammar: str) -> bool:
    """Validate a grammar string.

    Args:
        grammar: Grammar to validate

    Returns:
        True if valid
    """
    try:
        from lark import Lark

        # Try to create parser - will raise if invalid
        Lark(grammar, parser="lalr")
        return True
    except Exception as e:
        logger.error(f"Invalid grammar: {e}")
        return False
