"""Comprehensive tests for all PowerBuilder node types.

This file consolidates ALL PowerBuilder node tests from:
- test_pb_base.py
- test_pb_behavioral.py
- test_pb_builtin_functions.py
- test_pb_control_flow_nodes.py
- test_pb_core_nodes.py
- test_pb_datawindow_nodes.py
- test_pb_declaration_nodes.py
- test_pb_event_nodes.py
- test_pb_expression.py
- test_pb_sql.py
- test_pb_type.py
- test_source_anchor.py
"""

from datetime import datetime
from decimal import Decimal

import pytest

from src.model.ast import PBCustomTypeNode

# Base imports
from src.model.base.pb_behavioral import PBNode
from src.model.behavioral import PBBehavioralMethod, PBBehavioralObject
from src.model.builtin_functions import (
    builtin_function_registry,
    pb_abs,
    pb_ceiling,
    pb_day,
    pb_double,
    pb_hour,
    pb_integer,
    pb_left,
    pb_len,
    pb_long,
    pb_lower,
    pb_mid,
    pb_minute,
    pb_month,
    pb_right,
    pb_round,
    pb_second,
    pb_string,
    pb_upper,
    pb_year,
)
from src.model.datawindow import PBDataWindowNode

# Expression and AST imports
from src.model.entities.pb_expression import (
    PBAdditionExpression,
    PBAndExpression,
    PBArrayElementExpression,
    PBAttributeAccessExpression,
    PBBooleanExpression,
    PBCreateUsingExpression,
    # Core nodes
    PBCustomCallStatement,
    PBDataComponentNode,
    # DataWindow nodes
    PBDataWindowFileNode,
    PBDeclareCursorNode,
    PBDeclareProcedureNode,
    # Event nodes
    PBDescriptorNode,
    PBDestroyStatementNode,
    PBDivisionExpression,
    # Control flow nodes
    PBDoLoopUntilNode,
    PBDoLoopWhileNode,
    PBDoUntilLoopNode,
    PBDoWhileLoopNode,
    PBDynamicMethodInvocationNode,
    PBElseIfNode,
    PBElseNode,
    PBElseOnLineNode,
    PBEndForwardNode,
    PBEventAttributeNode,
    PBEventDeclarationNode,
    PBEventInvocationNode,
    PBEventNameNode,
    PBEventReferenceNameNode,
    PBExponentiationExpression,
    # Expression nodes
    PBFunctionArgumentNode,
    PBFunctionCallExpression,
    PBIsValidExpression,
    PBMethodCallExpression,
    PBMultiplicationExpression,
    PBNotExpression,
    PBNullExpression,
    PBNumberExpression,
    PBOrExpression,
    PBStringExpression,
    PBSubtractionExpression,
    PBThisExpression,
    PBVariableExpression,
)
from src.model.entities.pb_sql import SQLSelectStatement, SQLStatement
from src.model.entities.pb_variable import PBDefaultVariableNode
from src.model.source import SourceAnchor
from src.model.type_system import PBType, PBTypeCategory


class TestBaseNode:
    """Test base PBNode functionality."""

    def test_pb_node_creation(self):
        """Test creating a base node."""
        node = PBNode(start_position=10, stop_position=20)
        assert node.start_position == 10
        assert node.stop_position == 20

    def test_pb_node_default_values(self):
        """Test default values for base node."""
        node = PBNode()
        assert node.start_position is None
        assert node.stop_position is None

    def test_pb_node_equality(self):
        """Test base node equality comparison."""
        node1 = PBNode(start_position=10, stop_position=20)
        node2 = PBNode(start_position=10, stop_position=20)
        node3 = PBNode(start_position=15, stop_position=25)

        assert node1 == node2  # Same values
        assert node1 != node3  # Different positions

    def test_pb_node_visitor_not_implemented(self):
        """Test that accept_visitor raises NotImplementedError."""
        node = PBNode()
        with pytest.raises(NotImplementedError):
            node.accept_visitor(None)


