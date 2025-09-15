"""Test suite for EventConverter."""

import pytest

from src.generate.converters.flutter.events import EventConverter
from src.generate.converters.flutter.models import TypeConverter
from src.generate.converters.utils.expressions import ExpressionConverter


class TestEventConverter:
    """Test cases for PowerBuilder to Flutter event conversion."""

    def setup_method(self):
        """Set up test instances."""
        self.type_converter = TypeConverter()
        self.expression_converter = ExpressionConverter(self.type_converter)
        self.converter = EventConverter(self.type_converter, self.expression_converter)

    def test_initialization(self):
        """Test converter initialization."""
        assert self.converter is not None
        assert self.converter.type_converter is not None
        assert self.converter.expression_converter is not None
        assert len(self.converter.event_map) > 0

    def test_event_map_structure(self):
        """Test that event map has expected structure."""
        # Check common events
        assert "open" in self.converter.event_map
        assert "close" in self.converter.event_map
        assert "clicked" in self.converter.event_map
        assert "modified" in self.converter.event_map

        # Check event properties
        open_event = self.converter.event_map["open"]
        assert "flutter_method" in open_event
        assert open_event["flutter_method"] == "initState"
        assert open_event["lifecycle"] is True

        clicked_event = self.converter.event_map["clicked"]
        assert clicked_event["flutter_method"] == "onPressed"
        assert clicked_event["callback"] is True

    def test_lifecycle_event_conversion(self):
        """Test conversion of lifecycle events."""
        # Test open event
        body = ["open(w_main)", "this.title = 'My App'"]
        result = self.converter.convert_event("open", [], body)

        assert result is not None
        assert result.name == "initState"
        assert result.return_type == "void"
        assert result.is_event is True
        assert "super.initState();" in result.body

        # Test close event
        body = ["disconnect;", "// Cleanup"]
        result = self.converter.convert_event("close", [], body)

        assert result.name == "dispose"
        assert "super.dispose();" in result.body

    def test_callback_event_conversion(self):
        """Test conversion of callback events."""
        # Test clicked event
        body = ["messagebox('Info', 'Button clicked')"]
        result = self.converter.convert_event("clicked", [], body, "btn_save")

        assert result is not None
        assert result.name == "_btnSaveClickedHandler"
        assert result.return_type == "void"
        assert result.is_event is True
        assert any("showDialog" in line for line in result.body)

    def test_event_with_return_value(self):
        """Test events that return values."""
        # Test closequery event
        body = ["if unsaved_changes then", "return 1", "else", "return 0", "end if"]
        result = self.converter.convert_event("closequery", [], body)

        assert result is not None
        assert result.return_type == "bool"
        assert any("return false;" in line for line in result.body)  # 1 mapped to false
        assert any("return true;" in line for line in result.body)  # 0 mapped to true

    def test_event_with_parameters(self):
        """Test events with parameters."""
        # Test modified event (ValueChanged<String>)
        body = ["current_value = value"]
        result = self.converter.convert_event("modified", [], body)

        assert result is not None
        assert len(result.parameters) == 1
        assert result.parameters[0].name == "value"
        assert result.parameters[0].dart_type == "String"

    def test_datawindow_events(self):
        """Test DataWindow-specific events."""
        # Test itemchanged event
        body = ["if column = 'amount' then", "return 0", "end if"]
        result = self.converter.convert_event("itemchanged", [], body)

        assert result is not None
        assert len(result.parameters) == 3  # row, column, value

        # Test itemerror event with return mapping
        body = ["return 0"]  # Reject with message
        result = self.converter.convert_event("itemerror", [], body)

        assert result.return_type == "int"
        assert any("ValidationAction.reject.index" in line for line in result.body)

    def test_async_event_detection(self):
        """Test detection of async events."""
        # Event with await
        body = ["await fetchData()", "return true"]
        result = self.converter.convert_event("updatestart", [], body)

        assert result.is_async is True
        assert result.return_type == "Future<bool>"

    def test_event_widget_wrapper(self):
        """Test getting widget wrapper for events."""
        assert (
            self.converter.get_event_widget_wrapper("doubleclicked")
            == "GestureDetector"
        )
        assert self.converter.get_event_widget_wrapper("resize") == "LayoutBuilder"
        assert self.converter.get_event_widget_wrapper("timer") == "Timer.periodic"
        assert self.converter.get_event_widget_wrapper("clicked") is None

    def test_event_registration(self):
        """Test event registration code generation."""
        # Simple callback
        reg = self.converter.get_event_registration("clicked", "_onButtonClick")
        assert reg == "onPressed: _onButtonClick"

        # ValueChanged callback
        reg = self.converter.get_event_registration("modified", "_onTextChange")
        assert reg == "onChanged: (value) => _onTextChange(value)"

        # Complex callback
        reg = self.converter.get_event_registration("itemerror", "_onItemError")
        assert (
            "onValidationError: (row, col, val, err) => _onItemError(row, col, val, err)"
            in reg
        )

    def test_messagebox_conversion(self):
        """Test MessageBox conversion to Flutter dialog."""
        statement = "messagebox('Error', 'Invalid input')"
        result = self.converter._convert_messagebox(statement)

        assert "showDialog" in result
        assert "AlertDialog" in result
        assert "Error" in result
        assert "Invalid input" in result

    def test_messagebox_with_variables(self):
        """Test MessageBox with variable parameters."""
        statement = "messagebox(ls_title, ls_message)"
        result = self.converter._convert_messagebox(statement)

        assert "Text(ls_title.toString())" in result
        assert "Text(ls_message.toString())" in result

    def test_return_statement_conversion(self):
        """Test return statement conversion."""
        # Test boolean returns
        assert "return true;" in self.converter._convert_return_statement(
            "return true", "bool"
        )
        assert "return false;" in self.converter._convert_return_statement(
            "return false", "bool"
        )
        assert "return true;" in self.converter._convert_return_statement(
            "return 1", "bool"
        )
        assert "return false;" in self.converter._convert_return_statement(
            "return 0", "bool"
        )

        # Test numeric returns with mapping
        mapping = {0: "Action.continue.index", 1: "Action.stop.index"}
        result = self.converter._convert_return_statement("return 0", "int", mapping)
        assert "return Action.continue.index;" in result

        # Test empty return
        assert "return;" in self.converter._convert_return_statement("return", "void")

    def test_if_statement_conversion(self):
        """Test IF statement conversion."""
        # Simple if
        result = self.converter._convert_if_statement("IF x > 0 THEN")
        assert result == "if (x > 0) {"

        # If with complex condition
        result = self.converter._convert_if_statement(
            "IF IsNull(value) AND count > 0 THEN"
        )
        assert "if (" in result
        assert "== null" in result
        assert "&&" in result

        # Elseif
        result = self.converter._convert_if_statement("ELSEIF y < 10 THEN")
        assert result == "} else if (y < 10) {"

        # End if
        result = self.converter._convert_if_statement("END IF")
        assert result == "}"

    def test_assignment_conversion(self):
        """Test assignment statement conversion."""
        # Simple assignment
        result = self.converter._convert_assignment_statement("x = 10")
        assert result == "x = 10;"

        # Property assignment
        result = self.converter._convert_assignment_statement("this.title = 'Hello'")
        assert "setState(" in result
        assert "this.title = 'Hello'" in result

        # Array assignment
        result = self.converter._convert_assignment_statement("data[1] = 100")
        assert "data[0] = 100" in result  # 1-based to 0-based

    def test_method_call_conversion(self):
        """Test method call conversion."""
        # Simple method call
        result = self.converter._convert_method_call("save_data()")
        assert result == "saveData();"

        # Method with parameters
        result = self.converter._convert_method_call("set_value(10, 'test')")
        assert "setValue(10, 'test');" in result

        # Object method call
        result = self.converter._convert_method_call("dw_1.retrieve()")
        assert "dw1.retrieve();" in result

    def test_system_function_conversion(self):
        """Test system function conversions."""
        # Sleep
        result = self.converter._convert_sleep("sleep(5)")
        assert "await Future.delayed(Duration(seconds: 5));" in result

        # SetNull
        result = self.converter._convert_setnull("setnull(myVar)")
        assert "myVar = null;" in result

        # IsNull
        result = self.converter._convert_isnull("isnull(employee.name)")
        assert "(employee.name == null)" in result

        # IsValid
        result = self.converter._convert_isvalid("isvalid(window)")
        assert "(window != null)" in result

    def test_object_reference_conversion(self):
        """Test object reference conversion."""
        assert self.converter._convert_object_reference("this") == "this"
        assert self.converter._convert_object_reference("parent") == "widget"
        assert self.converter._convert_object_reference("super") == "super"
        assert (
            self.converter._convert_object_reference("employee_data") == "employeeData"
        )

    def test_camel_case_conversion(self):
        """Test snake_case to camelCase conversion."""
        assert self.converter._to_camel_case("my_variable") == "myVariable"
        assert self.converter._to_camel_case("simple") == "simple"
        assert self.converter._to_camel_case("long_variable_name") == "longVariableName"

    def test_pascal_case_conversion(self):
        """Test snake_case to PascalCase conversion."""
        assert self.converter._to_pascal_case("my_class") == "MyClass"
        assert self.converter._to_pascal_case("simple") == "Simple"
        assert self.converter._to_pascal_case("window_main") == "WindowMain"

    def test_complex_condition_conversion(self):
        """Test complex condition conversion."""
        condition = "IsNull(data) OR count = 0 AND active <> false"
        result = self.converter._convert_complex_condition(condition)

        assert "== null" in result
        assert "||" in result
        assert "&&" in result
        assert "!=" in result

    def test_infer_return_type(self):
        """Test return type inference from body."""
        # Integer return
        body = ["return 1"]
        assert self.converter._infer_return_type(body) == "int"

        # Boolean return
        body = ["return true"]
        assert self.converter._infer_return_type(body) == "bool"

        # String return
        body = ["return 'hello'"]
        assert self.converter._infer_return_type(body) == "String"

        # Async return
        body = ["await loadData()", "return true"]
        assert self.converter._infer_return_type(body) == "Future<bool>"

    def test_needs_set_state(self):
        """Test setState requirement detection."""
        assert self.converter._needs_set_state("this.title") is True
        assert self.converter._needs_set_state("title") is True
        assert self.converter._needs_set_state("temp") is False
        assert self.converter._needs_set_state("i") is False
        assert self.converter._needs_set_state("_localVar") is False

    def test_event_enums(self):
        """Test generation of event-related enums."""
        enums = self.converter.get_event_enums()

        assert len(enums) > 0
        assert any("ValidationAction" in enum for enum in enums)
        assert any("ButtonAction" in enum for enum in enums)
        assert any("ErrorAction" in enum for enum in enums)
        assert any("SqlErrorAction" in enum for enum in enums)

    def test_split_parameters(self):
        """Test parameter splitting."""
        # Simple parameters
        params = self.converter._split_parameters("a, b, c")
        assert params == ["a", "b", "c"]

        # Parameters with nested function calls
        params = self.converter._split_parameters("getValue(), calculate(x, y), 'test'")
        assert len(params) == 3
        assert params[0] == "getValue()"
        assert params[1] == "calculate(x, y)"
        assert params[2] == "'test'"

    def test_convert_destroy(self):
        """Test destroy statement conversion."""
        result = self.converter._convert_destroy("destroy(myObject)")
        assert "myObject?.dispose();" in result
        assert "myObject = null;" in result

    def test_convert_close(self):
        """Test close statement conversion."""
        result = self.converter._convert_close("close(this)")
        assert "Navigator.of(context).pop();" in result

    def test_convert_open(self):
        """Test open statement conversion."""
        result = self.converter._convert_open("open(w_main)")
        assert "Navigator.of(context).push" in result
        assert "MaterialPageRoute" in result
        assert "WMain()" in result

    def test_convert_array_access(self):
        """Test array access conversion."""
        result = self.converter._convert_array_access(
            "data_array[row_index][col_index].value"
        )
        assert "dataArray" in result
        assert "[rowIndex]" in result
        assert "[colIndex]" in result
        assert ".value" in result

    def test_convert_type_cast(self):
        """Test type casting conversion."""
        # Integer cast
        result = self.converter._convert_type_cast("Integer(amount)")
        assert "int.parse(" in result
        assert ".toString())" in result

        # String cast
        result = self.converter._convert_type_cast("String(123)")
        assert ".toString()" in result

        # Boolean cast
        result = self.converter._convert_type_cast("Boolean(flag)")
        assert "!= 0)" in result

    def test_generic_handler_creation(self):
        """Test creation of generic event handlers."""
        body = ["// Custom logic", "doSomething()"]
        result = self.converter.convert_event("customEvent", [], body, "myControl")

        assert result is not None
        assert result.name == "_myControlCustomEventHandler"
        assert result.is_event is True

    def test_event_body_default_patterns(self):
        """Test default patterns for common events."""
        # Clicked event with empty body
        result = self.converter.convert_event("clicked", [], [])
        assert any("// Handle button click" in line for line in result.body)

        # Modified event with empty body
        result = self.converter.convert_event("modified", [], [])
        assert any("setState(" in line for line in result.body)

    def test_complex_return_conversion(self):
        """Test complex return statement conversion."""
        # IIF expression
        statement = "return IIF(IsValid(data), data.value, 'N/A')"
        result = self.converter._convert_complex_return(statement, "String")
        assert "?" in result
        assert ":" in result
        assert "!= null" in result

    def test_method_chain_conversion(self):
        """Test method chaining conversion."""
        expr = "Parent.GetWindow().GetFrame().GetData()"
        result = self.converter._convert_method_chain(expr)

        assert "widget" in result
        assert "getWindow()" in result
        assert "getFrame()" in result
        assert "getData()" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
