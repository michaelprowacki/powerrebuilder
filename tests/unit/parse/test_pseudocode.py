"""Tests for pseudocode parser and transformer."""

import pytest
from lark import Lark

from src.parse.transformers.pseudocode_transformer import PseudocodeToPython

# Load grammar once for all tests
with open("parse/pseudocode.lark", encoding="utf-8") as f:
    grammar = f.read()
parser = Lark(grammar, parser="lalr", propagate_positions=True)
transformer = PseudocodeToPython()


def parse_and_transform(code: str) -> list[str]:
    """Parse and transform pseudocode to Python."""
    tree = parser.parse(code)
    return transformer.transform(tree)


def test_if_statement():
    """Test if statement transformation."""
    code = """
    IF x > 0 THEN
        RETURN x
    END IF
    """
    result = parse_and_transform(code)
    assert result == ["if x > 0:", "    return x"]


def test_if_else_statement():
    """Test if-else statement transformation."""
    code = """
    IF x > 0 THEN
        RETURN x
    ELSE
        RETURN -x
    END IF
    """
    result = parse_and_transform(code)
    assert result == ["if x > 0:", "    return x", "else:", "    return -x"]


def test_while_loop():
    """Test while loop transformation."""
    code = """
    WHILE i < 10 DO
        i := i + 1
    END WHILE
    """
    result = parse_and_transform(code)
    assert result == ["while i < 10:", "    i = i + 1"]


def test_for_loop():
    """Test for loop transformation."""
    code = """
    FOR i FROM 1 TO 10 STEP 2 DO
        x := x + i
    END FOR
    """
    result = parse_and_transform(code)
    assert result == ["for i in range(1, 10 + 1, 2):", "    x = x + i"]


def test_foreach_loop():
    """Test foreach loop transformation."""
    code = """
    FOREACH item IN items DO
        total := total + item
    END FOREACH
    """
    result = parse_and_transform(code)
    assert result == ["for item in items:", "    total = total + item"]


def test_case_statement():
    """Test case statement transformation."""
    code = """
    CASE x OF
        1: RETURN "one"
        2: RETURN "two"
        ELSE RETURN "other"
    END CASE
    """
    result = parse_and_transform(code)
    assert result == [
        "if x == 1:",
        '    return "one"',
        "elif x == 2:",
        '    return "two"',
        "else:",
        '    return "other"',
    ]


def test_sql_select():
    """Test SQL SELECT transformation."""
    code = """
    SELECT id, name FROM users WHERE age > 18 ORDER BY name
    """
    result = parse_and_transform(code)
    assert result == [
        "query = select(id, name)",
        "query = query.from_(users).where(age > 18).order_by(name)",
        "result = self.session.execute(query)",
        "return result.all()",
    ]


def test_sql_insert():
    """Test SQL INSERT transformation."""
    code = """
    INSERT INTO users (name, age) VALUES ("John", 25)
    """
    result = parse_and_transform(code)
    assert result == [
        "stmt = insert(users)",
        "stmt = stmt.values({'name': \"John\", 'age': 25})",
        "self.session.execute(stmt)",
        "self.session.commit()",
    ]


def test_sql_update():
    """Test SQL UPDATE transformation."""
    code = """
    UPDATE users SET age = age + 1 WHERE id = 1
    """
    result = parse_and_transform(code)
    assert result == [
        "stmt = update(users)",
        "stmt = stmt.values(age = age + 1).where(id = 1)",
        "self.session.execute(stmt)",
        "self.session.commit()",
    ]


def test_sql_delete():
    """Test SQL DELETE transformation."""
    code = """
    DELETE FROM users WHERE id = 1
    """
    result = parse_and_transform(code)
    assert result == [
        "stmt = delete(users).where(id = 1)",
        "self.session.execute(stmt)",
        "self.session.commit()",
    ]


def test_datawindow_retrieve():
    """Test DataWindow RETRIEVE transformation."""
    code = """
    RETRIEVE dw_users INTO users WHERE active = TRUE
    """
    result = parse_and_transform(code)
    assert result == [
        "self.datawindow.retrieve(dw_users, into=users, where=active = True)",
    ]


def test_expressions():
    """Test expression transformations."""
    cases = [
        ("x AND y", "(x and y)"),
        ("x OR y", "(x or y)"),
        ("NOT x", "(not x)"),
        ("x + y * z", "(x + (y * z))"),
        ("(x + y) * z", "((x + y) * z)"),
        ("x = y", "x == y"),
        ("x <> y", "x != y"),
        ("x LIKE y", "x like y"),
    ]
    for code, expected in cases:
        result = parse_and_transform(code)
        assert result == [expected]