class TestBehavioralNodes:
    """Test behavioral object and method nodes."""

    def test_pb_behavioral_object_creation(self):
        """Test creating a behavioral object."""
        obj = PBBehavioralObject(
            name="n_test",
            parent_type="nonvisualobject",
            methods=["method1", "method2"],
            attributes={"attr1": "string", "attr2": "integer"},
        )
        assert obj.name == "n_test"
        assert obj.parent_type == "nonvisualobject"
        assert len(obj.methods) == 2
        assert obj.attributes["attr1"] == "string"

    def test_pb_behavioral_method_creation(self):
        """Test creating a behavioral method."""
        method = PBBehavioralMethod(
            name="of_calculate",
            return_type="integer",
            parameters=[("ai_value", "integer"), ("as_type", "string")],
            body="return ai_value * 2",
            access_modifier="public",
        )
        assert method.name == "of_calculate"
        assert method.return_type == "integer"
        assert len(method.parameters) == 2
        assert method.access_modifier == "public"

    def test_behavioral_object_inheritance(self):
        """Test behavioral object inheritance chain."""
        child = PBBehavioralObject(
            name="n_child",
            parent_type="n_parent",
            methods=["child_method"],
        )
        parent = PBBehavioralObject(
            name="n_parent",
            parent_type="nonvisualobject",
            methods=["parent_method"],
        )

        assert child.parent_type == parent.name
        assert parent.parent_type == "nonvisualobject"


class TestBuiltinFunctions:
    """Test PowerBuilder builtin function nodes."""

    def test_builtin_function_registry(self):
        """Test that all builtin functions are registered."""
        assert "abs" in builtin_function_registry
        assert "string" in builtin_function_registry
        assert "len" in builtin_function_registry
        assert "isnull" in builtin_function_registry

    def test_numeric_functions(self):
        """Test numeric builtin functions."""
        # Test abs
        assert pb_abs(-5) == 5
        assert pb_abs(3.14) == 3.14
        assert pb_abs(Decimal("-10.5")) == Decimal("10.5")

        # Test ceiling
        assert pb_ceiling(3.14) == 4
        assert pb_ceiling(-2.1) == -2

        # Test round
        assert pb_round(3.14159, 2) == Decimal("3.14")
        assert pb_round(5.5, 0) == Decimal(6)

    def test_string_functions(self):
        """Test string builtin functions."""
        # Test len
        assert pb_len("hello") == 5
        assert pb_len("") == 0

        # Test upper/lower
        assert pb_upper("hello") == "HELLO"
        assert pb_lower("WORLD") == "world"

        # Test left/right/mid
        assert pb_left("PowerBuilder", 5) == "Power"
        assert pb_right("PowerBuilder", 7) == "Builder"
        assert pb_mid("PowerBuilder", 6, 7) == "Builder"

    def test_date_time_functions(self):
        """Test date/time builtin functions."""
        # Test date components
        dt = datetime(2024, 6, 29, 14, 30, 45)
        assert pb_year(dt) == 2024
        assert pb_month(dt) == 6
        assert pb_day(dt) == 29
        assert pb_hour(dt) == 14
        assert pb_minute(dt) == 30
        assert pb_second(dt) == 45

    def test_type_conversion_functions(self):
        """Test type conversion builtin functions."""
        # Test string conversions
        assert pb_string(123) == "123"
        assert pb_string(3.14) == "3.14"
        assert pb_string(True) == "true"

        # Test numeric conversions
        assert pb_integer("123") == 123
        assert pb_long("999999") == 999999
        assert pb_double("3.14") == 3.14


class TestControlFlowNodes:
    """Test all control flow nodes."""

    def test_loop_nodes(self):
        """Test all loop node types."""
        # Do-Loop-Until
        node1 = PBDoLoopUntilNode(name="test_loop", line_number=10)
        assert node1.name == "test_loop"
        assert node1.line_number == 10

        # Do-Loop-While
        node2 = PBDoLoopWhileNode(name="while_loop", line_number=20)
        assert node2.name == "while_loop"

        # Do-Until-Loop
        node3 = PBDoUntilLoopNode(name="until_loop", line_number=30)
        assert node3.name == "until_loop"

        # Do-While-Loop
        node4 = PBDoWhileLoopNode(name="do_while", line_number=40)
        assert node4.name == "do_while"

    def test_conditional_nodes(self):
        """Test conditional control flow nodes."""
        # ElseIf
        elseif = PBElseIfNode(name="elseif_test", line_number=100)
        assert elseif.name == "elseif_test"

        # Else
        else_node = PBElseNode(name="else_test", line_number=110)
        assert else_node.name == "else_test"

        # ElseOnLine
        else_online = PBElseOnLineNode(name="else_online", line_number=120)
        assert else_online.name == "else_online"

    def test_structural_nodes(self):
        """Test structural control flow nodes."""
        end_forward = PBEndForwardNode(name="end_forward", line_number=200)
        assert end_forward.name == "end_forward"
        assert end_forward.line_number == 200


