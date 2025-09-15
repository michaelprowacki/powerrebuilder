#!/usr/bin/env python3
"""Comprehensive test suite for Generate converters."""

from src.generate.converters.flutter.datawindows import DataWindowConverter
from src.generate.converters.flutter.events import EventConverter
from src.generate.converters.flutter.models import TypeConverter
from src.generate.converters.flutter.widgets import UIConverter
from src.generate.converters.utils.ast import ASTConverter
from src.generate.converters.utils.expressions import ExpressionConverter
from src.model import PBDataWindow
from src.model.ast import (
    ArrayAccess,
    ASTAssignment,
    BinaryExpression,
    Block,
    BooleanLiteral,
    CaseStatement,
    Event,
    ForLoop,
    FunctionDefinition,
    IfStatement,
    IntegerLiteral,
    Parameter,
    ReturnStatement,
    StringLiteral,
    Type,
    Variable,
)
from src.model.ast.functions import Signature
from src.model.ast.nodes.declarations import TypeCategory
from src.model.ui import Control, Window


class TestTypeConverter:
    """Test PowerBuilder to Dart type conversion."""

    def test_basic_type_conversion(self):
        """Test conversion of basic types."""
        converter = TypeConverter()

        test_cases = [
            (Type(name="integer", category=TypeCategory.NUMERIC), "int"),
            (Type(name="long", category=TypeCategory.NUMERIC), "int"),
            (Type(name="string", category=TypeCategory.TEXT), "String"),
            (Type(name="boolean", category=TypeCategory.LOGICAL), "bool"),
            (Type(name="real", category=TypeCategory.NUMERIC), "double"),
            (Type(name="decimal", category=TypeCategory.NUMERIC), "double"),
            (Type(name="date", category=TypeCategory.COMPOSITE), "DateTime"),
            (Type(name="time", category=TypeCategory.COMPOSITE), "DateTime"),
            (Type(name="datetime", category=TypeCategory.COMPOSITE), "DateTime"),
        ]

        for pb_type, expected_dart in test_cases:
            result = converter.convert_type(pb_type)
            assert result == expected_dart

    def test_array_type_conversion(self):
        """Test conversion of array types."""
        converter = TypeConverter()

        # Single dimensional array
        int_array = Type(name="integer", category=TypeCategory.NUMERIC, is_array=True)
        result = converter.convert_type(int_array)
        assert result == "List<int>"

        # String array
        string_array = Type(name="string", category=TypeCategory.TEXT, is_array=True)
        result = converter.convert_type(string_array)
        assert result == "List<String>"

    def test_custom_type_conversion(self):
        """Test conversion of custom types."""
        converter = TypeConverter()

        # Custom type should remain as-is
        custom_type = Type(name="n_custom_object", category=TypeCategory.CUSTOM)
        result = converter.convert_type(custom_type)
        assert result == "NCustomObject"  # Should convert to PascalCase

    def test_nullable_type_conversion(self):
        """Test conversion of nullable types."""
        converter = TypeConverter()

        int_type = Type(name="integer", category=TypeCategory.NUMERIC)
        result = converter.convert_type(int_type, nullable=True)
        assert result == "int?"

        string_type = Type(name="string", category=TypeCategory.TEXT)
        result = converter.convert_type(string_type, nullable=True)
        assert result == "String?"


