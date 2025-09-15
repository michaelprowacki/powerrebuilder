"""Tests for function and procedure AST nodes."""

import pytest

from src.model.ast import (
    Block,
    Expression,
    FunctionCall,
    FunctionDefinition,
    Parameter,
    ProcedureCall,
    ProcedureDefinition,
    Signature,
    TypeRegistry,
)
from src.model.utils.validators import ASTValidator


@pytest.fixture
def type_registry():
    """Create a type registry for testing."""
    return TypeRegistry()


@pytest.fixture
def ast_validator(type_registry):
    """Create an AST validator for testing."""
    return ASTValidator(type_registry)


def test_parameter_validation(type_registry):
    """Test parameter validation."""
    int_type = type_registry.get_type("INTEGER")
    param = Parameter("x", int_type)

    # Required parameter without value
    assert not param.validate({"type_registry": type_registry, "value": None})

    # Required parameter with value
    assert param.validate({"type_registry": type_registry, "value": Expression()})

    # Optional parameter without value
    param_with_default = Parameter("y", int_type, default_value=Expression())
    assert param_with_default.validate({"type_registry": type_registry, "value": None})


def test_signature_validation(type_registry):
    """Test function signature validation."""
    int_type = type_registry.get_type("INTEGER")
    string_type = type_registry.get_type("STRING")

    signature = Signature(
        name="test_func",
        parameters=[
            Parameter("x", int_type),
            Parameter("y", string_type, default_value=Expression()),
        ],
        return_type=int_type,
    )

    # Correct number of arguments
    assert signature.validate(
        {"type_registry": type_registry, "args": [Expression(), Expression()]},
    )

    # Missing optional argument
    assert signature.validate({"type_registry": type_registry, "args": [Expression()]})

    # Too many arguments
    assert not signature.validate(
        {
            "type_registry": type_registry,
            "args": [Expression(), Expression(), Expression()],
        },
    )


def test_function_definition(ast_validator):
    """Test function definition and validation."""
    int_type = ast_validator.type_registry.get_type("INTEGER")

    func = FunctionDefinition(
        signature=Signature(
            name="factorial",
            parameters=[Parameter("n", int_type)],
            return_type=int_type,
        ),
        body=Block([Expression()]),  # n * factorial(n - 1)
        local_variables={"result": int_type},
    )

    assert ast_validator.validate_function(func)
    assert (
        ast_validator.current_scope.get_function("factorial") is None
    )  # Back to original scope


def test_procedure_definition(ast_validator):
    """Test procedure definition and validation."""
    string_type = ast_validator.type_registry.get_type("STRING")

    proc = ProcedureDefinition(
        signature=Signature(
            name="print_message",
            parameters=[Parameter("msg", string_type)],
        ),
        body=Block([Expression()]),  # OUTPUT msg
        local_variables={},
    )

    assert ast_validator.validate_procedure(proc)
    assert (
        ast_validator.current_scope.get_procedure("print_message") is None
    )  # Back to original scope


def test_function_call_validation(ast_validator):
    """Test function call validation."""
    int_type = ast_validator.type_registry.get_type("INTEGER")

    # Define function
    func = FunctionDefinition(
        signature=Signature(
            name="add",
            parameters=[
                Parameter("a", int_type),
                Parameter("b", int_type),
            ],
            return_type=int_type,
        ),
        body=Block([Expression()]),  # return a + b
    )
    ast_validator.current_scope.declare_function(func)

    # Test valid call
    call = FunctionCall("add", [Expression(), Expression()])
    assert ast_validator.validate_function_call(call)

    # Test invalid call (wrong number of arguments)
    invalid_call = FunctionCall("add", [Expression()])
    assert not ast_validator.validate_function_call(invalid_call)

    # Test call to undefined function
    undefined_call = FunctionCall("undefined", [])
    assert not ast_validator.validate_function_call(undefined_call)


