from typing import Any

import pytest
from lark import Lark, UnexpectedInput

from src.parse.visitors.pb_js_transformer import PowerBuilderJSTransformer


@pytest.fixture
def parser() -> Lark:
    """Fixture for Lark parser with PowerBuilder JS grammar."""
    with open("parse/grammar/experimental/powerbuilder_js.lark", encoding="utf-8") as f:
        grammar = f.read()
    return Lark(grammar, parser="lalr", lexer="basic", start="start")


@pytest.fixture
def transformer() -> PowerBuilderJSTransformer:
    """Fixture for PowerBuilderJSTransformer instance."""
    return PowerBuilderJSTransformer()


@pytest.fixture
def poc_parser() -> Lark:
    """Fixture for POC Lark parser with custom grammar."""
    grammar = r"""
        ASC: "asc"
        ASCII: "ascii"
        LENGTHY: "lengthy"
        IDENTIFIER: /(?!asc|ascii|lengthy)[A-Za-z_][A-Za-z0-9_]*/
        %ignore /\s+/
        start: (ASC | ASCII | LENGTHY | IDENTIFIER)+
    """
    return Lark(grammar, parser="lalr", lexer="contextual", start="start")


def test_if_statement(parser: Lark, transformer: PowerBuilderJSTransformer) -> None:
    """Test transformation of if statement."""
    pb_code = """
    if x = 1 then
        y = 2
    end if
    """
    tree = parser.parse(pb_code.strip())
    js_code = transformer.transform(tree)
    expected = "if (x === 1) {\n  y = 2\n}"
    assert js_code.strip() == expected


def test_if_else_statement(
    parser: Lark,
    transformer: PowerBuilderJSTransformer,
) -> None:
    """Test transformation of if-else statement."""
    pb_code = """
    if x = 1 then
        y = 2
    else
        y = 3
    end if
    """
    tree = parser.parse(pb_code.strip())
    js_code = transformer.transform(tree)
    expected = "if (x === 1) {\n  y = 2;\n} else {\n  y = 3;\n}"
    assert js_code.strip() == expected


def test_while_statement(parser: Lark, transformer: PowerBuilderJSTransformer) -> None:
    """Test transformation of while statement."""
    pb_code = """
    do while x < 10
        x = x + 1
    loop
    """
    tree = parser.parse(pb_code.strip())
    js_code = transformer.transform(tree)
    expected = "while (x < 10) {\n  x = x + 1;\n}"
    assert js_code.strip() == expected


def test_for_statement(parser: Lark, transformer: PowerBuilderJSTransformer) -> None:
    """Test transformation of for statement."""
    pb_code = """
    for i = 1 to 10
        x = x + i
    next
    """
    tree = parser.parse(pb_code.strip())
    js_code = transformer.transform(tree)
    expected = "for (let i = 1; i <= 10; i++) {\n  x = x + i;\n}"
    assert js_code.strip() == expected


def test_repeat_statement(parser: Lark, transformer: PowerBuilderJSTransformer) -> None:
    """Test transformation of repeat-until statement."""
    pb_code = """
    repeat
        x = x + 1
    until x > 10
    """
    tree = parser.parse(pb_code.strip())
    js_code = transformer.transform(tree)
    expected = "do {\n  x = x + 1;\n} while (!(x > 10));"
    assert js_code.strip() == expected


def test_case_statement(parser: Lark, transformer: PowerBuilderJSTransformer) -> None:
    """Test transformation of case statement."""
    pb_code = """
    case x of
        1, 2: y = 1
        3: y = 2
    otherwise
        y = 3
    end case
    """
    tree = parser.parse(pb_code.strip())
    js_code = transformer.transform(tree)
    expected = "switch (x) {\n  case 1:\n  case 2:\n    y = 1;\n    break;\n  case 3:\n    y = 2;\n    break;\n  default:\n    y = 3;\n}"
    assert js_code.strip() == expected


