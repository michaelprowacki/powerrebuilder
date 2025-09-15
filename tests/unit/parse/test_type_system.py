"""Tests for the enhanced type system."""

import pytest

from src.model.ast import (
    ArrayType,
    BasicType,
    CustomType,
    Type,
    TypeBounds,
    TypeCategory,
    TypeRegistry,
)

# Constants for array dimensions
SINGLE_DIMENSION = 1
MULTI_DIMENSION = 2
ARRAY_SIZE = 10


@pytest.fixture
def type_registry() -> TypeRegistry:
    """Create a type registry for testing."""
    return TypeRegistry()


def test_basic_type_categories() -> None:
    """Test basic type categorization."""
    assert BasicType.INTEGER.category == TypeCategory.NUMERIC
    assert BasicType.REAL.category == TypeCategory.NUMERIC
    assert BasicType.STRING.category == TypeCategory.TEXT
    assert BasicType.BOOLEAN.category == TypeCategory.LOGICAL
    assert BasicType.DATE.category == TypeCategory.COMPOSITE


def test_type_bounds_validation() -> None:
    """Test array bounds validation."""
    # Valid bounds
    bounds = TypeBounds(1, 10)
    assert bounds.validate() is True
    assert bounds.size == 10

    # Invalid bounds
    invalid_bounds = TypeBounds(10, 1)
    assert invalid_bounds.validate() is False

    # Variable bounds
    var_bounds = TypeBounds("start", "end")
    assert var_bounds.validate() is True  # Can't validate at compile time
    assert var_bounds.size is None


def test_array_type_validation(type_registry: TypeRegistry) -> None:
    """Test array type validation."""
    bounds = [TypeBounds(1, 5)]
    array_type = type_registry.create_array_type("INTEGER", bounds)

    # Valid array
    assert array_type.validate_value([1, 2, 3, 4, 5]) is True

    # Invalid element type
    assert array_type.validate_value([1, "two", 3]) is False

    # Invalid bounds
    assert array_type.validate_bounds([0]) is False  # Below lower bound
    assert array_type.validate_bounds([6]) is False  # Above upper bound
    assert array_type.validate_bounds([1, 2]) is False  # Wrong dimensions


def test_multidimensional_array_type(type_registry: TypeRegistry) -> None:
    """Test multi-dimensional array types."""
    bounds = [
        TypeBounds(1, 3),
        TypeBounds(1, 2),
    ]
    matrix_type = type_registry.create_array_type("REAL", bounds)

    # Valid matrix
    valid_matrix = [
        [1.0, 2.0],
        [3.0, 4.0],
        [5.0, 6.0],
    ]
    assert matrix_type.validate_value(valid_matrix) is True

    # Invalid dimensions
    invalid_matrix = [
        [1.0, 2.0, 3.0],  # Too many columns
        [4.0, 5.0, 6.0],
    ]
    assert matrix_type.validate_value(invalid_matrix) is False


def test_type_compatibility(type_registry: TypeRegistry) -> None:
    """Test type assignment compatibility."""
    int_type = type_registry.get_type("INTEGER")
    real_type = type_registry.get_type("REAL")
    string_type = type_registry.get_type("STRING")
    any_type = type_registry.get_type("ANY")

    # Numeric type conversions
    assert real_type.can_assign_from(int_type) is True
    assert int_type.can_assign_from(real_type) is True

    # String to numeric
    assert int_type.can_assign_from(string_type) is False
    assert real_type.can_assign_from(string_type) is False

    # ANY type accepts all
    assert any_type.can_assign_from(int_type) is True
    assert any_type.can_assign_from(string_type) is True


def test_custom_type_inheritance(type_registry: TypeRegistry) -> None:
    """Test custom type inheritance and field access."""
    # Create base type
    base_type = CustomType(
        name="Shape",
        category=TypeCategory.CUSTOM,
        fields={
            "x": type_registry.get_type("INTEGER"),
            "y": type_registry.get_type("INTEGER"),
        },
    )
    type_registry.register_custom_type(base_type)

    # Create derived type
    circle_type = CustomType(
        name="Circle",
        category=TypeCategory.CUSTOM,
        fields={
            "radius": type_registry.get_type("REAL"),
        },
        parent_type=base_type,
    )
    type_registry.register_custom_type(circle_type)

    # Test field access
    assert circle_type.get_field_type("radius") is not None
    assert circle_type.get_field_type("x") is not None  # Inherited
    assert circle_type.get_field_type("y") is not None  # Inherited
    assert circle_type.get_field_type("nonexistent") is None


