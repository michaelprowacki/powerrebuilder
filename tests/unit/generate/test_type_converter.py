"""Unit tests for PowerBuilder to Dart type converter."""

import json
from pathlib import Path
from unittest.mock import Mock, mock_open, patch

from src.generate.converters.flutter.models import TypeConverter


class TestTypeConverter:
    """Test suite for TypeConverter."""

    def test_init_default_mapping_file(self):
        """Test initialization with default mapping file."""
        with patch("builtins.open", mock_open(read_data='{"type_mappings": {}}')):
            converter = TypeConverter()
            assert converter.mappings is not None
            assert isinstance(converter._type_cache, dict)

    def test_init_custom_mapping_file(self, tmp_path):
        """Test initialization with custom mapping file."""
        mapping_file = tmp_path / "custom_mapping.json"
        mapping_data = {
            "type_mappings": {
                "basic_types": {
                    "integer": {
                        "dart_type": "int",
                        "nullable_syntax": "int?",
                        "default_value": "0",
                    },
                },
            },
        }
        mapping_file.write_text(json.dumps(mapping_data))

        converter = TypeConverter(mapping_file)
        assert "basic_types" in converter.mappings
        assert "integer" in converter.mappings["basic_types"]

    def test_load_mappings_file_not_found(self):
        """Test loading mappings when file doesn't exist."""
        converter = TypeConverter(Path("nonexistent.json"))
        # Should fall back to default mappings
        assert "basic_types" in converter.mappings
        assert "integer" in converter.mappings["basic_types"]

    def test_convert_basic_types(self):
        """Test converting basic PowerBuilder types."""
        converter = TypeConverter()

        # Test integer types
        assert converter.convert_type("integer") == "int"
        assert converter.convert_type("long") == "int"
        assert converter.convert_type("number") == "int"

        # Test decimal types
        assert converter.convert_type("decimal") == "double"
        assert converter.convert_type("real") == "double"
        assert converter.convert_type("double") == "double"

        # Test string types
        assert converter.convert_type("string") == "String"
        assert converter.convert_type("char") == "String"

        # Test other types
        assert converter.convert_type("boolean") == "bool"
        assert converter.convert_type("date") == "DateTime"
        assert converter.convert_type("time") == "DateTime"
        assert converter.convert_type("datetime") == "DateTime"
        assert converter.convert_type("blob") == "Uint8List"
        assert converter.convert_type("any") == "dynamic"

    def test_convert_nullable_types(self):
        """Test converting nullable types."""
        converter = TypeConverter()

        assert converter.convert_type("integer", nullable=True) == "int?"
        assert converter.convert_type("string", nullable=True) == "String?"
        assert converter.convert_type("boolean", nullable=True) == "bool?"
        assert converter.convert_type("date", nullable=True) == "DateTime?"
        assert converter.convert_type("blob", nullable=True) == "Uint8List?"

        # Dynamic is always nullable
        assert converter.convert_type("any", nullable=True) == "dynamic"

    def test_convert_array_types(self):
        """Test converting array types."""
        converter = TypeConverter()

        # String notation
        assert converter.convert_type("integer[]") == "List<int>"
        assert converter.convert_type("string[]") == "List<String>"
        assert converter.convert_type("boolean[]") == "List<bool>"
        assert converter.convert_type("date[]") == "List<DateTime>"

        # Nullable arrays
        assert converter.convert_type("integer[]", nullable=True) == "List<int>?"
        assert converter.convert_type("string[]", nullable=True) == "List<String>?"

    def test_convert_type_objects(self):
        """Test converting Type objects instead of strings."""
        converter = TypeConverter()

        # Mock Type object
        type_obj = Mock()
        type_obj.name = "integer"
        type_obj.is_nullable = False
        type_obj.is_array = False

        assert converter.convert_type(type_obj) == "int"

        # Nullable Type object
        type_obj.is_nullable = True
        assert converter.convert_type(type_obj) == "int?"

        # Array Type object
        type_obj.is_array = True
        type_obj.is_nullable = False
        assert converter.convert_type(type_obj) == "List<int>"

    def test_convert_unknown_types(self):
        """Test converting unknown PowerBuilder types."""
        converter = TypeConverter()

        # Unknown types should return as-is
        assert converter.convert_type("customtype") == "dynamic"
        assert converter.convert_type("unknowntype") == "dynamic"

    def test_convert_case_insensitive(self):
        """Test that type conversion is case insensitive."""
        converter = TypeConverter()

        assert converter.convert_type("INTEGER") == "int"
        assert converter.convert_type("Integer") == "int"
        assert converter.convert_type("STRING") == "String"
        assert converter.convert_type("String") == "String"

    def test_type_cache(self):
        """Test that converted types are cached."""
        converter = TypeConverter()

        # First call
        result1 = converter.convert_type("integer")
        assert "integer:False:False" in converter._type_cache

        # Second call should use cache
        with patch.object(converter, "_get_dart_type") as mock_get:
            result2 = converter.convert_type("integer")
            mock_get.assert_not_called()  # Should not be called due to cache
            assert result1 == result2

    def test_decimal_precision(self):
        """Test decimal type with precision."""
        converter = TypeConverter()

        # PowerBuilder decimal(2) should still map to double
        assert converter.convert_type("decimal(2)") == "double"
        assert converter.convert_type("decimal(10,2)") == "double"

    def test_char_length(self):
        """Test char type with length."""
        converter = TypeConverter()

        # PowerBuilder char(50) should still map to String
        assert converter.convert_type("char(50)") == "String"
        assert converter.convert_type("char(1)") == "String"

    def test_get_default_value(self):
        """Test getting default values for types."""
        converter = TypeConverter()

        assert converter.get_default_value("integer") == "0"
        assert converter.get_default_value("string") == "''"
        assert converter.get_default_value("boolean") == "false"
        assert converter.get_default_value("date") == "DateTime.now()"
        assert converter.get_default_value("blob") == "Uint8List(0)"
        assert converter.get_default_value("any") == "null"

    def test_get_imports_for_type(self):
        """Test getting required imports for Dart types."""
        converter = TypeConverter()

        # Basic types don't need imports
        assert converter.get_imports_for_type("integer") == []
        assert converter.get_imports_for_type("string") == []

        # Complex types need imports
        imports = converter.get_imports_for_type("blob")
        assert any("dart:typed_data" in imp for imp in imports)
        assert any("dart:convert" in imp for imp in imports)

        imports = converter.get_imports_for_type("date")
        assert len(imports) == 0  # DateTime is built-in

    def test_is_complex_type(self):
        """Test identifying complex types."""
        converter = TypeConverter()

        # Basic types
        assert not converter.is_complex_type("integer")
        assert not converter.is_complex_type("string")
        assert not converter.is_complex_type("boolean")

        # Complex types
        assert converter.is_complex_type("structure")
        assert converter.is_complex_type("datastore")
        assert converter.is_complex_type("custom_object")

    def test_convert_with_type_parameters(self):
        """Test converting generic types with parameters."""
        converter = TypeConverter()

        # Current implementation doesn't handle parameterized types
        # They default to dynamic
        assert converter.convert_type("list<string>") == "dynamic"
        assert converter.convert_type("map<string,integer>") == "dynamic"

    def test_edge_cases(self):
        """Test edge cases in type conversion."""
        converter = TypeConverter()

        # Empty string
        assert converter.convert_type("") == "dynamic"

        # Whitespace
        assert converter.convert_type("  integer  ") == "int"

        # Special characters in custom types
        assert converter.convert_type("my_custom_type") == "dynamic"

        # Very long type names
        long_type = "a" * 100
        assert converter.convert_type(long_type) == "dynamic"
