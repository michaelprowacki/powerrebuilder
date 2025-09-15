"""Tests for pseudocode transformer."""

import sys
from pathlib import Path

import pytest

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.parse.parser.specialized.pseudocode import PowerBuilderPseudocodeParser


@pytest.fixture
def parser():
    """Create a pseudocode parser instance."""
    return PowerBuilderPseudocodeParser()


def test_factorial_example(parser):
    """Test factorial function example."""
    code = """
    // Declaration and implementation of function calculating factorial of given number
    FUNCTION Factorial(Num:INTEGER) RETURNS INTEGER
        IF Num = 0 OR Num = 1
          THEN
            RETURN 1
          ELSE
            RETURN Num * Factorial(Num - 1)
        ENDIF
    ENDFUNCTION

    // Getting number from user
    INPUT Number
    Number ← INTEGER(Number)

    OUTPUT Factorial(Number)
    """
    result = parser.parse_and_transform(code)
    assert result == [
        "# Declaration and implementation of function calculating factorial of given number",
        "def Factorial(Num: int) -> int:",
        "    if Num == 0 or Num == 1:",
        "        return 1",
        "    else:",
        "        return Num * Factorial(Num - 1)",
        "",
        "# Getting number from user",
        "Number = input('Enter Number: ')",
        "Number = int(Number)",
        "",
        "print(f'{Factorial(Number)}')",
    ]


def test_nested_loops_example(parser):
    """Test nested loops example."""
    code = """
    INPUT NumRows
    FOR i ← 0 TO NumRows
        FOR j ← 0 TO i
            OUTPUT "i:", i
        NEXT j
        OUTPUT '\\n'
    NEXT i
    """
    result = parser.parse_and_transform(code)
    assert result == [
        "NumRows = input('Enter NumRows: ')",
        "for i in range(0, NumRows + 1):",
        "    for j in range(0, i + 1):",
        '        print(f"i:{i}")',
        '    print("\\n")',
    ]


def test_calculator_example(parser):
    """Test calculator example."""
    code = """
    OUTPUT "Enter a number: "
    INPUT NumA

    OUTPUT "Enter another number: "
    INPUT NumB

    NumA ← REAL(NumA)
    NumB ← REAL(NumB)

    OUTPUT "Enter operator: "
    INPUT Operator

    CASE OF Operator
      "add": OUTPUT NumA + NumB
      "sub": OUTPUT NumA - NumB
      "mul": OUTPUT NumA * NumB
      "div": OUTPUT NumA / NumB
      "mod": OUTPUT MOD(NumA, NumB)
      OTHERWISE: OUTPUT "Unknown operator"
    ENDCASE
    """
    result = parser.parse_and_transform(code)
    assert result == [
        'print("Enter a number: ")',
        "NumA = input('Enter NumA: ')",
        "",
        'print("Enter another number: ")',
        "NumB = input('Enter NumB: ')",
        "",
        "NumA = float(NumA)",
        "NumB = float(NumB)",
        "",
        'print("Enter operator: ")',
        "Operator = input('Enter Operator: ')",
        "",
        "match Operator:",
        '    case "add":',
        "        print(f'{NumA + NumB}')",
        '    case "sub":',
        "        print(f'{NumA - NumB}')",
        '    case "mul":',
        "        print(f'{NumA * NumB}')",
        '    case "div":',
        "        print(f'{NumA / NumB}')",
        '    case "mod":',
        "        print(f'{NumA % NumB}')",
        "    case _:",
        '        print("Unknown operator")',
    ]


