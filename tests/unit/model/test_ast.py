"""Comprehensive tests for AST nodes and expression evaluation.

This file consolidates AST-related tests from:
- test_ast_nodes.py
- test_expression_evaluator.py
- test_expression_evaluator_fixed.py
"""

from dataclasses import fields, is_dataclass

import pytest

from src.model.ast import (
    ArrayType,
    AssignmentStatement,
    BasicType,
    BinaryExpression,
    # Additional nodes
    Block,
    CustomType,
    # Events
    Event,
    EventTrigger,
    # Expressions
    FunctionDeclaration,
    IfStatement,
    Literal,
    NodeKind,
    Parameter,
    # Base nodes
    PBNode,
    ReturnStatement,
    # Statements
    UnaryExpression,
    # Declarations
    VariableDeclaration,
)
from src.model.expression_evaluator import (
    EvaluationContext,
    EvaluationError,
    evaluate_arithmetic,
    evaluate_comparison,
    evaluate_expression,
    evaluate_function_call,
    evaluate_logical,
    evaluate_unary_expression,
)
from src.model.unified_expressions import (
    ArithmeticOperator,
    ArrayAccessExpression,
    AttributeAccessExpression,
    BooleanExpression,
    CastExpression,
    ComparisonOperator,
    FunctionCallExpression,
    LogicalOperator,
    NullExpression,
    NumberExpression,
    ParenthesesExpression,
    # Expression types from consolidated module
    StringExpression,
    SuperExpression,
    ThisExpression,
    UnaryOperator,
    VariableExpression,
)
from src.model.unified_expressions import (
    ConditionalExpression as CondExpr,
)


class TestASTNodes:
    """Test AST node hierarchy and structure."""

    def test_pbnode_structure(self):
        """Test PBNode base class structure."""
        assert is_dataclass(PBNode)
        field_names = {f.name for f in fields(PBNode)}
        expected_fields = {"start_position", "stop_position", "source_file"}
        assert expected_fields.issubset(field_names)

    def test_node_creation(self):
        """Test creating various AST nodes."""
        # Base node
        node = PBNode(start_position=0, stop_position=10, source_file="test.pb")
        assert node.start_position == 0
        assert node.stop_position == 10
        assert node.source_file == "test.pb"

    def test_node_kind_enum(self):
        """Test NodeKind enumeration."""
        assert NodeKind.EXPRESSION
        assert NodeKind.STATEMENT
        assert NodeKind.DECLARATION
        assert NodeKind.TYPE
        assert NodeKind.EVENT
        assert NodeKind.BLOCK

    def test_expression_hierarchy(self):
        """Test expression node hierarchy."""
        # Literal
        lit = Literal(value=42, type_name="integer")
        assert lit.value == 42
        assert lit.type_name == "integer"

        # Binary expression
        left = Literal(value=10, type_name="integer")
        right = Literal(value=5, type_name="integer")
        binary = BinaryExpression(
            left=left, operator="+", right=right, type_name="integer"
        )
        assert binary.operator == "+"
        assert binary.left.value == 10
        assert binary.right.value == 5

        # Unary expression
        unary = UnaryExpression(operator="-", operand=lit, type_name="integer")
        assert unary.operator == "-"
        assert unary.operand.value == 42

    def test_statement_hierarchy(self):
        """Test statement node hierarchy."""
        # Assignment
        var = VariableExpression(name="x")
        val = Literal(value=10, type_name="integer")
        assign = AssignmentStatement(target=var, value=val)
        assert assign.target.name == "x"
        assert assign.value.value == 10

        # If statement
        cond = BooleanExpression(value=True)
        then_block = Block(statements=[assign])
        if_stmt = IfStatement(condition=cond, then_block=then_block, else_block=None)
        assert if_stmt.condition.value is True
        assert len(if_stmt.then_block.statements) == 1

        # Return statement
        ret = ReturnStatement(value=val)
        assert ret.value.value == 10

    def test_declaration_nodes(self):
        """Test declaration AST nodes."""
        # Variable declaration
        var_decl = VariableDeclaration(
            name="count",
            type_name="integer",
            initial_value=Literal(value=0, type_name="integer"),
            is_constant=False,
        )
        assert var_decl.name == "count"
        assert var_decl.type_name == "integer"
        assert not var_decl.is_constant

        # Function declaration
        param = Parameter(name="value", type_name="integer")
        body = Block(
            statements=[ReturnStatement(value=VariableExpression(name="value"))]
        )
        func_decl = FunctionDeclaration(
            name="identity",
            return_type="integer",
            parameters=[param],
            body=body,
            access_modifier="public",
        )
        assert func_decl.name == "identity"
        assert func_decl.return_type == "integer"
        assert len(func_decl.parameters) == 1

    def test_event_nodes(self):
        """Test event AST nodes."""
        # Event trigger
        trigger = EventTrigger(event_name="clicked", target="cb_ok")
        assert trigger.event_name == "clicked"
        assert trigger.target == "cb_ok"

        # Event declaration
        event = Event(
            name="ue_process",
            return_type="integer",
            parameters=[],
            body=Block(statements=[]),
            trigger_type="user",
            extends="pbm_custom01",
        )
        assert event.name == "ue_process"
        assert event.trigger_type == "user"

    def test_type_nodes(self):
        """Test type AST nodes."""
        # Basic type
        basic = BasicType(name="string")
        assert basic.name == "string"

        # Array type
        array = ArrayType(element_type="integer", dimensions=[10, 20])
        assert array.element_type == "integer"
        assert array.dimensions == [10, 20]

        # Custom type
        custom = CustomType(name="n_custom", base_type="nonvisualobject", members={})
        assert custom.name == "n_custom"
        assert custom.base_type == "nonvisualobject"


