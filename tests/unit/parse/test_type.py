"""Tests for type validation and normalization."""

import pytest

from src.common.types import validate_simple_type as validate_type
from src.core.exceptions import TypeValidationError


def test_type_validation() -> None:
    """Test type validation."""
    # Test valid types
    assert validate_type({"name": "integer", "is_array": False, "array_bounds": None})
    assert validate_type({"name": "string", "is_array": True, "array_bounds": [10]})
    assert validate_type({"name": "MyType", "is_array": False, "array_bounds": None})

    # Test invalid types
    with pytest.raises(TypeValidationError, match="Invalid type name"):
        validate_type({"name": 123})  # Invalid name type

    with pytest.raises(TypeValidationError, match="Invalid is_array value"):
        validate_type({"name": "integer", "is_array": "yes"})  # Invalid is_array type

    with pytest.raises(TypeValidationError, match="Invalid array bounds"):
        validate_type(
            {"name": "string", "array_bounds": "large"},
        )  # Invalid bounds type