def test_prime_sieve_example(parser):
    """Test prime sieve example."""
    code = """
    DECLARE Limit: INTEGER

    INPUT Limit

    DECLARE IsPrime : ARRAY[Limit] OF BOOLEAN

    FOR Number ← 2 TO Limit
        IsPrime[Number] ← TRUE
    NEXT Number

    FOR Number ← 2 TO Limit
        IF IsPrime[Number] = TRUE
          THEN
            OUTPUT Number

            FOR Multiple ← 2 TO DIV(Limit, Number)
                IsPrime[Number * Multiple] ← FALSE
            NEXT Multiple
        ENDIF
    NEXT Number
    """
    result = parser.parse_and_transform(code)
    assert result == [
        "Limit = input('Enter Limit: ')",
        "Limit = int(Limit)",
        "",
        "IsPrime = [False for _ in range(Limit + 1)]",
        "",
        "for Number in range(2, Limit + 1):",
        "    IsPrime[Number] = True",
        "",
        "for Number in range(2, Limit + 1):",
        "    if IsPrime[Number] == True:",
        "        print(f'{Number}')",
        "",
        "        for Multiple in range(2, (Limit // Number) + 1):",
        "            IsPrime[Number * Multiple] = False",
    ]


def test_file_copy_example(parser):
    """Test file copy example."""
    code = """
    OPENFILE "inp.txt" FOR READ
    READFILE "inp.txt", Text
    CLOSEFILE "inp.txt"

    OUTPUT "Text from file: ", Text, "\\n"

    OPENFILE "out.txt" FOR WRITE
    WRITEFILE "out.txt", Text
    CLOSEFILE "out.txt"
    """
    result = parser.parse_and_transform(code)
    assert result == [
        'inp = open("inp.txt", "r")',
        "Text = inp.read()",
        "inp.close()",
        "",
        'print(f"Text from file: {Text}\\n")',
        "",
        'out = open("out.txt", "w")',
        "out.write(Text)",
        "out.close()",
    ]


def test_syntax_error_example(parser):
    """Test syntax error handling example."""
    code = """
    // Handling error in for loop
    INPUT NumRows
    FOR TO NumRows
        FOR j ← 0 TO i
            OUTPUT "i:", i
        NEXT j
        OUTPUT '\\n'
    NEXT i
    """
    with pytest.raises(ValueError) as exc:
        parser.parse_and_transform(code)
    assert "Syntax error" in str(exc.value)


def test_array_example(parser):
    """Test array manipulation example."""
    code = """
    DECLARE numbers: ARRAY[5] OF INTEGER
    DECLARE i: INTEGER

    FOR i FROM 0 TO 4 DO
        INPUT numbers[i]
        numbers[i] ← INTEGER(numbers[i])
    END FOR

    FOR i FROM 0 TO 4 DO
        OUTPUT numbers[i]
    END FOR
    """
    result = parser.parse_and_transform(code)
    assert result == [
        "numbers = [0 for _ in range(5)]",
        "",
        "for i in range(0, 4 + 1):",
        "    numbers[i] = input('Enter numbers[i]: ')",
        "    numbers[i] = int(numbers[i])",
        "",
        "for i in range(0, 4 + 1):",
        "    print(f'{numbers[i]}')",
    ]


def test_file_example(parser):
    """Test file handling example."""
    code = """
    OPENFILE data FOR READ SHARING READONLY
    DECLARE line: STRING

    READFILE data INTO line
    OUTPUT line

    CLOSEFILE data
    """
    result = parser.parse_and_transform(code)
    assert result == [
        "data = open(data_path, 'r')",
        "",
        "line = data.read()",
        "print(f'{line}')",
        "",
        "data.close()",
    ]


def test_error_handling_example(parser):
    """Test error handling example."""
    code = """
    FUNCTION ReadNumber() RETURNS INTEGER THROWS ValueError
        DECLARE num: STRING
        INPUT num

        TRY
            RETURN INTEGER(num)
        CATCH e: ValueError
            OUTPUT "Invalid number"
            RETURN 0
        END TRY
    ENDFUNCTION
    """
    result = parser.parse_and_transform(code)
    assert result == [
        "def ReadNumber() -> int:",
        '    """',
        "    Raises:",
        "        ValueError: If an error occurs",
        '    """',
        "",
        "    num = input('Enter num: ')",
        "",
        "    try:",
        "        return int(num)",
        "    except ValueError as e:",
        '        print("Invalid number")',
        "        return 0",
    ]


