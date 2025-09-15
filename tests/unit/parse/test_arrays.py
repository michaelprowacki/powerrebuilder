"""Tests for array operations and validation."""

import pytest

from src.model.ast import (
    ArrayAccess,
    ArrayAssignment,
    ArrayDeclaration,
    ArrayOperation,
    ArraySlice,
    ArrayType,
    BasicType,
    Type,
    TypeBounds,
    TypeCategory,
)


@pytest.fixture
def integer_type():
    """Fixture for INTEGER type."""
    return Type(
        name="INTEGER",
        category=TypeCategory.NUMERIC,
    )


@pytest.fixture
def string_type():
    """Fixture for STRING type."""
    return Type(
        name=BasicType.STRING.type_name,
        category=TypeCategory.TEXT,
    )


@pytest.fixture
def simple_array_type(integer_type):
    """Fixture for 1D integer array type."""
    return ArrayType(
        name="ARRAY OF INTEGER",
        category=TypeCategory.COMPOSITE,
        element_type=integer_type,
        bounds=[TypeBounds(1, 10)],
    )


@pytest.fixture
def matrix_type(integer_type):
    """Fixture for 2D integer array type."""
    return ArrayType(
        name="ARRAY OF INTEGER",
        category=TypeCategory.COMPOSITE,
        element_type=integer_type,
        bounds=[
            TypeBounds(1, 3),
            TypeBounds(1, 4),
        ],
    )


def test_array_declaration_validation(integer_type):
    """Test array declaration validation."""
    # Valid declaration
    decl = ArrayDeclaration(
        name="numbers",
        element_type=integer_type,
        bounds=[TypeBounds(1, 10)],
        initial_value=[1, 2, 3],
    )
    assert decl.validate()

    # Invalid bounds
    decl = ArrayDeclaration(
        name="numbers",
        element_type=integer_type,
        bounds=[TypeBounds(10, 1)],  # Upper < lower
        initial_value=[1, 2, 3],
    )
    assert not decl.validate()

    # Invalid initial value type
    decl = ArrayDeclaration(
        name="numbers",
        element_type=integer_type,
        bounds=[TypeBounds(1, 10)],
        initial_value=["a", "b", "c"],  # Strings instead of integers
    )
    assert not decl.validate()


def test_array_access_validation(simple_array_type):
    """Test array access validation."""
    # Valid access
    access = ArrayAccess(
        array_name="numbers",
        indices=[5],
        array_type=simple_array_type,
    )
    assert access.validate()

    # Index out of bounds
    access = ArrayAccess(
        array_name="numbers",
        indices=[11],  # Beyond upper bound
        array_type=simple_array_type,
    )
    assert not access.validate()

    # Wrong number of dimensions
    access = ArrayAccess(
        array_name="numbers",
        indices=[1, 2],  # 2D access on 1D array
        array_type=simple_array_type,
    )
    assert not access.validate()


def test_array_assignment_validation(simple_array_type, integer_type):
    """Test array assignment validation."""
    access = ArrayAccess(
        array_name="numbers",
        indices=[5],
        array_type=simple_array_type,
    )

    # Valid assignment
    assignment = ArrayAssignment(
        access=access,
        value=42,
    )
    assert assignment.validate()

    # Invalid value type
    assignment = ArrayAssignment(
        access=access,
        value="string",  # String instead of integer
    )
    assert not assignment.validate()


def test_array_slice_validation(matrix_type):
    """Test array slice validation."""
    # Valid 2D slice
    slice_op = ArraySlice(
        array_name="matrix",
        start_indices=[1, 1],
        end_indices=[2, 3],
        array_type=matrix_type,
    )
    assert slice_op.validate()

    # Invalid: end before start
    slice_op = ArraySlice(
        array_name="matrix",
        start_indices=[2, 1],
        end_indices=[1, 3],
        array_type=matrix_type,
    )
    assert not slice_op.validate()

    # Invalid: out of bounds
    slice_op = ArraySlice(
        array_name="matrix",
        start_indices=[1, 1],
        end_indices=[3, 5],  # Beyond upper bound
        array_type=matrix_type,
    )
    assert not slice_op.validate()


def test_array_operations(simple_array_type, matrix_type):
    """Test array operations."""
    # Test LENGTH
    op = ArrayOperation(
        array_name="numbers",
        operation=ArrayOperation.Operation.LENGTH,
        array_type=simple_array_type,
    )
    assert op.validate()

    # Test COPY
    op = ArrayOperation(
        array_name="numbers",
        operation=ArrayOperation.Operation.COPY,
        array_type=simple_array_type,
    )
    assert op.validate()

    # Test CONCAT with compatible array
    op = ArrayOperation(
        array_name="numbers",
        operation=ArrayOperation.Operation.CONCAT,
        parameters=[simple_array_type],
        array_type=simple_array_type,
    )
    assert op.validate()

    # Test RESIZE
    op = ArrayOperation(
        array_name="matrix",
        operation=ArrayOperation.Operation.RESIZE,
        parameters=[5, 6],  # New dimensions
        array_type=matrix_type,
    )
    assert op.validate()

    # Test invalid RESIZE (wrong number of dimensions)
    op = ArrayOperation(
        array_name="matrix",
        operation=ArrayOperation.Operation.RESIZE,
        parameters=[5],  # Only one dimension for 2D array
        array_type=matrix_type,
    )
    assert not op.validate()

    # Test unknown operation
    op = ArrayOperation(
        array_name="numbers",
        operation="UNKNOWN",
        array_type=simple_array_type,
    )
    assert not op.validate()