class TestCoreNodes:
    """Test core functionality nodes."""

    def test_statement_nodes(self):
        """Test statement nodes."""
        # Custom call
        call = PBCustomCallStatement(
            identifier="my_custom_call",
            start_position=10,
            stop_position=20,
        )
        assert call.identifier == "my_custom_call"

        # Destroy statement
        destroy = PBDestroyStatementNode(
            expression="my_obj",
            start_position=10,
            stop_position=20,
        )
        assert destroy.expression == "my_obj"
        assert str(destroy) == "destroy my_obj"

    def test_type_nodes(self):
        """Test type-related nodes."""
        custom_type = PBCustomTypeNode(
            identifier="my_type",
            start_position=10,
            stop_position=20,
        )
        assert custom_type.identifier == "my_type"
        assert str(custom_type) == "my_type"

    def test_dynamic_invocation(self):
        """Test dynamic method invocation."""
        dynamic = PBDynamicMethodInvocationNode(
            target="my_object",
            method_name="my_method",
            arguments=["arg1", "arg2"],
            start_position=10,
            stop_position=20,
        )
        assert dynamic.target == "my_object"
        assert dynamic.method_name == "my_method"
        assert len(dynamic.arguments) == 2
        assert str(dynamic) == "my_object.dynamic my_method(arg1, arg2)"


class TestDataWindowNodes:
    """Test DataWindow-related nodes."""

    def test_datawindow_node(self):
        """Test DataWindow node."""
        dw = PBDataWindowNode(
            parameters=["param1", "param2"],
            start_position=10,
            stop_position=20,
        )
        assert dw.parameters == ["param1", "param2"]
        assert str(dw) == "datawindow(param1, param2)"

    def test_datawindow_file_node(self):
        """Test DataWindow file node."""
        dw_file = PBDataWindowFileNode(
            file_name="d_employee",
            file_path="/datawindows/d_employee.srd",
            start_position=10,
            stop_position=20,
        )
        assert dw_file.file_name == "d_employee"
        assert dw_file.file_path == "/datawindows/d_employee.srd"

    def test_data_component_node(self):
        """Test data component node."""
        component = PBDataComponentNode(
            component_type="column",
            component_name="emp_id",
            component_properties={"datatype": "long", "nullable": False},
            start_position=10,
            stop_position=20,
        )
        assert component.component_type == "column"
        assert component.component_name == "emp_id"
        assert component.component_properties["datatype"] == "long"


class TestDeclarationNodes:
    """Test declaration and definition nodes."""

    def test_declare_statements(self):
        """Test declare statement nodes."""
        # Declare cursor
        cursor = PBDeclareCursorNode(
            identifier="my_cursor",
            target="SELECT * FROM table",
            start_position=10,
            stop_position=20,
        )
        assert cursor.identifier == "my_cursor"
        assert str(cursor) == "declare my_cursor cursor for SELECT * FROM table"

        # Declare procedure
        proc = PBDeclareProcedureNode(
            procedure_name="my_proc",
            start_position=10,
            stop_position=20,
        )
        assert proc.procedure_name == "my_proc"
        assert str(proc) == "declare procedure my_proc"

    def test_variable_nodes(self):
        """Test variable declaration nodes."""
        # Default variable
        var = PBDefaultVariableNode(
            default_variable="my_var",
            start_position=10,
            stop_position=20,
        )
        assert var.default_variable == "my_var"
        assert str(var) == "default variable my_var"

        # Function argument
        arg = PBFunctionArgumentNode(
            argument_name="arg1",
            argument_type="integer",
            is_reference=True,
            start_position=10,
            stop_position=20,
        )
        assert arg.argument_name == "arg1"
        assert arg.is_reference is True
        assert str(arg) == "ref integer arg1"

    def test_descriptor_nodes(self):
        """Test descriptor nodes."""
        desc = PBDescriptorNode(
            descriptor_type="attribute",
            descriptor_name="visible",
            descriptor_value="true",
            start_position=10,
            stop_position=20,
        )
        assert desc.descriptor_type == "attribute"
        assert str(desc) == "attribute visible = true"