def test_procedure_call_validation(ast_validator):
    """Test procedure call validation."""
    string_type = ast_validator.type_registry.get_type("STRING")
    int_type = ast_validator.type_registry.get_type("INTEGER")

    # Define procedure
    proc = ProcedureDefinition(
        signature=Signature(
            name="print_formatted",
            parameters=[
                Parameter("template", string_type),
                Parameter("value", int_type),
            ],
        ),
        body=Block([Expression()]),  # OUTPUT template + STRING(value)
    )
    ast_validator.current_scope.declare_procedure(proc)

    # Test valid call
    call = ProcedureCall("print_formatted", [Expression(), Expression()])
    assert ast_validator.validate_procedure_call(call)

    # Test invalid call (wrong number of arguments)
    invalid_call = ProcedureCall("print_formatted", [Expression()])
    assert not ast_validator.validate_procedure_call(invalid_call)

    # Test call to undefined procedure
    undefined_call = ProcedureCall("undefined", [])
    assert not ast_validator.validate_procedure_call(undefined_call)


def test_nested_scope_handling(ast_validator):
    """Test nested scope handling."""
    int_type = ast_validator.type_registry.get_type("INTEGER")

    # Define outer function
    outer_func = FunctionDefinition(
        signature=Signature(
            name="outer",
            parameters=[Parameter("x", int_type)],
            return_type=int_type,
        ),
        body=Block(
            [
                # Define inner function
                FunctionDefinition(
                    signature=Signature(
                        name="inner",
                        parameters=[Parameter("y", int_type)],
                        return_type=int_type,
                    ),
                    body=Block([Expression()]),  # return x + y
                    local_variables={},
                ),
                Expression(),  # return inner(x)
            ],
        ),
        local_variables={},
    )

    # Validate outer function
    assert ast_validator.validate_function(outer_func)

    # Inner function should not be visible in outer scope
    assert ast_validator.current_scope.get_function("inner") is None


def test_recursive_function_validation(ast_validator):
    """Test recursive function validation."""
    int_type = ast_validator.type_registry.get_type("INTEGER")

    # Define factorial function
    factorial = FunctionDefinition(
        signature=Signature(
            name="factorial",
            parameters=[Parameter("n", int_type)],
            return_type=int_type,
        ),
        body=Block(
            [
                Expression(),  # if n <= 1 return 1
                Expression(),  # return n * factorial(n - 1)
            ],
        ),
        local_variables={},
    )

    # Register function before validation to allow recursive calls
    ast_validator.current_scope.declare_function(factorial)
    assert ast_validator.validate_function(factorial)


def test_scope_variable_visibility(ast_validator):
    """Test variable visibility across scopes."""
    int_type = ast_validator.type_registry.get_type("INTEGER")

    # Declare global variable
    ast_validator.current_scope.declare_variable("global_var", int_type)

    # Enter new scope
    ast_validator.enter_scope()

    # Declare local variable
    ast_validator.current_scope.declare_variable("local_var", int_type)

    # Test visibility
    assert ast_validator.current_scope.get_variable("global_var") == int_type
    assert ast_validator.current_scope.get_variable("local_var") == int_type

    # Exit scope
    ast_validator.exit_scope()

    # Test visibility in original scope
    assert ast_validator.current_scope.get_variable("global_var") == int_type
    assert ast_validator.current_scope.get_variable("local_var") is None


def test_function_overloading(ast_validator):
    """Test function overloading is not allowed."""
    int_type = ast_validator.type_registry.get_type("INTEGER")
    string_type = ast_validator.type_registry.get_type("STRING")

    # Define first version
    func1 = FunctionDefinition(
        signature=Signature(
            name="convert",
            parameters=[Parameter("x", int_type)],
            return_type=string_type,
        ),
        body=Block([Expression()]),
    )
    ast_validator.current_scope.declare_function(func1)

    # Define second version with same name
    func2 = FunctionDefinition(
        signature=Signature(
            name="convert",
            parameters=[Parameter("s", string_type)],
            return_type=int_type,
        ),
        body=Block([Expression()]),
    )

    # Second declaration should replace first
    ast_validator.current_scope.declare_function(func2)
    assert ast_validator.current_scope.get_function("convert") == func2
