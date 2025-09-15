"""Test suite for ExpressionConverter."""

import pytest

from src.generate.converters.utils.expressions import ExpressionConverter


class TestExpressionConverter:
    """Test cases for PowerBuilder to Dart expression conversion."""

    def setup_method(self):
        """Set up test instances."""
        self.converter = ExpressionConverter()

    def test_initialization(self):
        """Test converter initialization."""
        assert self.converter is not None
        assert self.converter.type_converter is not None
        assert len(self.converter.operator_map) > 0
        assert len(self.converter.function_map) > 0

    def test_operator_conversion(self):
        """Test operator conversion from PowerBuilder to Dart."""
        test_cases = [
            ("a = b", "a == b"),
            ("a <> b", "a != b"),
            ("a and b", "a && b"),
            ("a or b", "a || b"),
            ("not valid", "! valid"),
            ("x mod 10", "x % 10"),
            ("a = b and c <> d", "a == b && c != d"),
            ("x > 5 or y < 3", "x > 5 || y < 3"),
        ]

        for pb_expr, expected in test_cases:
            result = self.converter._convert_operators(pb_expr)
            assert result == expected

    def test_null_handling_conversion(self):
        """Test null handling conversion."""
        test_cases = [
            ("IsNull(myVar)", "myVar == null"),
            ("IsValid(myObj)", "myObj != null"),
            ("SetNull(myVar)", "myVar = null"),
            ("IsNull(employee.name)", "employee.name == null"),
            ("if IsNull(value) then", "if value == null then"),
        ]

        for pb_expr, expected in test_cases:
            result = self.converter._convert_null_handling(pb_expr)
            assert result == expected

    def test_string_function_conversion(self):
        """Test string function conversion."""
        test_cases = [
            ("len(myString)", "myString.length"),
            ("trim(text)", "text.trim()"),
            ("upper(name)", "name.toUpperCase()"),
            ("lower(name)", "name.toLowerCase()"),
            ("ltrim(text)", "text.trimLeft()"),
            ("rtrim(text)", "text.trimRight()"),
            ("pos(haystack, needle)", "haystack.indexOf(needle)"),
            ("replace(text, old, new)", "text.replaceAll(old, new)"),
        ]

        for pb_expr, expected in test_cases:
            result = self.converter._convert_functions(pb_expr)
            assert result == expected

    def test_numeric_function_conversion(self):
        """Test numeric function conversion."""
        test_cases = [
            ("abs(-5)", "abs(-5)"),
            ("ceiling(3.14)", "ceil(3.14)"),
            ("int(value)", "value.toInt()"),
            ("truncate(3.14)", "3.14.truncate()"),
        ]

        for pb_expr, expected in test_cases:
            result = self.converter._convert_functions(pb_expr)
            assert result == expected

    def test_date_function_conversion(self):
        """Test date/time function conversion."""
        test_cases = [
            ("today()", "DateTime.now()"),
            ("now()", "DateTime.now()"),
        ]

        for pb_expr, expected in test_cases:
            result = self.converter._convert_functions(pb_expr)
            assert result == expected

    def test_array_access_conversion(self):
        """Test array access conversion (1-based to 0-based)."""
        test_cases = [
            ("array[1]", "array[0]"),
            ("array[10]", "array[9]"),
            ("matrix[5]", "matrix[4]"),
            ("data[i]", "data[i]"),  # Variable index unchanged
            ("array[0]", "array[0]"),  # Zero index unchanged
        ]

        for pb_expr, expected in test_cases:
            result = self.converter._convert_array_access(pb_expr)
            assert result == expected

    def test_property_access_conversion(self):
        """Test property access conversion."""
        test_cases = [
            ("object::property", "object.property"),
            ("this.text", "this.text"),
            ("checkbox.checked", "checkbox.value"),
            ("dropdown.selected", "dropdown.value"),
            ("control.enabled", "control.enabled"),
            ("window.visible", "window.visible"),
        ]

        for pb_expr, expected in test_cases:
            result = self.converter._convert_property_access(pb_expr)
            assert result == expected

    def test_camel_case_conversion(self):
        """Test snake_case to camelCase conversion."""
        test_cases = [
            ("my_variable", "myVariable"),
            ("employee_name", "employeeName"),
            ("is_valid_user", "isValidUser"),
            ("simple", "simple"),
            ("this.my_property", "this.myProperty"),
            ("object.get_value", "object.getValue"),
        ]

        for snake_case, expected in test_cases:
            result = self.converter._to_camel_case(snake_case)
            assert result == expected

    def test_complex_expression_conversion(self):
        """Test conversion of complex expressions."""
        # Test compound expression
        pb_expr = "len(trim(name)) > 0 and not IsNull(id)"
        result = self.converter.convert_expression(pb_expr)
        assert "trim()" in result
        assert ".length" in result
        assert "&&" in result
        assert "! " in result
        assert "== null" in result

        # Test nested function calls
        pb_expr = "upper(trim(employee_name)) = 'ADMIN'"
        result = self.converter.convert_expression(pb_expr)
        assert "toUpperCase()" in result
        assert "trim()" in result
        assert "==" in result

    def test_assignment_conversion(self):
        """Test assignment statement conversion."""
        test_cases = [
            ("x = 10", "x = 10;"),
            ("name = null", "name = null;"),
            ("is_valid = true", "is_valid = true;"),
            ("enabled = false", "enabled = false;"),
        ]

        for pb_assign, expected in test_cases:
            result = self.converter.convert_assignment(pb_assign)
            assert result == expected

    def test_conditional_conversion(self):
        """Test IF statement conversion."""
        test_cases = [
            ("IF x > 0 THEN", "if (x > 0) {"),
            ("ELSEIF y < 10 THEN", "} else if (y < 10) {"),
            ("ELSE", "} else {"),
            ("END IF", "}"),
            ("if IsNull(value) then", "if (value == null) {"),
        ]

        for pb_if, expected in test_cases:
            result = self.converter.convert_conditional(pb_if)
            assert result == expected

    def test_blob_expression_conversion(self):
        """Test blob expression conversion."""
        test_cases = [
            ("Blob(myString)", "Uint8List.fromList(myString.codeUnits)"),
            ("String(myBlob)", "String.fromCharCodes(myBlob)"),
            ("BlobMid(data, 5, 10)", "data.sublist(5 - 1, (5 - 1) + 10)"),
            ("BlobMid(data, 10)", "data.sublist(10 - 1)"),
            ("Len(blobData)", "blobData.length"),
            ("IsNull(blobVar)", "(blobVar == null)"),
            ("SetNull(blobVar)", "blobVar = null"),
        ]

        for pb_expr, expected in test_cases:
            result = self.converter.convert_blob_expression(pb_expr)
            assert result == expected

    def test_blob_string_with_encoding(self):
        """Test blob to string conversion with encoding."""
        test_cases = [
            ('String(data, "UTF-8")', "utf8.decode(data)"),
            ('String(data, "UTF8")', "utf8.decode(data)"),
            ('String(data, "UTF-16")', "_decodeUtf16(data)"),
            ('String(data, "BASE64")', "base64.encode(data)"),
        ]

        for pb_expr, expected in test_cases:
            result = self.converter.convert_blob_expression(pb_expr)
            assert result == expected

    def test_blob_concatenation(self):
        """Test blob concatenation conversion."""
        pb_expr = "blob1 + blob2"
        result = self.converter.convert_blob_expression(pb_expr)
        assert "Uint8List.fromList([...blob1, ...blob2])" in result

    def test_blob_comparison(self):
        """Test blob comparison conversion."""
        pb_expr = "blob1 == blob2"
        result = self.converter.convert_blob_expression(pb_expr)
        assert "listEquals(blob1, blob2)" in result

    def test_blobedit_conversion(self):
        """Test BlobEdit conversion."""
        pb_expr = "BlobEdit(data, 5, 255)"
        result = self.converter.convert_blob_expression(pb_expr)
        assert "Uint8List.from(data)" in result
        assert "_temp[5 - 1] = 255" in result

    def test_required_imports(self):
        """Test getting required imports for expressions."""
        # Test math import
        expr = "pow(x, 2) + abs(y)"
        imports = self.converter.get_required_imports(expr)
        assert any("dart:math" in imp for imp in imports)

        # Test async import
        expr = "await fetchData()"
        imports = self.converter.get_required_imports(expr)
        assert any("dart:async" in imp for imp in imports)

        # Test typed data import
        expr = "Uint8List.fromList(data)"
        imports = self.converter.get_required_imports(expr)
        assert any("dart:typed_data" in imp for imp in imports)

        # Test convert import
        expr = "base64.encode(blob)"
        imports = self.converter.get_required_imports(expr)
        assert any("dart:convert" in imp for imp in imports)

    def test_required_blob_helpers(self):
        """Test getting required blob helper functions."""
        helpers = self.converter.get_required_blob_helpers()

        assert len(helpers) > 0
        assert any("_decodeUtf16" in helper for helper in helpers)
        assert any("_blobEquals" in helper for helper in helpers)

    def test_expression_with_context(self):
        """Test expression conversion with context."""
        context = {
            "variables": {
                "employee_id": {"type": "integer", "dart_type": "int"},
                "employee_name": {"type": "string", "dart_type": "String"},
            },
        }

        pb_expr = "employee_id > 0 and not IsNull(employee_name)"
        result = self.converter.convert_expression(pb_expr, context)

        assert "employee_id > 0" in result  # Variable names converted
        assert "&&" in result
        assert "employee_name == null" in result

    def test_special_characters_in_strings(self):
        """Test handling of special characters in string literals."""
        # Test that string literals are preserved
        pb_expr = 'name = "John\'s Data"'
        result = self.converter.convert_expression(pb_expr)
        assert '"John\'s Data"' in result

    def test_multiple_operator_conversion(self):
        """Test multiple operators in one expression."""
        pb_expr = "a = b and c <> d or e mod 2 = 0"
        result = self.converter.convert_expression(pb_expr)

        assert "==" in result
        assert "!=" in result
        assert "&&" in result
        assert "||" in result
        assert "%" in result

    def test_case_insensitive_functions(self):
        """Test case-insensitive function name handling."""
        test_cases = [
            ("LEN(text)", "text.length"),
            ("Trim(text)", "text.trim()"),
            ("UPPER(text)", "text.toUpperCase()"),
            ("IsNull(var)", "var == null"),
        ]

        for pb_expr, expected in test_cases:
            result = self.converter.convert_expression(pb_expr)
            assert expected in result

    def test_empty_expression(self):
        """Test handling of empty expressions."""
        assert self.converter.convert_expression("") == ""
        assert self.converter.convert_expression(None) == ""

    def test_mid_function_conversion(self):
        """Test MID function conversion to substring."""
        # MID function needs special handling as it uses 1-based indexing
        pb_expr = "mid(text, 5, 3)"
        result = self.converter._convert_functions(pb_expr)
        assert "_substring" in result or "substring" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