class TestExpressionEvaluator:
    """Test expression evaluation functionality."""

    def test_evaluation_context(self):
        """Test evaluation context creation and usage."""
        context = EvaluationContext()

        # Set and get variables
        context.set_variable("x", 10)
        context.set_variable("name", "test")

        assert context.get_variable("x") == 10
        assert context.get_variable("name") == "test"

        # Non-existent variable
        with pytest.raises(EvaluationError):
            context.get_variable("undefined")

    def test_literal_evaluation(self):
        """Test evaluation of literal expressions."""
        context = EvaluationContext()

        # Number
        num_expr = NumberExpression(value=42)
        assert evaluate_expression(num_expr, context) == 42

        # String
        str_expr = StringExpression(value="hello")
        assert evaluate_expression(str_expr, context) == "hello"

        # Boolean
        bool_expr = BooleanExpression(value=True)
        assert evaluate_expression(bool_expr, context) is True

        # Null
        null_expr = NullExpression()
        assert evaluate_expression(null_expr, context) is None

    def test_variable_evaluation(self):
        """Test evaluation of variable expressions."""
        context = EvaluationContext()
        context.set_variable("count", 5)
        context.set_variable("name", "PowerBuilder")

        # Simple variable
        var1 = VariableExpression(name="count")
        assert evaluate_expression(var1, context) == 5

        var2 = VariableExpression(name="name")
        assert evaluate_expression(var2, context) == "PowerBuilder"

        # Undefined variable
        var3 = VariableExpression(name="undefined")
        with pytest.raises(EvaluationError):
            evaluate_expression(var3, context)

    def test_arithmetic_evaluation(self):
        """Test evaluation of arithmetic expressions."""
        context = EvaluationContext()

        # Addition
        add = BinaryExpression(
            left=NumberExpression(value=10),
            operator=ArithmeticOperator.ADD,
            right=NumberExpression(value=5),
        )
        assert evaluate_arithmetic(add, context) == 15

        # Subtraction
        sub = BinaryExpression(
            left=NumberExpression(value=10),
            operator=ArithmeticOperator.SUBTRACT,
            right=NumberExpression(value=3),
        )
        assert evaluate_arithmetic(sub, context) == 7

        # Multiplication
        mul = BinaryExpression(
            left=NumberExpression(value=4),
            operator=ArithmeticOperator.MULTIPLY,
            right=NumberExpression(value=7),
        )
        assert evaluate_arithmetic(mul, context) == 28

        # Division
        div = BinaryExpression(
            left=NumberExpression(value=20),
            operator=ArithmeticOperator.DIVIDE,
            right=NumberExpression(value=4),
        )
        assert evaluate_arithmetic(div, context) == 5

        # Division by zero
        div_zero = BinaryExpression(
            left=NumberExpression(value=10),
            operator=ArithmeticOperator.DIVIDE,
            right=NumberExpression(value=0),
        )
        with pytest.raises(EvaluationError):
            evaluate_arithmetic(div_zero, context)

    def test_comparison_evaluation(self):
        """Test evaluation of comparison expressions."""
        context = EvaluationContext()

        # Equal
        eq = BinaryExpression(
            left=NumberExpression(value=5),
            operator=ComparisonOperator.EQUAL,
            right=NumberExpression(value=5),
        )
        assert evaluate_comparison(eq, context) is True

        # Not equal
        ne = BinaryExpression(
            left=NumberExpression(value=5),
            operator=ComparisonOperator.NOT_EQUAL,
            right=NumberExpression(value=10),
        )
        assert evaluate_comparison(ne, context) is True

        # Less than
        lt = BinaryExpression(
            left=NumberExpression(value=3),
            operator=ComparisonOperator.LESS_THAN,
            right=NumberExpression(value=7),
        )
        assert evaluate_comparison(lt, context) is True

        # Greater than or equal
        gte = BinaryExpression(
            left=NumberExpression(value=10),
            operator=ComparisonOperator.GREATER_EQUAL,
            right=NumberExpression(value=10),
        )
        assert evaluate_comparison(gte, context) is True

    def test_logical_evaluation(self):
        """Test evaluation of logical expressions."""
        context = EvaluationContext()

        # AND
        and_expr = BinaryExpression(
            left=BooleanExpression(value=True),
            operator=LogicalOperator.AND,
            right=BooleanExpression(value=False),
        )
        assert evaluate_logical(and_expr, context) is False

        # OR
        or_expr = BinaryExpression(
            left=BooleanExpression(value=True),
            operator=LogicalOperator.OR,
            right=BooleanExpression(value=False),
        )
        assert evaluate_logical(or_expr, context) is True

        # NOT
        not_expr = UnaryExpression(
            operator=UnaryOperator.NOT, operand=BooleanExpression(value=True)
        )
        assert evaluate_unary_expression(not_expr, context) is False

    def test_complex_expression_evaluation(self):
        """Test evaluation of complex nested expressions."""
        context = EvaluationContext()
        context.set_variable("x", 10)
        context.set_variable("y", 5)

        # (x + 5) * (y - 2)
        expr = BinaryExpression(
            left=BinaryExpression(
                left=VariableExpression(name="x"),
                operator=ArithmeticOperator.ADD,
                right=NumberExpression(value=5),
            ),
            operator=ArithmeticOperator.MULTIPLY,
            right=BinaryExpression(
                left=VariableExpression(name="y"),
                operator=ArithmeticOperator.SUBTRACT,
                right=NumberExpression(value=2),
            ),
        )
        # (10 + 5) * (5 - 2) = 15 * 3 = 45
        assert evaluate_expression(expr, context) == 45

    def test_conditional_expression_evaluation(self):
        """Test evaluation of conditional (ternary) expressions."""
        context = EvaluationContext()
        context.set_variable("score", 85)

        # score > 80 ? "Pass" : "Fail"
        cond = CondExpr(
            condition=BinaryExpression(
                left=VariableExpression(name="score"),
                operator=ComparisonOperator.GREATER_THAN,
                right=NumberExpression(value=80),
            ),
            true_expr=StringExpression(value="Pass"),
            false_expr=StringExpression(value="Fail"),
        )
        assert evaluate_expression(cond, context) == "Pass"

        # Change score and re-evaluate
        context.set_variable("score", 75)
        assert evaluate_expression(cond, context) == "Fail"

    def test_function_call_evaluation(self):
        """Test evaluation of function call expressions."""
        context = EvaluationContext()

        # Register some built-in functions
        context.register_function("abs", lambda x: abs(x))
        context.register_function("max", lambda a, b: max(a, b))
        context.register_function("len", lambda s: len(s))

        # abs(-10)
        abs_call = FunctionCallExpression(
            name="abs", arguments=[NumberExpression(value=-10)]
        )
        assert evaluate_function_call(abs_call, context) == 10

        # max(5, 10)
        max_call = FunctionCallExpression(
            name="max",
            arguments=[NumberExpression(value=5), NumberExpression(value=10)],
        )
        assert evaluate_function_call(max_call, context) == 10

        # len("hello")
        len_call = FunctionCallExpression(
            name="len", arguments=[StringExpression(value="hello")]
        )
        assert evaluate_function_call(len_call, context) == 5

    def test_attribute_access_evaluation(self):
        """Test evaluation of attribute access expressions."""
        context = EvaluationContext()

        # Create an object with attributes
        obj = {"name": "Test Object", "value": 42, "active": True}
        context.set_variable("obj", obj)

        # obj.name
        attr1 = AttributeAccessExpression(
            object=VariableExpression(name="obj"), attribute="name"
        )
        assert evaluate_expression(attr1, context) == "Test Object"

        # obj.value
        attr2 = AttributeAccessExpression(
            object=VariableExpression(name="obj"), attribute="value"
        )
        assert evaluate_expression(attr2, context) == 42

    def test_array_access_evaluation(self):
        """Test evaluation of array access expressions."""
        context = EvaluationContext()

        # Create an array
        arr = [10, 20, 30, 40, 50]
        context.set_variable("numbers", arr)

        # numbers[0]
        access1 = ArrayAccessExpression(
            array=VariableExpression(name="numbers"), index=NumberExpression(value=0)
        )
        assert evaluate_expression(access1, context) == 10

        # numbers[2]
        access2 = ArrayAccessExpression(
            array=VariableExpression(name="numbers"), index=NumberExpression(value=2)
        )
        assert evaluate_expression(access2, context) == 30

        # Out of bounds
        access3 = ArrayAccessExpression(
            array=VariableExpression(name="numbers"), index=NumberExpression(value=10)
        )
        with pytest.raises(EvaluationError):
            evaluate_expression(access3, context)

    def test_type_casting_evaluation(self):
        """Test evaluation of type casting expressions."""
        context = EvaluationContext()

        # Cast string to integer
        cast1 = CastExpression(
            expression=StringExpression(value="123"), target_type="integer"
        )
        assert evaluate_expression(cast1, context) == 123

        # Cast float to integer
        cast2 = CastExpression(
            expression=NumberExpression(value=3.14), target_type="integer"
        )
        assert evaluate_expression(cast2, context) == 3

        # Cast integer to string
        cast3 = CastExpression(
            expression=NumberExpression(value=42), target_type="string"
        )
        assert evaluate_expression(cast3, context) == "42"

    def test_special_expressions(self):
        """Test evaluation of special expressions."""
        context = EvaluationContext()
        context.set_this({"id": 100, "name": "Current Object"})
        context.set_super({"base_value": 50})

        # this
        this = ThisExpression()
        result = evaluate_expression(this, context)
        assert result["id"] == 100
        assert result["name"] == "Current Object"

        # super
        super_expr = SuperExpression()
        result = evaluate_expression(super_expr, context)
        assert result["base_value"] == 50

        # Parentheses
        paren = ParenthesesExpression(
            expression=BinaryExpression(
                left=NumberExpression(value=2),
                operator=ArithmeticOperator.ADD,
                right=NumberExpression(value=3),
            )
        )
        assert evaluate_expression(paren, context) == 5


# Test fixtures
@pytest.fixture
def sample_context():
    """Provide a sample evaluation context."""
    context = EvaluationContext()
    context.set_variable("x", 10)
    context.set_variable("y", 20)
    context.set_variable("name", "test")
    context.set_variable("items", [1, 2, 3, 4, 5])
    context.set_variable("user", {"id": 1, "name": "John", "active": True})

    # Register some functions
    context.register_function("abs", lambda x: abs(x))
    context.register_function("min", lambda a, b: min(a, b))
    context.register_function("max", lambda a, b: max(a, b))
    context.register_function("len", lambda x: len(x))

    return context


@pytest.fixture
def sample_expressions():
    """Provide sample expressions for testing."""
    return {
        "number": NumberExpression(value=42),
        "string": StringExpression(value="hello"),
        "boolean": BooleanExpression(value=True),
        "null": NullExpression(),
        "variable": VariableExpression(name="x"),
        "add": BinaryExpression(
            left=NumberExpression(value=10),
            operator=ArithmeticOperator.ADD,
            right=NumberExpression(value=5),
        ),
        "compare": BinaryExpression(
            left=VariableExpression(name="x"),
            operator=ComparisonOperator.GREATER_THAN,
            right=NumberExpression(value=5),
        ),
    }
