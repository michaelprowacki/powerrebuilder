"""Tests for PowerBuilder pseudocode parser and transformer."""

import pytest

from src.parse.parser.specialized.pseudocode import PowerBuilderPseudocodeParser


@pytest.fixture
def parser() -> PowerBuilderPseudocodeParser:
    """Create a pseudocode parser instance."""
    return PowerBuilderPseudocodeParser()


def test_basic_parsing(parser: PowerBuilderPseudocodeParser) -> None:
    """Test basic pseudocode parsing."""
    code = """
    IF x > 0 THEN
        RETURN x
    END IF
    """
    tree = parser.parse(code)
    assert tree is not None
    assert tree.data == "start"


def test_parse_and_transform(parser: PowerBuilderPseudocodeParser) -> None:
    """Test parsing and transforming pseudocode to Python."""
    code = """
    IF x > 0 THEN
        RETURN x
    ELSE
        RETURN -x
    END IF
    """
    result = parser.parse_and_transform(code)
    assert result == [
        "if x > 0:",
        "    return x",
        "else:",
        "    return -x",
    ]


def test_function_definition(parser: PowerBuilderPseudocodeParser) -> None:
    """Test parsing function definitions."""
    code = """
    FUNCTION max(a: INTEGER, b: INTEGER) RETURNS INTEGER
        IF a > b THEN
            RETURN a
        ELSE
            RETURN b
        END IF
    END FUNCTION
    """
    result = parser.parse_and_transform(code)
    assert result == [
        "def max(a: int, b: int) -> int:",
        "    if a > b:",
        "        return a",
        "    else:",
        "        return b",
    ]


def test_array_operations(parser: PowerBuilderPseudocodeParser) -> None:
    """Test array operations."""
    code = """
    DECLARE numbers: ARRAY[10] OF INTEGER
    numbers[0] := 42
    RETURN numbers[0]
    """
    result = parser.parse_and_transform(code)
    assert result == [
        "numbers = [0 for _ in range(10)]",
        "numbers[0] = 42",
        "return numbers[0]",
    ]


def test_file_operations(parser: PowerBuilderPseudocodeParser) -> None:
    """Test file operations."""
    code = """
    OPENFILE data FOR READ
    READFILE data INTO content
    CLOSEFILE data
    """
    result = parser.parse_and_transform(code)
    assert result == [
        "data = open(data_path, 'r')",
        "content = data.read()",
        "data.close()",
    ]


def test_sql_operations(parser: PowerBuilderPseudocodeParser) -> None:
    """Test SQL operations."""
    code = """
    SELECT id, name
    FROM users
    WHERE active = TRUE
    ORDER BY name ASC
    """
    result = parser.parse_and_transform(code)
    assert result == [
        "query = select(id, name)",
        "query = query.from_(users).where(active = True).order_by(name ASC)",
        "result = self.session.execute(query)",
        "return result.all()",
    ]


def test_datawindow_operations(parser: PowerBuilderPseudocodeParser) -> None:
    """Test DataWindow operations."""
    code = """
    RETRIEVE dw_users INTO users WHERE active = TRUE
    UPDATE dw_users
    """
    result = parser.parse_and_transform(code)
    assert result == [
        "self.datawindow.retrieve(dw_users, into=users, where=active = True)",
        "self.datawindow.update(dw_users)",
    ]


def test_error_handling(parser: PowerBuilderPseudocodeParser) -> None:
    """Test error handling in parser."""
    with pytest.raises(ValueError, match="Syntax error") as exc:
        parser.parse("INVALID x := 1")
    assert "Syntax error" in str(exc.value)


def test_type_inference(parser: PowerBuilderPseudocodeParser) -> None:
    """Test type inference in declarations."""
    code = """
    DECLARE x: INTEGER = 42
    DECLARE name: STRING = "John"
    DECLARE active: BOOLEAN = TRUE
    """
    result = parser.parse_and_transform(code)
    assert result == [
        "x: int = 42",
        'name: str = "John"',
        "active: bool = True",
    ]


def test_complex_expressions(parser: PowerBuilderPseudocodeParser) -> None:
    """Test complex expression handling."""
    code = """
    x := (a + b) * (c - d) / 2
    y := NOT (x > 0 AND y < 10)
    z := LCASE(name) LIKE "%john%"
    """
    result = parser.parse_and_transform(code)
    assert result == [
        "x = ((a + b) * (c - d)) / 2",
        "y = (not ((x > 0) and (y < 10)))",
        'z = str(name).lower() like "%john%"',
    ]


def test_builtin_functions(parser: PowerBuilderPseudocodeParser) -> None:
    """Test built-in function transformations."""
    cases = [
        ("LENGTH(text)", "len(text)"),
        ("LCASE(name)", "str(name).lower()"),
        ("UCASE(name)", "str(name).upper()"),
        ("SUBSTRING(text, 1, 5)", "str(text)[1:1 + 5]"),
        ("ROUND(3.14)", "round(3.14)"),
        ("RANDOM(100)", "random.randint(1, 100)"),
        ("DIV(10, 3)", "(10 // 3)"),
        ("MOD(10, 3)", "(10 % 3)"),
    ]
    for code, expected in cases:
        result = parser.parse_and_transform(code)
        assert result == [expected]