class TestExpressionConverter:
    """Test expression conversion to Dart."""

    def test_literal_conversion(self):
        """Test conversion of literal values."""
        converter = ExpressionConverter()

        # Integer literal
        int_lit = IntegerLiteral(value=42)
        assert converter.convert_expression(int_lit) == "42"

        # String literal
        str_lit = StringLiteral(value="Hello World")
        assert converter.convert_expression(str_lit) == '"Hello World"'

        # Boolean literals
        true_lit = BooleanLiteral(value=True)
        assert converter.convert_expression(true_lit) == "true"

        false_lit = BooleanLiteral(value=False)
        assert converter.convert_expression(false_lit) == "false"

    def test_variable_conversion(self):
        """Test conversion of variable references."""
        converter = ExpressionConverter()

        var = Variable(name="li_count")
        assert converter.convert_expression(var) == "liCount"  # camelCase conversion

        var_with_prefix = Variable(name="this.width")
        assert converter.convert_expression(var_with_prefix) == "this.width"

    def test_binary_expression_conversion(self):
        """Test conversion of binary expressions."""
        converter = ExpressionConverter()

        # Arithmetic expression
        expr = BinaryExpression(
            left=Variable(name="a"),
            operator="+",
            right=IntegerLiteral(value=10),
        )
        assert converter.convert_expression(expr) == "a + 10"

        # Comparison expression
        comp = BinaryExpression(
            left=Variable(name="count"),
            operator=">",
            right=IntegerLiteral(value=0),
        )
        assert converter.convert_expression(comp) == "count > 0"

        # PowerBuilder specific operators
        pb_and = BinaryExpression(
            left=Variable(name="a"),
            operator="and",
            right=Variable(name="b"),
        )
        assert converter.convert_expression(pb_and) == "a && b"

        pb_or = BinaryExpression(
            left=Variable(name="x"),
            operator="or",
            right=Variable(name="y"),
        )
        assert converter.convert_expression(pb_or) == "x || y"

    def test_array_access_conversion(self):
        """Test conversion of array access."""
        converter = ExpressionConverter()

        arr_access = ArrayAccess(
            array_name="items",
            indices=[0],
        )
        assert converter.convert_expression(arr_access) == "items[0]"

        # Multi-dimensional array
        multi_arr = ArrayAccess(
            array_name="matrix",
            indices=["i", "j"],
        )
        assert converter.convert_expression(multi_arr) == "matrix[i][j]"


class TestEventConverter:
    """Test event conversion to Dart."""

    def test_simple_event_conversion(self):
        """Test conversion of simple events."""
        converter = EventConverter()

        # Button click event
        result = converter.convert_event(
            event_name="clicked",
            parameters=[],
            body=["return 0;"],
        )
        # Result is a Method object
        assert hasattr(result, "name")
        assert "onPressed" in result.name or result.is_event
        assert "return 0;" in result.body

    def test_event_with_parameters(self):
        """Test conversion of events with parameters."""
        converter = EventConverter()

        # Custom event with parameters
        result = converter.convert_event(
            event_name="itemchanged",
            parameters=[
                "int row",
                "DwObject dwo",
            ],
            body=[],
        )
        # Result is a Method object
        assert hasattr(result, "name")
        assert "onItemChanged" in result.name or result.is_event
        assert hasattr(result, "parameters")

    def test_event_mapping(self):
        """Test PowerBuilder to Flutter event mapping."""
        converter = EventConverter()

        # Test that common events get converted to proper handler methods
        result = converter.convert_event("clicked", [], [])
        assert hasattr(result, "name")
        assert "_clickedHandler" in result.name  # Method name uses handler pattern
        assert result.is_event == True

        result = converter.convert_event("doubleclicked", [], [])
        assert hasattr(result, "name")
        assert "_doubleclickedHandler" in result.name
        assert result.is_event == True

        result = converter.convert_event("getfocus", [], [])
        assert hasattr(result, "name")
        assert "_getfocusHandler" in result.name
        assert result.is_event == True

        result = converter.convert_event("modified", [], [])
        assert hasattr(result, "name")
        assert "_modifiedHandler" in result.name
        assert result.is_event == True