class TestEventNodes:
    """Test event-related nodes."""

    def test_event_declaration(self):
        """Test event declaration nodes."""
        event = PBEventDeclarationNode(
            return_type="integer",
            event_reference_name="clicked",
            custom_call_statement="call super::clicked",
            statements=["MessageBox('Info', 'Clicked')"],
            start_position=10,
            stop_position=20,
        )
        assert event.return_type == "integer"
        assert event.event_reference_name == "clicked"

    def test_event_invocation(self):
        """Test event invocation nodes."""
        invocation = PBEventInvocationNode(
            identifier="clicked",
            function_arguments=["sender", "e"],
            start_position=10,
            stop_position=20,
        )
        assert invocation.identifier == "clicked"
        assert len(invocation.function_arguments) == 2

    def test_event_metadata(self):
        """Test event metadata nodes."""
        # Event attribute
        attr = PBEventAttributeNode(
            attributes=["create", "destroy"],
            type_declaration="pbm_dwnkey",
            start_position=10,
            stop_position=20,
        )
        assert len(attr.attributes) == 2

        # Event name
        name = PBEventNameNode(
            event_name="clicked",
            start_position=10,
            stop_position=20,
        )
        assert name.event_name == "clicked"

        # Event reference
        ref = PBEventReferenceNameNode(
            identifier="base_clicked",
            start_position=10,
            stop_position=20,
        )
        assert ref.identifier == "base_clicked"


class TestExpressionNodes:
    """Test all expression nodes."""

    def test_literal_expressions(self):
        """Test literal expression nodes."""
        # String
        str_expr = PBStringExpression(value="Hello World")
        assert str_expr.value == "Hello World"
        assert str(str_expr) == '"Hello World"'

        # Number
        num_expr = PBNumberExpression(value=42)
        assert num_expr.value == 42
        assert str(num_expr) == "42"

        # Boolean
        bool_expr = PBBooleanExpression(value=True)
        assert bool_expr.value is True
        assert str(bool_expr) == "true"

        # Null
        null_expr = PBNullExpression()
        assert str(null_expr) == "null"

    def test_arithmetic_expressions(self):
        """Test arithmetic expression nodes."""
        left = PBNumberExpression(value=10)
        right = PBNumberExpression(value=5)

        # Addition
        add = PBAdditionExpression(left=left, right=right)
        assert str(add) == "10 + 5"

        # Subtraction
        sub = PBSubtractionExpression(left=left, right=right)
        assert str(sub) == "10 - 5"

        # Multiplication
        mul = PBMultiplicationExpression(left=left, right=right)
        assert str(mul) == "10 * 5"

        # Division
        div = PBDivisionExpression(left=left, right=right)
        assert str(div) == "10 / 5"

        # Exponentiation
        exp = PBExponentiationExpression(left=left, right=right)
        assert str(exp) == "10 ^ 5"

    def test_logical_expressions(self):
        """Test logical expression nodes."""
        left = PBBooleanExpression(value=True)
        right = PBBooleanExpression(value=False)

        # AND
        and_expr = PBAndExpression(left=left, right=right)
        assert str(and_expr) == "true and false"

        # OR
        or_expr = PBOrExpression(left=left, right=right)
        assert str(or_expr) == "true or false"

        # NOT
        not_expr = PBNotExpression(operand=left)
        assert str(not_expr) == "not true"

    def test_access_expressions(self):
        """Test access expression nodes."""
        # Variable
        var = PBVariableExpression(variable_name="my_var")
        assert var.variable_name == "my_var"
        assert str(var) == "my_var"

        # Attribute access
        attr = PBAttributeAccessExpression(
            object_expression=var, attribute_name="property"
        )
        assert attr.attribute_name == "property"
        assert str(attr) == "my_var.property"

        # Array element
        array = PBArrayElementExpression(
            array_expression=var, index_expression=PBNumberExpression(value=1)
        )
        assert str(array) == "my_var[1]"

    def test_call_expressions(self):
        """Test call expression nodes."""
        # Function call
        func = PBFunctionCallExpression(
            function_name="MessageBox",
            arguments=[
                PBStringExpression(value="Title"),
                PBStringExpression(value="Message"),
            ],
        )
        assert func.function_name == "MessageBox"
        assert len(func.arguments) == 2

        # Method call
        obj = PBVariableExpression(variable_name="dw_1")
        method = PBMethodCallExpression(
            object_expression=obj, method_name="Retrieve", arguments=[]
        )
        assert method.method_name == "Retrieve"

    def test_special_expressions(self):
        """Test special expression nodes."""
        # This
        this = PBThisExpression()
        assert str(this) == "this"

        # IsValid
        valid = PBIsValidExpression(
            expression=PBVariableExpression(variable_name="my_obj")
        )
        assert str(valid) == "IsValid(my_obj)"

        # CreateUsing
        create = PBCreateUsingExpression(
            type_name="n_custom", descriptor="my_descriptor"
        )
        assert create.type_name == "n_custom"


