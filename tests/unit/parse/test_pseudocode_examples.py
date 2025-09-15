"""Tests for example pseudocode files."""

import pytest

from src.parse.parser.specialized.pseudocode import PowerBuilderPseudocodeParser


@pytest.fixture
def parser() -> PowerBuilderPseudocodeParser:
    """Create a pseudocode parser instance."""
    return PowerBuilderPseudocodeParser()


def test_factorial_example(parser: PowerBuilderPseudocodeParser) -> None:
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
        "def Factorial(Num: int) -> int:",
        "    if Num == 0 or Num == 1:",
        "        return 1",
        "    else:",
        "        return Num * Factorial(Num - 1)",
        "",
        "Number = input('Enter Number: ')",
        "Number = int(Number)",
        "",
        "print(Factorial(Number))",
    ]


def test_array_example(parser: PowerBuilderPseudocodeParser) -> None:
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
        "    print(numbers[i])",
    ]


def test_file_example(parser: PowerBuilderPseudocodeParser) -> None:
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
        "print(line)",
        "",
        "data.close()",
    ]


def test_error_handling_example(parser: PowerBuilderPseudocodeParser) -> None:
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


def test_arrow_operator(parser: PowerBuilderPseudocodeParser) -> None:
    """Test both arrow operators for assignment."""
    code = """
    x <- 5
    y ← 10
    """
    ast = parser.parse(code)
    assert ast is not None


def test_array_bounds(parser: PowerBuilderPseudocodeParser) -> None:
    """Test array declaration with bounds."""
    code = """
    DECLARE numbers : ARRAY[1:10] OF INTEGER
    DECLARE matrix : ARRAY[0:3, 0:3] OF REAL
    """
    ast = parser.parse(code)
    assert ast is not None


def test_case_statement(parser: PowerBuilderPseudocodeParser) -> None:
    """Test CASE statement with OTHERWISE clause."""
    code = """
    CASE OF grade
        "A": OUTPUT "Excellent"
        "B": OUTPUT "Good"
        "C": OUTPUT "Fair"
        OTHERWISE: OUTPUT "Need improvement"
    ENDCASE
    """
    ast = parser.parse(code)
    assert ast is not None


def test_for_loop_with_step(parser: PowerBuilderPseudocodeParser) -> None:
    """Test FOR loop with STEP keyword."""
    code = """
    FOR i <- 0 TO 10 STEP 2
        OUTPUT i
    NEXT i
    """
    ast = parser.parse(code)
    assert ast is not None


def test_repeat_until(parser: PowerBuilderPseudocodeParser) -> None:
    """Test REPEAT-UNTIL loop."""
    code = """
    REPEAT
        INPUT x
        OUTPUT x
    UNTIL x = 0
    """
    ast = parser.parse(code)
    assert ast is not None


def test_file_operations(parser: PowerBuilderPseudocodeParser) -> None:
    """Test file I/O operations."""
    code = """
    OPENFILE "data.txt" FOR READ
    READFILE "data.txt", content
    CLOSEFILE "data.txt"
    OPENFILE "output.txt" FOR WRITE
    WRITEFILE "output.txt", "Hello World"
    CLOSEFILE "output.txt"
    """
    ast = parser.parse(code)
    assert ast is not None


def test_factorial_function(parser: PowerBuilderPseudocodeParser) -> None:
    """Test recursive function with type declarations."""
    code = """
    FUNCTION Factorial(n: INTEGER) RETURNS INTEGER
        IF n = 0 OR n = 1 THEN
            RETURN 1
        ELSE
            RETURN n * Factorial(n - 1)
        ENDIF
    ENDFUNCTION
    """
    ast = parser.parse(code)
    assert ast is not None


def test_array_operations(parser: PowerBuilderPseudocodeParser) -> None:
    """Test array operations and multi-dimensional arrays."""
    code = """
    DECLARE list : ARRAY[1:5] OF INTEGER
    DECLARE grid : ARRAY[1:3, 1:3] OF REAL
    list[1] <- 10
    grid[1,1] <- 3.14
    """
    ast = parser.parse(code)
    assert ast is not None


def test_procedure_declaration(parser: PowerBuilderPseudocodeParser) -> None:
    """Test procedure declaration with parameters."""
    code = """
    PROCEDURE PrintArray(arr: ARRAY[1:10] OF INTEGER)
        FOR i <- 1 TO 10
            OUTPUT arr[i]
        NEXT i
    ENDPROCEDURE
    """
    ast = parser.parse(code)
    assert ast is not None


