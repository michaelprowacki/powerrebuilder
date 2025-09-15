"""Comprehensive tests for ASTConverter."""

from unittest.mock import Mock

import pytest

from src.generate.converters.utils.ast import ASTConverter
from src.model.ast import ASTAssignment as Assignment
from src.model.ast import (
    BinaryExpression,
    Block,
    Event,
    Field,
    Function,
    Identifier,
    IfStatement,
    IntegerLiteral,
    Parameter,
    ReturnStatement,
    StringLiteral,
    Structure,
    Type,
    Variable,
)
from src.model.ui import Control, UserObject, Window


class TestASTConverter:
    """Test AST converter functionality."""

    def setup_method(self):
        """Set up test dependencies."""
        self.converter = ASTConverter()
        # Mock the sub-converters
        self.converter.type_converter = Mock()
        self.converter.expression_converter = Mock()
        self.converter.ui_converter = Mock()
        self.converter.event_converter = Mock()
        self.converter.datawindow_converter = Mock()

    def test_convert_window_basic(self):
        """Test converting a basic window definition."""
        # Create a mock window AST
        window_ast = Mock(spec=Window)
        window_ast.name = "w_test"
        window_ast.properties = {"title": "Test Window", "width": 800, "height": 600}
        window_ast.variables = [
            Variable("instance_var", Type("string")),
        ]
        window_ast.controls = [
            Control("button", "btn_ok", {"x": 10, "y": 10}),
        ]
        window_ast.events = [
            Event("clicked", [], Block([])),
        ]
        window_ast.methods = []

        # Set up mocks
        self.converter.type_converter.convert_type.return_value = "String"
        self.converter.ui_converter.convert_control.return_value = {
            "type": "button",
            "dart_name": "btnOk",
            "widget": "ElevatedButton",
            "properties": {"x": 10, "y": 10},
        }
        self.converter.event_converter.convert_event.return_value = Mock(
            name="clicked",
            parameters=[],
            body=["// Event handler"],
            dart_return_type="void",
            is_async=False,
        )

        # Convert
        result = self.converter.convert_window(window_ast)

        # Verify
        assert result.name == "WTest"
        assert result.properties["title"] == "Test Window"
        assert len(result.variables) == 1
        assert result.variables[0].name == "instanceVar"
        assert result.variables[0].dart_type == "String"
        assert len(result.controls) == 1
        assert result.controls[0]["dart_name"] == "btnOk"
        assert len(result.events) == 1

    def test_convert_user_object_stateful(self):
        """Test converting a user object to stateful widget."""
        # Create mock user object
        uo_ast = Mock(spec=UserObject)
        uo_ast.name = "uo_custom"
        uo_ast.variables = [
            Variable("counter", Type("integer")),
        ]
        uo_ast.controls = []
        uo_ast.events = [
            Event("timer", [], Block([])),
        ]
        uo_ast.methods = []

        # Set up mocks
        self.converter.type_converter.convert_type.return_value = "int"
        self.converter.event_converter.convert_event.return_value = Mock(
            name="timer",
            parameters=[],
            body=["// Timer event"],
            dart_return_type="void",
            is_async=False,
        )

        # Convert
        result = self.converter.convert_user_object(uo_ast)

        # Verify
        assert result.name == "UoCustom"
        assert len(result.variables) == 1
        assert result.variables[0].dart_type == "int"

    def test_convert_structure(self):
        """Test converting a structure definition."""
        # Create mock structure
        struct_ast = Mock(spec=Structure)
        struct_ast.name = "str_person"
        struct_ast.fields = [
            Field("name", Type("string")),
            Field("age", Type("integer")),
            Field("active", Type("boolean")),
        ]

        # Set up mocks
        self.converter.type_converter.convert_type.side_effect = [
            "String",
            "int",
            "bool",
        ]

        # Convert
        result = self.converter.convert_structure(struct_ast)

        # Verify
        assert result.name == "Person"
        assert len(result.fields) == 3
        assert result.fields[0].name == "name"
        assert result.fields[0].dart_type == "String"
        assert result.fields[1].name == "age"
        assert result.fields[1].dart_type == "int"
        assert result.fields[2].name == "active"
        assert result.fields[2].dart_type == "bool"

    def test_convert_function(self):
        """Test converting a function definition."""
        # Create mock function
        func_ast = Mock(spec=Function)
        func_ast.name = "calculate_total"
        func_ast.return_type = Type("decimal")
        func_ast.parameters = [
            Parameter("price", Type("decimal")),
            Parameter("quantity", Type("integer")),
        ]
        func_ast.body = Block(
            [
                Assignment(
                    Identifier("total"),
                    BinaryExpression(Identifier("price"), "*", Identifier("quantity")),
                ),
                ReturnStatement(Identifier("total")),
            ]
        )

        # Set up mocks
        self.converter.type_converter.convert_type.side_effect = [
            "double",
            "double",
            "int",
        ]
        self.converter.expression_converter.convert_expression.side_effect = [
            "price * quantity",
        ]

        # Convert
        result = self.converter.convert_function(func_ast)

        # Verify
        assert result.name == "calculateTotal"
        assert result.dart_return_type == "double"
        assert len(result.parameters) == 2
        assert result.parameters[0].name == "price"
        assert result.parameters[0].dart_type == "double"
        assert result.parameters[1].name == "quantity"
        assert result.parameters[1].dart_type == "int"

    def test_convert_datawindow(self):
        """Test converting a DataWindow definition."""
        # Mock DataWindow syntax
        dw_syntax = "release 12.5; datawindow(units=0 timer_interval=0)"
        dw_name = "dw_employee"

        # Set up mock
        mock_dw_def = Mock()
        mock_dw_def.name = "DwEmployee"
        mock_dw_def.columns = []
        mock_dw_def.sql = "SELECT * FROM employee"
        mock_dw_def.presentation_style = "grid"
        mock_dw_def.row_type = "Employee"

        self.converter.datawindow_converter.convert_datawindow.return_value = (
            mock_dw_def
        )

        # Convert
        result = self.converter.convert_datawindow(dw_syntax, dw_name)

        # Verify
        assert result.name == "DwEmployee"
        assert result.sql == "SELECT * FROM employee"
        self.converter.datawindow_converter.convert_datawindow.assert_called_once_with(
            dw_syntax,
            dw_name,
        )

    def test_convert_method_with_body(self):
        """Test converting a method with implementation."""
        # Create mock method
        method = Mock()
        method.name = "update_display"
        method.return_type = Type("void")
        method.parameters = []
        method.body = Block(
            [
                Assignment(Identifier("text"), StringLiteral("Updated")),
            ]
        )
        method.access_modifier = "public"

        # Set up mocks
        self.converter.type_converter.convert_type.return_value = "void"
        statements = ["text = 'Updated';"]
        self.converter._convert_method_body = Mock(return_value=statements)

        # Convert
        result = self.converter._convert_method(method)

        # Verify
        assert result.name == "updateDisplay"
        assert result.dart_return_type == "void"
        assert result.body == statements
        assert not result.is_async

    def test_name_conversion(self):
        """Test PowerBuilder to Dart name conversion."""
        # Test various name formats
        assert self.converter._to_camel_case("my_variable") == "myVariable"
        assert self.converter._to_camel_case("is_valid") == "isValid"
        assert self.converter._to_camel_case("simple") == "simple"

        assert self.converter._to_pascal_case("w_main_window") == "WMainWindow"
        assert self.converter._to_pascal_case("uo_custom") == "UoCustom"
        assert self.converter._to_pascal_case("str_data") == "StrData"

    def test_convert_control_flow(self):
        """Test converting control flow statements."""
        # Create mock if statement
        if_stmt = Mock(spec=IfStatement)
        if_stmt.condition = BinaryExpression(Identifier("x"), ">", IntegerLiteral(0))
        if_stmt.then_branch = Block(
            [
                Assignment(Identifier("result"), StringLiteral("positive")),
            ]
        )
        if_stmt.else_branch = None

        # Set up mocks
        self.converter.expression_converter.convert_expression.return_value = "x > 0"

        # Convert method body with if statement
        statements = [if_stmt]
        result = self.converter._convert_method_body(statements)

        # Should delegate to expression converter
        assert isinstance(result, list)

    def test_convert_empty_window(self):
        """Test converting window with no controls or events."""
        # Create minimal window
        window_ast = Mock(spec=Window)
        window_ast.name = "w_empty"
        window_ast.properties = {}
        window_ast.variables = []
        window_ast.controls = []
        window_ast.events = []
        window_ast.methods = []

        # Convert
        result = self.converter.convert_window(window_ast)

        # Verify
        assert result.name == "WEmpty"
        assert result.variables == []
        assert result.controls == []
        assert result.events == []
        assert result.methods == []

    def test_is_async_detection(self):
        """Test async method detection."""
        # Test various async patterns
        assert self.converter._is_async_method(["await getData();"])
        assert self.converter._is_async_method(["var result = await api.call();"])
        assert self.converter._is_async_method(
            ["Future.delayed(Duration(seconds: 1));"]
        )
        assert not self.converter._is_async_method(["print('hello');"])
        assert not self.converter._is_async_method([])

    def test_extract_datawindows(self):
        """Test extracting DataWindow references from controls."""
        controls = [
            {"type": "datawindow", "dart_name": "dwEmployee"},
            {"type": "button", "dart_name": "btnSave"},
            {"type": "datawindow", "dart_name": "dwDepartment"},
        ]

        result = self.converter._extract_datawindows(controls)

        assert result == ["dwEmployee", "dwDepartment"]

    def test_convert_with_inheritance(self):
        """Test converting object with inheritance."""
        # Create user object with parent
        uo_ast = Mock(spec=UserObject)
        uo_ast.name = "uo_derived"
        uo_ast.parent = "uo_base"
        uo_ast.variables = []
        uo_ast.controls = []
        uo_ast.events = []
        uo_ast.methods = []

        # Convert
        result = self.converter.convert_user_object(uo_ast)

        # Verify parent handling
        assert result.name == "UoDerived"
        # Parent should be handled in template generation

    def test_error_handling(self):
        """Test error handling in conversion."""
        # Test with None input
        with pytest.raises(AttributeError):
            self.converter.convert_window(None)

        # Test with missing required attributes
        incomplete_window = Mock()
        incomplete_window.name = "w_test"
        # Missing other required attributes

        with pytest.raises(AttributeError):
            self.converter.convert_window(incomplete_window)