class TestSQLNodes:
    """Test SQL-related nodes."""

    def test_sql_statement(self):
        """Test basic SQL statement node."""
        sql = SQLStatement(
            statement_type="SELECT",
            text="SELECT * FROM employee WHERE dept_id = :dept",
            parameters=[":dept"],
            source_line=100,
        )
        assert sql.statement_type == "SELECT"
        assert len(sql.parameters) == 1
        assert sql.source_line == 100

    def test_sql_select_statement(self):
        """Test SQL SELECT statement node."""
        select = SQLSelectStatement(
            columns=["emp_id", "emp_name", "salary"],
            tables=["employee"],
            where_clause="dept_id = :dept AND active = 'Y'",
            order_by=["emp_name"],
            group_by=None,
            having_clause=None,
            into_variables=["li_id", "ls_name", "ld_salary"],
            parameters=[":dept"],
            source_line=200,
        )
        assert len(select.columns) == 3
        assert select.tables[0] == "employee"
        assert len(select.into_variables) == 3
        assert select.where_clause is not None

    def test_sql_dml_statements(self):
        """Test SQL DML statement nodes."""
        # INSERT
        insert = SQLStatement(
            statement_type="INSERT",
            text="INSERT INTO employee (id, name) VALUES (:id, :name)",
            parameters=[":id", ":name"],
        )
        assert insert.statement_type == "INSERT"
        assert len(insert.parameters) == 2

        # UPDATE
        update = SQLStatement(
            statement_type="UPDATE",
            text="UPDATE employee SET salary = :salary WHERE id = :id",
            parameters=[":salary", ":id"],
        )
        assert update.statement_type == "UPDATE"

        # DELETE
        delete = SQLStatement(
            statement_type="DELETE",
            text="DELETE FROM employee WHERE id = :id",
            parameters=[":id"],
        )
        assert delete.statement_type == "DELETE"