def test_record_declaration(
    parser: Lark,
    transformer: PowerBuilderJSTransformer,
) -> None:
    """Test transformation of record declaration."""
    pb_code = """
    record Person
        string name
        integer age
    end if
    """
    tree = parser.parse(pb_code.strip())
    js_code = transformer.transform(tree)
    expected = "class Person {\n  name: string;\n  age: number;\n\n  constructor() {\n    this.name = null;\n    this.age = null;\n  }\n}"
    assert js_code.strip() == expected


def test_array_access(parser: Lark, transformer: PowerBuilderJSTransformer) -> None:
    """Test transformation of array access."""
    pb_code = """
    x = arr(1)
    """
    tree = parser.parse(pb_code.strip())
    js_code = transformer.transform(tree)
    expected = "x = arr[1];"
    assert js_code.strip() == expected


def test_record_access(parser: Lark, transformer: PowerBuilderJSTransformer) -> None:
    """Test transformation of record field access."""
    pb_code = """
    x = person.name
    """
    tree = parser.parse(pb_code.strip())
    js_code = transformer.transform(tree)
    expected = "x = person.name;"
    assert js_code.strip() == expected


def test_builtin_functions(
    parser: Lark,
    transformer: PowerBuilderJSTransformer,
) -> None:
    """Test transformation of built-in functions."""
    pb_code = """
    len = length(str)
    myAscii = asc("A")
    char = chr(65)
    output "Hello"
    """
    tree = parser.parse(pb_code.strip())
    js_code = transformer.transform(tree)
    expected = 'len = str.length;\nmyAscii = "A".charCodeAt(0);\nchar = String.fromCharCode(65);\nconsole.log("Hello");'
    assert js_code.strip() == expected


def test_array_type_declaration(
    parser: Lark,
    transformer: PowerBuilderJSTransformer,
) -> None:
    """Test transformation of array type declaration."""
    pb_code = """
    local array(integer) numbers
    """
    tree = parser.parse(pb_code.strip())
    js_code = transformer.transform(tree)
    expected = "let numbers: Array<number>;"
    assert js_code.strip() == expected


def test_function_call(parser: Lark, transformer: PowerBuilderJSTransformer) -> None:
    """Test transformation of function call."""
    pb_code = """
    MessageBox("Hello", "World")
    """
    tree = parser.parse(pb_code.strip())
    js_code = transformer.transform(tree)
    expected = 'MessageBox("Hello", "World");'
    assert js_code.strip() == expected


def test_variable_declaration(
    parser: Lark,
    transformer: PowerBuilderJSTransformer,
) -> None:
    """Test transformation of variable declaration."""
    pb_code = """
    local integer x = 1
    local string name = "John"
    """
    tree = parser.parse(pb_code.strip())
    js_code = transformer.transform(tree)
    expected = 'let x: number = 1;\nlet name: string = "John";'
    assert js_code.strip() == expected


def test_keywords_are_matched(poc_parser: Lark) -> None:
    """Test that keywords are matched correctly in the POC parser."""
    tree = poc_parser.parse("asc ascii lengthy")

    def always_true(v: Any) -> bool:
        return True

    assert [t.type for t in tree.scan_values(always_true)] == [
        "ASC",
        "ASCII",
        "LENGTHY",
    ]


def test_valid_identifiers(poc_parser: Lark) -> None:
    """Test that valid identifiers are accepted by the POC parser."""
    for ident in ["foo", "bar", "len", "lengthen"]:
        tree = poc_parser.parse(ident)
        assert tree.children[0].type == "IDENTIFIER"


def test_forbidden_identifiers(poc_parser: Lark) -> None:
    """Test that forbidden identifiers raise a parse error in the POC parser."""
    for ident in ["asc", "ascii", "lengthy"]:
        with pytest.raises(UnexpectedInput):
            poc_parser.parse(ident)