def test_literals():
    """Test literal transformations."""
    cases = [
        ("42", "42"),
        ("3.14", "3.14"),
        ('"hello"', '"hello"'),
        ("TRUE", "True"),
        ("FALSE", "False"),
        ("NULL", "None"),
    ]
    for code, expected in cases:
        result = parse_and_transform(code)
        assert result == [expected]


def test_repeat_until():
    """Test repeat-until loop transformation."""
    code = """
    REPEAT
        i := i + 1
    UNTIL i >= 10
    """
    result = parse_and_transform(code)
    assert result == [
        "while True:",
        "    i = i + 1",
        "    if i >= 10:",
        "        break",
    ]


def test_declare_variables():
    """Test variable declarations."""
    cases = [
        (
            "DECLARE x: INTEGER",
            ["x: int = 0"],
        ),
        (
            'DECLARE name: STRING = "John"',
            ['name: str = "John"'],
        ),
        (
            "DECLARE numbers: ARRAY[10] OF INTEGER",
            ["numbers: list[int] = 0"],
        ),
    ]
    for code, expected in cases:
        result = parse_and_transform(code)
        assert result == expected


def test_file_operations():
    """Test file operation transformations."""
    cases = [
        (
            "OPENFILE data FOR READ",
            ["data = open(data_path, 'r')"],
        ),
        (
            "READFILE data INTO content",
            ["content = data.read()"],
        ),
        (
            'WRITEFILE data FROM "Hello"',
            ['data.write(str("Hello"))'],
        ),
        (
            "CLOSEFILE data",
            ["data.close()"],
        ),
    ]
    for code, expected in cases:
        result = parse_and_transform(code)
        assert result == expected


def test_builtin_functions():
    """Test built-in function transformations."""
    cases = [
        ("LENGTH(text)", "len(text)"),
        ("LCASE(name)", "str(name).lower()"),
        ("UCASE(name)", "str(name).upper()"),
        ("SUBSTRING(text, 1, 5)", "str(text)[1:1 + 5]"),
        ("SUBSTRING(text, 1)", "str(text)[1:]"),
        ("ROUND(3.14)", "round(3.14)"),
        ("ROUND(3.14, 1)", "round(3.14, 1)"),
        ("RANDOM()", "random.random()"),
        ("RANDOM(100)", "random.randint(1, 100)"),
        ("DIV(10, 3)", "(10 // 3)"),
        ("MOD(10, 3)", "(10 % 3)"),
    ]
    for code, expected in cases:
        result = parse_and_transform(code)
        assert result == [expected]


def test_array_access():
    """Test array access transformations."""
    code = """
    x := numbers[i]
    numbers[i] := x + 1
    """
    result = parse_and_transform(code)
    assert result == [
        "x = numbers[i]",
        "numbers[i] = x + 1",
    ]


def test_powerbuilder_sql():
    """Test PowerBuilder SQL transformations."""
    code = """
    SELECT id, name
    FROM users
    WHERE active = TRUE
    ORDER BY name ASC
    """
    result = parse_and_transform(code)
    assert any("select" in line or "from_" in line for line in result)


def test_powerbuilder_datawindow():
    """Test PowerBuilder DataWindow transformations."""
    cases = [
        (
            "RETRIEVE dw_users INTO users WHERE active = TRUE",
            ["self.datawindow.retrieve(dw_users, into=users, where=active = True)"],
        ),
        (
            "UPDATE dw_users",
            ["self.datawindow.update(dw_users)"],
        ),
        (
            "INSERT dw_users",
            ["self.datawindow.insert(dw_users)"],
        ),
        (
            "DELETE dw_users",
            ["self.datawindow.delete(dw_users)"],
        ),
    ]
    for code, expected in cases:
        result = parse_and_transform(code)
        assert result == expected


def test_complex_expressions():
    """Test complex expression transformations."""
    cases = [
        (
            "x + y * (z - 1) / 2",
            "(x + ((y * (z - 1)) / 2))",
        ),
        (
            "NOT (x > 0 AND y < 10)",
            "(not ((x > 0) and (y < 10)))",
        ),
        (
            'LCASE(name) LIKE "%john%"',
            'str(name).lower() like "%john%"',
        ),
    ]
    for code, expected in cases:
        result = parse_and_transform(code)
        assert result == [expected]


def test_error_handling():
    """Test error handling in parser and transformer."""
    with pytest.raises(ValueError, match="Syntax error"):
        parse_and_transform("INVALID x := 1")