class TestUIConverter:
    """Test UI control conversion."""

    def test_button_conversion(self):
        """Test button conversion to Flutter."""
        converter = UIConverter()

        button = Control(
            name="cb_ok",
            type="commandbutton",
            position=(10, 20),
            size=(100, 30),
            properties={
                "text": "OK",
                "enabled": "true",
                "visible": "true",
            },
        )

        result = converter.convert_control(button.type, button.name, button.properties)
        assert isinstance(result, dict)
        assert result["widget"] == "ElevatedButton"
        assert result["name"] == "cb_ok"
        assert result["dart_name"] == "ok"  # cb_ prefix is removed
        assert (
            "_buttonText" in result["flutter_properties"]
        )  # text property is mapped to _buttonText

    def test_textbox_conversion(self):
        """Test textbox conversion to Flutter."""
        converter = UIConverter()

        textbox = Control(
            name="sle_name",
            type="edit",
            position=(10, 50),
            size=(200, 25),
            properties={
                "text": "",
                "enabled": "true",
                "visible": "true",
                "maxlength": "50",  # Note: should be lowercase to match the mapping
            },
        )

        result = converter.convert_control(
            textbox.type, textbox.name, textbox.properties
        )
        assert isinstance(result, dict)
        assert result["widget"] == "TextField"
        assert result["requires_controller"] == True
        assert result["controller_type"] == "TextEditingController"
        assert "maxLength" in result["flutter_properties"]

    def test_combobox_conversion(self):
        """Test combobox conversion to Flutter."""
        converter = UIConverter()

        # Check if combobox is in the control map
        assert "combobox" in converter.control_map
        combo_mapping = converter.control_map["combobox"]
        assert combo_mapping["widget"] == "Autocomplete"

    def test_window_widget_generation(self):
        """Test widget tree generation for multiple controls."""
        converter = UIConverter()

        # Create controls that would be in a window
        controls = [
            {
                "type": "commandbutton",
                "name": "cb_ok",
                "widget": "ElevatedButton",
                "dart_name": "cbOk",
                "properties": {"text": "OK"},
                "flutter_properties": {},
                "is_container": False,
            },
        ]

        # Test that we can generate widget tree
        result = converter.generate_widget_tree(controls)
        assert "ElevatedButton" in result
        assert "Column" in result  # Default layout


class TestDataWindowConverter:
    """Test DataWindow conversion."""

    def test_datawindow_to_datagrid(self):
        """Test DataWindow to DataGrid conversion."""
        converter = DataWindowConverter()

        datawindow = PBDataWindow(
            name="d_employee",
            sql_select="SELECT emp_id, emp_name FROM employee",
            columns=[
                {"name": "emp_id", "type": "integer", "label": "ID"},
                {"name": "emp_name", "type": "string", "label": "Name"},
            ],
        )

        result = converter.convert_datawindow(datawindow)
        assert "DataTable" in result
        assert "columns: [" in result
        assert 'DataColumn(label: Text("ID"))' in result
        assert 'DataColumn(label: Text("Name"))' in result
        assert "rows:" in result

    def test_datawindow_with_computed_fields(self):
        """Test DataWindow with computed fields."""
        converter = DataWindowConverter()

        datawindow = PBDataWindow(
            name="d_sales",
            columns=[
                {"name": "quantity", "type": "integer"},
                {"name": "price", "type": "decimal"},
                {"name": "total", "type": "decimal", "computed": "quantity * price"},
            ],
        )

        result = converter.convert_datawindow(datawindow)
        # Should handle computed fields
        assert "DataColumn" in result