def test_expression_precedence(parser: PowerBuilderPseudocodeParser) -> None:
    """Test expression precedence rules."""
    code = """
    result <- 2 + 3 * 4 ^ 2 - (6 / 2)
    """
    ast = parser.parse(code)
    assert ast is not None


def test_sieve_of_eratosthenes() -> None:
    """Test complex array and loop handling with the Sieve of Eratosthenes algorithm."""
    code = """
    DECLARE limit : INTEGER
    INPUT limit
    DECLARE isPrime : ARRAY[2:limit] OF BOOLEAN
    FOR i <- 2 TO limit
        isPrime[i] <- TRUE
    NEXT i
    FOR i <- 2 TO limit
        IF isPrime[i] = TRUE THEN
            FOR j <- 2 TO limit/i
                isPrime[i*j] <- FALSE
            NEXT j
        ENDIF
    NEXT i
    """
    ast = parser.parse(code)
    assert ast is not None


def test_string_manipulation(parser: PowerBuilderPseudocodeParser) -> None:
    """Test string operations and concatenation."""
    code = """
    DECLARE name : STRING
    INPUT name
    IF LENGTH(name) > 0 THEN
        OUTPUT "Hello " + UCASE(name)
    ENDIF
    """
    ast = parser.parse(code)
    assert ast is not None


def test_nested_control_structures(parser: PowerBuilderPseudocodeParser) -> None:
    """Test nested IF and loop structures."""
    code = """
    FOR i <- 1 TO 10
        IF i MOD 2 = 0 THEN
            REPEAT
                OUTPUT i
                i <- i - 1
            UNTIL i < 0
        ELSE
            CASE OF i
                1: OUTPUT "One"
                3: OUTPUT "Three"
                5: OUTPUT "Five"
                OTHERWISE: OUTPUT "Other"
            ENDCASE
        ENDIF
    NEXT i
    """
    ast = parser.parse(code)
    assert ast is not None


def test_invalid_array_bounds(parser: PowerBuilderPseudocodeParser) -> None:
    """Test error handling for invalid array bounds."""
    code = """
    DECLARE arr : ARRAY[5:1] OF INTEGER  # Upper bound less than lower bound
    """
    with pytest.raises(ValueError, match="bound"):
        parser.parse(code)


def test_invalid_case_statement(parser: PowerBuilderPseudocodeParser) -> None:
    """Test error handling for invalid CASE statement."""
    code = """
    CASE OF x
        1: OUTPUT "One"
        OTHERWISE: OUTPUT "Other"
        2: OUTPUT "Two"  # Case after OTHERWISE
    ENDCASE
    """
    with pytest.raises(SyntaxError, match="CASE"):
        parser.parse(code)


def test_type_mismatch(parser: PowerBuilderPseudocodeParser) -> None:
    """Test error handling for type mismatches."""
    code = """
    DECLARE x : INTEGER
    x <- "Hello"  # Assigning string to integer
    """
    with pytest.raises(TypeError, match="type"):
        parser.parse(code)


def test_complete_program(parser: PowerBuilderPseudocodeParser) -> None:
    """Test a complete program using multiple features."""
    code = """
    FUNCTION BinarySearch(arr: ARRAY[1:10] OF INTEGER, target: INTEGER) RETURNS INTEGER
        DECLARE left : INTEGER
        DECLARE right : INTEGER
        DECLARE mid : INTEGER
        left <- 1
        right <- 10
        REPEAT
            mid <- (left + right) / 2
            CASE OF COMPARE(arr[mid], target)
                -1: left <- mid + 1
                1: right <- mid - 1
                0: RETURN mid
            ENDCASE
        UNTIL left > right
        RETURN -1
    ENDFUNCTION
    PROCEDURE PrintResult(index: INTEGER)
        IF index >= 0 THEN
            OUTPUT "Found at position: " + STRING(index)
        ELSE
            OUTPUT "Not found"
        ENDIF
    ENDPROCEDURE
    // Main program
    DECLARE numbers : ARRAY[1:10] OF INTEGER
    DECLARE searchValue : INTEGER
    FOR i <- 1 TO 10
        numbers[i] <- i * 2
    NEXT i
    INPUT searchValue
    PrintResult(BinarySearch(numbers, searchValue))
    """
    ast = parser.parse(code)
    assert ast is not None