def test_array_of_custom_type(type_registry: TypeRegistry) -> None:
    """Test arrays of custom types."""
    # Create custom type
    point_type = CustomType(
        name="Point",
        category=TypeCategory.CUSTOM,
        fields={
            "x": type_registry.get_type("INTEGER"),
            "y": type_registry.get_type("INTEGER"),
        },
    )
    type_registry.register_custom_type(point_type)

    # Create array of points
    bounds = [TypeBounds(1, 3)]
    points_array_type = type_registry.create_array_type("Point", bounds)

    # Valid array of points
    valid_points = [
        {"x": 1, "y": 1},
        {"x": 2, "y": 2},
        {"x": 3, "y": 3},
    ]
    assert points_array_type.validate_value(valid_points) is True

    # Invalid point data
    invalid_points = [
        {"x": 1, "y": 1},
        {"x": "2", "y": 2},  # Invalid x type
        {"x": 3, "y": 3},
    ]
    assert points_array_type.validate_value(invalid_points) is False


def test_type_constraints() -> None:
    """Test type constraints."""
    # Create constrained integer type
    positive_int = Type(
        name="POSITIVE_INTEGER",
        category=TypeCategory.NUMERIC,
        constraints={
            "min": 0,
        },
    )

    # Create constrained string type
    email_type = Type(
        name="EMAIL",
        category=TypeCategory.TEXT,
        constraints={
            "pattern": r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$",
        },
    )

    # Test constraint validation
    assert positive_int.validate_value(10) is True
    assert positive_int.validate_value(-5) is False
    assert email_type.validate_value("test@example.com") is True
    assert email_type.validate_value("invalid-email") is False


def test_type_registry_management(type_registry: TypeRegistry) -> None:
    """Test type registry management."""
    # All basic types should be registered
    for basic_type in BasicType:
        assert type_registry.get_type(basic_type.type_name) is not None

    # Register custom type
    custom_type = CustomType(
        name="MyType",
        category=TypeCategory.CUSTOM,
        fields={
            "field1": type_registry.get_type("INTEGER"),
            "field2": type_registry.get_type("STRING"),
        },
    )
    type_registry.register_custom_type(custom_type)

    # Retrieve registered type
    retrieved_type = type_registry.get_type("MyType")
    assert retrieved_type is not None
    assert retrieved_type.name == "MyType"
    assert retrieved_type.get_field_type("field1") is not None


def test_array_bounds_edge_cases() -> None:
    """Test edge cases for array bounds."""
    # Zero-based bounds
    bounds1 = TypeBounds(0, 5)
    assert bounds1.validate() is True
    assert bounds1.size == 6

    # Single element bounds
    bounds2 = TypeBounds(1, 1)
    assert bounds2.validate() is True
    assert bounds2.size == 1

    # Variable upper bound
    bounds3 = TypeBounds(1, "n")
    assert bounds3.validate() is True
    assert bounds3.size is None


def test_type_system_error_cases(type_registry: TypeRegistry) -> None:
    """Test error cases in type system."""
    with pytest.raises(ValueError, match="bounds"):
        # Try to create array with invalid bounds
        type_registry.create_array_type("INTEGER", [TypeBounds(5, 1)])

    with pytest.raises(KeyError, match="NONEXISTENT_TYPE"):
        # Try to get non-existent type
        type_registry.get_type("NONEXISTENT_TYPE")

    with pytest.raises(ValueError, match="InvalidType"):
        # Try to register custom type with invalid field type
        CustomType(
            name="InvalidType",
            category=TypeCategory.CUSTOM,
            fields={
                "field": "not_a_type",  # Invalid type
            },
        )


def test_basic_type() -> None:
    """Test basic type functionality."""
    # ... rest of function unchanged ...


def test_custom_type() -> None:
    """Test custom type functionality."""
    # ... rest of function unchanged ...


def test_array_type() -> None:
    """Test array type functionality."""
    # Create array types
    int_type = Type(name="integer", category=TypeCategory.NUMERIC)
    int_array = ArrayType(
        name="integer[]",
        category=TypeCategory.NUMERIC,
        bounds=[TypeBounds(lower=1, upper=ARRAY_SIZE)],
        element_type=int_type,
    )
    int_matrix = ArrayType(
        name="integer[][]",
        category=TypeCategory.NUMERIC,
        bounds=[
            TypeBounds(lower=1, upper=ARRAY_SIZE),
            TypeBounds(lower=1, upper=ARRAY_SIZE),
        ],
        element_type=int_type,
    )

    # Test dimensions
    assert len(int_array.bounds) == SINGLE_DIMENSION
    assert len(int_matrix.bounds) == MULTI_DIMENSION

    # ... rest of function unchanged ...


def test_datawindow_type() -> None:
    """Test DataWindow type functionality."""
    # ... rest of function unchanged ...


def test_type_ownership() -> None:
    """Test type ownership functionality."""
    # ... rest of function unchanged ...


def test_type_registry() -> None:
    """Test type registry functionality."""
    # ... rest of function unchanged ...


def test_namespaced_types() -> None:
    """Test types with namespaces."""
    # ... rest of function unchanged ...


def test_type_inheritance_chain() -> None:
    """Test type inheritance chain."""
    # ... rest of function unchanged ...