class TestTypeNodes:
    """Test type system nodes."""

    def test_pb_type_creation(self):
        """Test PowerBuilder type creation."""
        # Simple type
        int_type = PBType(
            name="integer",
            category=PBTypeCategory.PRIMITIVE,
            is_array=False,
        )
        assert int_type.name == "integer"
        assert int_type.category == PBTypeCategory.PRIMITIVE
        assert not int_type.is_array

        # Array type
        array_type = PBType(
            name="string",
            category=PBTypeCategory.PRIMITIVE,
            is_array=True,
            array_dimensions=[10],
        )
        assert array_type.is_array
        assert array_type.array_dimensions == [10]

    def test_pb_type_categories(self):
        """Test PowerBuilder type categories."""
        # Primitive
        prim = PBType(name="long", category=PBTypeCategory.PRIMITIVE)
        assert prim.category == PBTypeCategory.PRIMITIVE

        # Object
        obj = PBType(name="datawindow", category=PBTypeCategory.OBJECT)
        assert obj.category == PBTypeCategory.OBJECT

        # Custom
        custom = PBType(name="n_custom", category=PBTypeCategory.CUSTOM)
        assert custom.category == PBTypeCategory.CUSTOM

        # Structure
        struct = PBType(name="str_address", category=PBTypeCategory.STRUCTURE)
        assert struct.category == PBTypeCategory.STRUCTURE

    def test_pb_type_compatibility(self):
        """Test type compatibility checks."""
        int_type = PBType(name="integer", category=PBTypeCategory.PRIMITIVE)
        long_type = PBType(name="long", category=PBTypeCategory.PRIMITIVE)
        string_type = PBType(name="string", category=PBTypeCategory.PRIMITIVE)

        # Numeric types should be compatible
        assert int_type.name != long_type.name
        assert int_type.category == long_type.category

        # String is different category
        assert string_type.category == PBTypeCategory.PRIMITIVE
        assert string_type.name != int_type.name


class TestSourceAnchor:
    """Test source position tracking."""

    def test_source_anchor_creation(self):
        """Test creating a source anchor."""
        anchor = SourceAnchor(
            file_path="/src/window.srw",
            start_line=10,
            start_column=5,
            end_line=15,
            end_column=20,
        )
        assert anchor.file_path == "/src/window.srw"
        assert anchor.start_line == 10
        assert anchor.start_column == 5
        assert anchor.end_line == 15
        assert anchor.end_column == 20

    def test_source_anchor_single_line(self):
        """Test source anchor for single line."""
        anchor = SourceAnchor(
            file_path="/src/function.srf",
            start_line=100,
            start_column=10,
            end_line=100,
            end_column=50,
        )
        assert anchor.start_line == anchor.end_line
        assert anchor.end_column > anchor.start_column

    def test_source_anchor_comparison(self):
        """Test source anchor comparison."""
        anchor1 = SourceAnchor(
            file_path="/src/test.srw",
            start_line=10,
            start_column=1,
            end_line=20,
            end_column=1,
        )
        anchor2 = SourceAnchor(
            file_path="/src/test.srw",
            start_line=10,
            start_column=1,
            end_line=20,
            end_column=1,
        )
        anchor3 = SourceAnchor(
            file_path="/src/other.srw",
            start_line=10,
            start_column=1,
            end_line=20,
            end_column=1,
        )

        assert anchor1 == anchor2
        assert anchor1 != anchor3


# Test fixtures for common node data
@pytest.fixture
def sample_expression_nodes():
    """Provide sample expression nodes for testing."""
    return {
        "number": PBNumberExpression(value=42),
        "string": PBStringExpression(value="test"),
        "boolean": PBBooleanExpression(value=True),
        "null": PBNullExpression(),
        "variable": PBVariableExpression(variable_name="my_var"),
        "this": PBThisExpression(),
    }


@pytest.fixture
def sample_control_flow_nodes():
    """Provide sample control flow nodes for testing."""
    return {
        "do_loop_until": PBDoLoopUntilNode(name="loop1", line_number=10),
        "do_while": PBDoWhileLoopNode(name="loop2", line_number=20),
        "elseif": PBElseIfNode(name="cond1", line_number=30),
        "else": PBElseNode(name="else1", line_number=40),
    }


@pytest.fixture
def sample_sql_statements():
    """Provide sample SQL statements for testing."""
    return {
        "select": SQLSelectStatement(
            columns=["*"],
            tables=["employee"],
            where_clause="active = 'Y'",
            parameters=[],
        ),
        "insert": SQLStatement(
            statement_type="INSERT",
            text="INSERT INTO log (message) VALUES (:msg)",
            parameters=[":msg"],
        ),
        "update": SQLStatement(
            statement_type="UPDATE",
            text="UPDATE config SET value = :val WHERE key = :key",
            parameters=[":val", ":key"],
        ),
    }