class TestASTConverter:
    """Test full AST conversion."""

    def test_function_conversion(self):
        """Test function definition conversion."""
        converter = ASTConverter()

        func = FunctionDefinition(
            signature=Signature(
                name="calculate_total",
                return_type=Type(name="decimal", category=TypeCategory.NUMERIC),
                parameters=[
                    Parameter(
                        name="quantity",
                        type=Type(name="integer", category=TypeCategory.NUMERIC),
                    ),
                    Parameter(
                        name="price",
                        type=Type(name="decimal", category=TypeCategory.NUMERIC),
                    ),
                ],
            ),
            body=Block(
                statements=[
                    ReturnStatement(
                        value=BinaryExpression(
                            left=Variable(name="quantity"),
                            operator="*",
                            right=Variable(name="price"),
                        ),
                    ),
                ]
            ),
        )

        result = converter.convert_function(func)
        assert "double calculateTotal(int quantity, double price)" in result
        assert "return quantity * price;" in result

    def test_if_statement_conversion(self):
        """Test if statement conversion."""
        converter = ASTConverter()

        if_stmt = IfStatement(
            condition=BinaryExpression(
                left=Variable(name="count"),
                operator=">",
                right=IntegerLiteral(value=0),
            ),
            then_branch=Block(
                statements=[
                    ASTAssignment(
                        target=Variable(name="result"),
                        value=StringLiteral(value="Found"),
                    ),
                ]
            ),
            else_branch=Block(
                statements=[
                    ASTAssignment(
                        target=Variable(name="result"),
                        value=StringLiteral(value="Not found"),
                    ),
                ]
            ),
        )

        result = converter.convert_statement(if_stmt)
        assert "if (count > 0)" in result
        assert 'result = "Found";' in result
        assert "else" in result
        assert 'result = "Not found";' in result

    def test_for_loop_conversion(self):
        """Test for loop conversion."""
        converter = ASTConverter()

        for_loop = ForLoop(
            variable="i",
            start=IntegerLiteral(value=1),
            end=IntegerLiteral(value=10),
            step=IntegerLiteral(value=1),
            body=Block(statements=[]),
        )

        result = converter.convert_statement(for_loop)
        assert "for (int i = 1; i <= 10; i++)" in result

    def test_case_statement_conversion(self):
        """Test case statement conversion."""
        converter = ASTConverter()

        case_stmt = CaseStatement(
            expression=Variable(name="status"),
            cases=[
                (StringLiteral(value="A"), Block(statements=[])),
                (StringLiteral(value="B"), Block(statements=[])),
            ],
            default_body=Block(statements=[]),
        )

        result = converter.convert_statement(case_stmt)
        assert "switch (status)" in result
        assert 'case "A":' in result
        assert 'case "B":' in result
        assert "default:" in result


class TestConverterIntegration:
    """Test converter integration scenarios."""

    def test_full_window_conversion(self):
        """Test converting a complete window with controls and events."""
        ui_converter = UIConverter()
        event_converter = EventConverter()

        # Create a window with button and click event
        window = Window(
            name="w_login",
            title="Login",
            width=400,
            height=300,
            controls=[
                Control(
                    name="sle_username",
                    type="edit",
                    position=(50, 50),
                    size=(200, 25),
                    properties={},
                ),
                Control(
                    name="sle_password",
                    type="edit",
                    position=(50, 100),
                    size=(200, 25),
                    properties={"password": "true"},
                ),
                Control(
                    name="cb_login",
                    type="button",
                    position=(50, 150),
                    size=(100, 30),
                    properties={"text": "Login"},
                ),
            ],
            events=[
                Event(
                    name="cb_login_clicked",
                    parameters=[],
                    body=Block(statements=[]),
                ),
            ],
        )

        result = ui_converter.convert_window(window)
        assert "WLoginScreen" in result
        assert "TextField" in result  # Username and password fields
        assert "ElevatedButton" in result  # Login button

    def test_datawindow_integration(self):
        """Test DataWindow with full conversion."""
        dw_converter = DataWindowConverter()

        datawindow = PBDataWindow(
            name="d_customer_list",
            sql_select="SELECT id, name, email, status FROM customers",
            columns=[
                {"name": "id", "type": "integer", "label": "ID"},
                {"name": "name", "type": "string", "label": "Customer Name"},
                {"name": "email", "type": "string", "label": "Email"},
                {"name": "status", "type": "string", "label": "Status"},
            ],
            retrieve_args=["status_filter"],
        )

        result = dw_converter.convert_datawindow(datawindow)
        assert "DataTable" in result
        assert "Customer Name" in result
        assert len([line for line in result.split("\n") if "DataColumn" in line]) == 4