def test_case_example(parser):
    """Test case statement example."""
    code = """
    CASE grade OF
        "A": OUTPUT "Excellent"
        "B": OUTPUT "Good"
        "C": OUTPUT "Fair"
        "D": OUTPUT "Poor"
        OTHERWISE: OUTPUT "Invalid grade"
    END CASE
    """
    result = parser.parse_and_transform(code)
    assert result == [
        "match grade:",
        '    case "A":',
        '        print("Excellent")',
        '    case "B":',
        '        print("Good")',
        '    case "C":',
        '        print("Fair")',
        '    case "D":',
        '        print("Poor")',
        "    case _:",
        '        print("Invalid grade")',
    ]


def test_repeat_until_example(parser):
    """Test repeat until loop example."""
    code = """
    DECLARE num: INTEGER
    num ← 0

    REPEAT
        num ← num + 1
        OUTPUT num
    UNTIL num = 5
    """
    result = parser.parse_and_transform(code)
    assert result == [
        "num = 0",
        "",
        "while True:",
        "    num = num + 1",
        "    print(f'{num}')",
        "    if num == 5:",
        "        break",
    ]


def test_function_with_multiple_params(parser):
    """Test function with multiple parameters."""
    code = """
    FUNCTION Add(a:INTEGER, b:INTEGER) RETURNS INTEGER
        RETURN a + b
    ENDFUNCTION

    FUNCTION Concat(s1:STRING, s2:STRING) RETURNS STRING
        RETURN s1 + s2
    ENDFUNCTION
    """
    result = parser.parse_and_transform(code)
    assert result == [
        "def Add(a: int, b: int) -> int:",
        "    return a + b",
        "",
        "def Concat(s1: str, s2: str) -> str:",
        "    return s1 + s2",
    ]


def test_array_operations(parser):
    """Test array operations."""
    code = """
    DECLARE matrix: ARRAY[3] OF ARRAY[3] OF INTEGER
    DECLARE i: INTEGER
    DECLARE j: INTEGER

    FOR i FROM 0 TO 2 DO
        FOR j FROM 0 TO 2 DO
            matrix[i][j] ← i * 3 + j
        END FOR
    END FOR
    """
    result = parser.parse_and_transform(code)
    assert result == [
        "matrix = [[0 for _ in range(3)] for _ in range(3)]",
        "",
        "for i in range(0, 2 + 1):",
        "    for j in range(0, 2 + 1):",
        "        matrix[i][j] = i * 3 + j",
    ]


def test_file_operations(parser):
    """Test file operations."""
    code = """
    OPENFILE data FOR WRITE
    WRITEFILE data FROM "Hello"
    CLOSEFILE data

    OPENFILE data FOR READ
    DECLARE content: STRING
    READFILE data INTO content
    OUTPUT content
    CLOSEFILE data
    """
    result = parser.parse_and_transform(code)
    assert result == [
        "data = open(data_path, 'w')",
        'data.write("Hello")',
        "data.close()",
        "",
        "data = open(data_path, 'r')",
        "content = data.read()",
        "print(f'{content}')",
        "data.close()",
    ]


def test_builtin_functions(parser):
    """Test built-in functions."""
    code = """
    DECLARE str: STRING
    str ← "Hello World"

    OUTPUT LENGTH(str)
    OUTPUT LCASE(str)
    OUTPUT UCASE(str)
    OUTPUT SUBSTRING(str, 0, 5)
    OUTPUT ROUND(3.14159, 2)
    OUTPUT RANDOM()
    """
    result = parser.parse_and_transform(code)
    assert result == [
        'str = "Hello World"',
        "",
        "print(f'{len(str)}')",
        "print(f'{str.lower()}')",
        "print(f'{str.upper()}')",
        "print(f'{str[0:5]}')",
        "print(f'{round(3.14159, 2)}')",
        "print(f'{random.random()}')",
    ]
