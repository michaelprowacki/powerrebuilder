"""Tests for expression optimizer."""

from src.decompile.analysis.data import ExpressionOptimizer
from src.model.unified_expressions import (
    PBBinaryOperator,
    PBBooleanLiteral,
    PBConcatenationOperator,
    PBNullLiteral,
    PBNumberLiteral,
    PBPowerOperator,
    PBStringLiteral,
    PBTernaryExpression,
    PBUnaryOperator,
    PBVariable,
)


class TestConstantFolding:
    """Test constant folding optimizations."""

    def test_fold_numeric_addition(self):
        """Test folding of numeric addition."""
        optimizer = ExpressionOptimizer()

        # 2 + 3 = 5
        expr = PBBinaryOperator(
            left=PBNumberLiteral(value=2),
            operator="+",
            right=PBNumberLiteral(value=3),
        )

        result = optimizer.optimize(expr)
        assert isinstance(result, PBNumberLiteral)
        assert result.value == 5
        assert optimizer.optimizations_applied == 1

    def test_fold_numeric_subtraction(self):
        """Test folding of numeric subtraction."""
        optimizer = ExpressionOptimizer()

        # 10 - 4 = 6
        expr = PBBinaryOperator(
            left=PBNumberLiteral(value=10),
            operator="-",
            right=PBNumberLiteral(value=4),
        )

        result = optimizer.optimize(expr)
        assert isinstance(result, PBNumberLiteral)
        assert result.value == 6

    def test_fold_numeric_multiplication(self):
        """Test folding of numeric multiplication."""
        optimizer = ExpressionOptimizer()

        # 3 * 4 = 12
        expr = PBBinaryOperator(
            left=PBNumberLiteral(value=3),
            operator="*",
            right=PBNumberLiteral(value=4),
        )

        result = optimizer.optimize(expr)
        assert isinstance(result, PBNumberLiteral)
        assert result.value == 12

    def test_fold_numeric_division(self):
        """Test folding of numeric division."""
        optimizer = ExpressionOptimizer()

        # 15 / 3 = 5
        expr = PBBinaryOperator(
            left=PBNumberLiteral(value=15),
            operator="/",
            right=PBNumberLiteral(value=3),
        )

        result = optimizer.optimize(expr)
        assert isinstance(result, PBNumberLiteral)
        assert result.value == 5

    def test_no_fold_division_by_zero(self):
        """Test that division by zero is not folded."""
        optimizer = ExpressionOptimizer()

        # 10 / 0 should not be folded
        expr = PBBinaryOperator(
            left=PBNumberLiteral(value=10),
            operator="/",
            right=PBNumberLiteral(value=0),
        )

        result = optimizer.optimize(expr)
        assert isinstance(result, PBBinaryOperator)
        assert optimizer.optimizations_applied == 0

    def test_fold_string_concatenation(self):
        """Test folding of string concatenation."""
        optimizer = ExpressionOptimizer()

        # "Hello" + " World" = "Hello World"
        expr = PBBinaryOperator(
            left=PBStringLiteral(value="Hello"),
            operator="+",
            right=PBStringLiteral(value=" World"),
        )

        result = optimizer.optimize(expr)
        assert isinstance(result, PBStringLiteral)
        assert result.value == "Hello World"

    def test_fold_concatenation_operator(self):
        """Test folding of concatenation operator."""
        optimizer = ExpressionOptimizer()

        # "A" + "B" + "C" = "ABC"
        expr = PBConcatenationOperator(
            operands=[
                PBStringLiteral(value="A"),
                PBStringLiteral(value="B"),
                PBStringLiteral(value="C"),
            ],
        )

        result = optimizer.optimize(expr)
        assert isinstance(result, PBStringLiteral)
        assert result.value == "ABC"

    def test_partial_concatenation_folding(self):
        """Test partial folding of concatenation with non-literals."""
        optimizer = ExpressionOptimizer()

        # "Hello " + var + " World" -> "Hello " + var + " World" (no change)
        # But "A" + "B" + var + "C" + "D" -> "AB" + var + "CD"
        expr = PBConcatenationOperator(
            operands=[
                PBStringLiteral(value="A"),
                PBStringLiteral(value="B"),
                PBVariable(name="var"),
                PBStringLiteral(value="C"),
                PBStringLiteral(value="D"),
            ],
        )

        result = optimizer.optimize(expr)
        assert isinstance(result, PBConcatenationOperator)
        assert len(result.operands) == 3
        assert result.operands[0].value == "AB"
        assert isinstance(result.operands[1], PBVariable)
        assert result.operands[2].value == "CD"

    def test_fold_boolean_operations(self):
        """Test folding of boolean operations."""
        optimizer = ExpressionOptimizer()

        # true AND false = false
        expr = PBBinaryOperator(
            left=PBBooleanLiteral(value=True),
            operator="AND",
            right=PBBooleanLiteral(value=False),
        )

        result = optimizer.optimize(expr)
        assert isinstance(result, PBBooleanLiteral)
        assert result.value is False

        # true OR false = true
        expr = PBBinaryOperator(
            left=PBBooleanLiteral(value=True),
            operator="OR",
            right=PBBooleanLiteral(value=False),
        )

        result = optimizer.optimize(expr)
        assert isinstance(result, PBBooleanLiteral)
        assert result.value is True

    def test_fold_comparison_operations(self):
        """Test folding of comparison operations."""
        optimizer = ExpressionOptimizer()

        # 5 > 3 = true
        expr = PBBinaryOperator(
            left=PBNumberLiteral(value=5),
            operator=">",
            right=PBNumberLiteral(value=3),
        )

        result = optimizer.optimize(expr)
        assert isinstance(result, PBBooleanLiteral)
        assert result.value is True

        # "abc" = "abc" = true
        expr = PBBinaryOperator(
            left=PBStringLiteral(value="abc"),
            operator="=",
            right=PBStringLiteral(value="abc"),
        )

        result = optimizer.optimize(expr)
        assert isinstance(result, PBBooleanLiteral)
        assert result.value is True

    def test_fold_unary_operations(self):
        """Test folding of unary operations."""
        optimizer = ExpressionOptimizer()

        # -5 = -5
        expr = PBUnaryOperator(
            operator="-",
            operand=PBNumberLiteral(value=5),
        )

        result = optimizer.optimize(expr)
        assert isinstance(result, PBNumberLiteral)
        assert result.value == -5

        # NOT true = false
        expr = PBUnaryOperator(
            operator="NOT",
            operand=PBBooleanLiteral(value=True),
        )

        result = optimizer.optimize(expr)
        assert isinstance(result, PBBooleanLiteral)
        assert result.value is False

    def test_fold_power_operation(self):
        """Test folding of power operations."""
        optimizer = ExpressionOptimizer()

        # 2 ^ 3 = 8
        expr = PBPowerOperator(
            base=PBNumberLiteral(value=2),
            exponent=PBNumberLiteral(value=3),
        )

        result = optimizer.optimize(expr)
        assert isinstance(result, PBNumberLiteral)
        assert result.value == 8

    def test_fold_ternary_with_constant_condition(self):
        """Test folding of ternary expressions with constant conditions."""
        optimizer = ExpressionOptimizer()

        # true ? 10 : 20 = 10
        expr = PBTernaryExpression(
            condition=PBBooleanLiteral(value=True),
            true_expr=PBNumberLiteral(value=10),
            false_expr=PBNumberLiteral(value=20),
        )

        result = optimizer.optimize(expr)
        assert isinstance(result, PBNumberLiteral)
        assert result.value == 10

        # false ? 10 : 20 = 20
        expr = PBTernaryExpression(
            condition=PBBooleanLiteral(value=False),
            true_expr=PBNumberLiteral(value=10),
            false_expr=PBNumberLiteral(value=20),
        )

        result = optimizer.optimize(expr)
        assert isinstance(result, PBNumberLiteral)
        assert result.value == 20

    def test_nested_constant_folding(self):
        """Test folding of nested expressions."""
        optimizer = ExpressionOptimizer()

        # (2 + 3) * (4 - 1) = 5 * 3 = 15
        expr = PBBinaryOperator(
            left=PBBinaryOperator(
                left=PBNumberLiteral(value=2),
                operator="+",
                right=PBNumberLiteral(value=3),
            ),
            operator="*",
            right=PBBinaryOperator(
                left=PBNumberLiteral(value=4),
                operator="-",
                right=PBNumberLiteral(value=1),
            ),
        )

        result = optimizer.optimize(expr)
        assert isinstance(result, PBNumberLiteral)
        assert result.value == 15
        assert optimizer.optimizations_applied >= 3  # At least 3 folds


class TestAlgebraicSimplification:
    """Test algebraic simplification optimizations."""

    def test_add_zero_identity(self):
        """Test x + 0 = x and 0 + x = x."""
        optimizer = ExpressionOptimizer()
        var = PBVariable(name="x")

        # x + 0 = x
        expr = PBBinaryOperator(
            left=var,
            operator="+",
            right=PBNumberLiteral(value=0),
        )

        result = optimizer.optimize(expr)
        assert isinstance(result, PBVariable)
        assert result.name == "x"

        # 0 + x = x
        expr = PBBinaryOperator(
            left=PBNumberLiteral(value=0),
            operator="+",
            right=var,
        )

        result = optimizer.optimize(expr)
        assert isinstance(result, PBVariable)
        assert result.name == "x"

    def test_subtract_zero_identity(self):
        """Test x - 0 = x."""
        optimizer = ExpressionOptimizer()
        var = PBVariable(name="x")

        # x - 0 = x
        expr = PBBinaryOperator(
            left=var,
            operator="-",
            right=PBNumberLiteral(value=0),
        )

        result = optimizer.optimize(expr)
        assert isinstance(result, PBVariable)
        assert result.name == "x"

    def test_subtract_self_identity(self):
        """Test x - x = 0."""
        optimizer = ExpressionOptimizer()
        var1 = PBVariable(name="x")
        var2 = PBVariable(name="x")

        # x - x = 0
        expr = PBBinaryOperator(
            left=var1,
            operator="-",
            right=var2,
        )

        result = optimizer.optimize(expr)
        assert isinstance(result, PBNumberLiteral)
        assert result.value == 0

    def test_multiply_one_identity(self):
        """Test x * 1 = x and 1 * x = x."""
        optimizer = ExpressionOptimizer()
        var = PBVariable(name="x")

        # x * 1 = x
        expr = PBBinaryOperator(
            left=var,
            operator="*",
            right=PBNumberLiteral(value=1),
        )

        result = optimizer.optimize(expr)
        assert isinstance(result, PBVariable)
        assert result.name == "x"

        # 1 * x = x
        expr = PBBinaryOperator(
            left=PBNumberLiteral(value=1),
            operator="*",
            right=var,
        )

        result = optimizer.optimize(expr)
        assert isinstance(result, PBVariable)
        assert result.name == "x"

    def test_multiply_zero_identity(self):
        """Test x * 0 = 0 and 0 * x = 0."""
        optimizer = ExpressionOptimizer()
        var = PBVariable(name="x")

        # x * 0 = 0
        expr = PBBinaryOperator(
            left=var,
            operator="*",
            right=PBNumberLiteral(value=0),
        )

        result = optimizer.optimize(expr)
        assert isinstance(result, PBNumberLiteral)
        assert result.value == 0

        # 0 * x = 0
        expr = PBBinaryOperator(
            left=PBNumberLiteral(value=0),
            operator="*",
            right=var,
        )

        result = optimizer.optimize(expr)
        assert isinstance(result, PBNumberLiteral)
        assert result.value == 0

    def test_divide_one_identity(self):
        """Test x / 1 = x."""
        optimizer = ExpressionOptimizer()
        var = PBVariable(name="x")

        # x / 1 = x
        expr = PBBinaryOperator(
            left=var,
            operator="/",
            right=PBNumberLiteral(value=1),
        )

        result = optimizer.optimize(expr)
        assert isinstance(result, PBVariable)
        assert result.name == "x"

    def test_power_zero_identity(self):
        """Test x ^ 0 = 1."""
        optimizer = ExpressionOptimizer()
        var = PBVariable(name="x")

        # x ^ 0 = 1
        expr = PBPowerOperator(
            base=var,
            exponent=PBNumberLiteral(value=0),
        )

        result = optimizer.optimize(expr)
        assert isinstance(result, PBNumberLiteral)
        assert result.value == 1

    def test_power_one_identity(self):
        """Test x ^ 1 = x."""
        optimizer = ExpressionOptimizer()
        var = PBVariable(name="x")

        # x ^ 1 = x
        expr = PBPowerOperator(
            base=var,
            exponent=PBNumberLiteral(value=1),
        )

        result = optimizer.optimize(expr)
        assert isinstance(result, PBVariable)
        assert result.name == "x"


class TestBooleanOptimization:
    """Test boolean expression optimizations."""

    def test_and_true_identity(self):
        """Test true AND x = x and x AND true = x."""
        optimizer = ExpressionOptimizer()
        var = PBVariable(name="x")

        # true AND x = x
        expr = PBBinaryOperator(
            left=PBBooleanLiteral(value=True),
            operator="AND",
            right=var,
        )

        result = optimizer.optimize(expr)
        assert isinstance(result, PBVariable)
        assert result.name == "x"

        # x AND true = x
        expr = PBBinaryOperator(
            left=var,
            operator="AND",
            right=PBBooleanLiteral(value=True),
        )

        result = optimizer.optimize(expr)
        assert isinstance(result, PBVariable)
        assert result.name == "x"

    def test_and_false_identity(self):
        """Test false AND x = false and x AND false = false."""
        optimizer = ExpressionOptimizer()
        var = PBVariable(name="x")

        # false AND x = false
        expr = PBBinaryOperator(
            left=PBBooleanLiteral(value=False),
            operator="AND",
            right=var,
        )

        result = optimizer.optimize(expr)
        assert isinstance(result, PBBooleanLiteral)
        assert result.value is False

        # x AND false = false
        expr = PBBinaryOperator(
            left=var,
            operator="AND",
            right=PBBooleanLiteral(value=False),
        )

        result = optimizer.optimize(expr)
        assert isinstance(result, PBBooleanLiteral)
        assert result.value is False

    def test_or_true_identity(self):
        """Test true OR x = true and x OR true = true."""
        optimizer = ExpressionOptimizer()
        var = PBVariable(name="x")

        # true OR x = true
        expr = PBBinaryOperator(
            left=PBBooleanLiteral(value=True),
            operator="OR",
            right=var,
        )

        result = optimizer.optimize(expr)
        assert isinstance(result, PBBooleanLiteral)
        assert result.value is True

        # x OR true = true
        expr = PBBinaryOperator(
            left=var,
            operator="OR",
            right=PBBooleanLiteral(value=True),
        )

        result = optimizer.optimize(expr)
        assert isinstance(result, PBBooleanLiteral)
        assert result.value is True

    def test_or_false_identity(self):
        """Test false OR x = x and x OR false = x."""
        optimizer = ExpressionOptimizer()
        var = PBVariable(name="x")

        # false OR x = x
        expr = PBBinaryOperator(
            left=PBBooleanLiteral(value=False),
            operator="OR",
            right=var,
        )

        result = optimizer.optimize(expr)
        assert isinstance(result, PBVariable)
        assert result.name == "x"

        # x OR false = x
        expr = PBBinaryOperator(
            left=var,
            operator="OR",
            right=PBBooleanLiteral(value=False),
        )

        result = optimizer.optimize(expr)
        assert isinstance(result, PBVariable)
        assert result.name == "x"

    def test_double_negation_elimination(self):
        """Test NOT NOT x = x."""
        optimizer = ExpressionOptimizer()
        var = PBVariable(name="x")

        # NOT NOT x = x
        expr = PBUnaryOperator(
            operator="NOT",
            operand=PBUnaryOperator(
                operator="NOT",
                operand=var,
            ),
        )

        result = optimizer.optimize(expr)
        assert isinstance(result, PBVariable)
        assert result.name == "x"


class TestComplexOptimizations:
    """Test complex optimization scenarios."""

    def test_mixed_optimizations(self):
        """Test expressions requiring multiple optimization types."""
        optimizer = ExpressionOptimizer()

        # (x + 0) * 1 = x
        var = PBVariable(name="x")
        expr = PBBinaryOperator(
            left=PBBinaryOperator(
                left=var,
                operator="+",
                right=PBNumberLiteral(value=0),
            ),
            operator="*",
            right=PBNumberLiteral(value=1),
        )

        result = optimizer.optimize(expr)
        assert isinstance(result, PBVariable)
        assert result.name == "x"

    def test_no_optimization_needed(self):
        """Test that expressions without optimization opportunities are unchanged."""
        optimizer = ExpressionOptimizer()

        # x + y (no optimization possible)
        expr = PBBinaryOperator(
            left=PBVariable(name="x"),
            operator="+",
            right=PBVariable(name="y"),
        )

        result = optimizer.optimize(expr)
        assert isinstance(result, PBBinaryOperator)
        assert optimizer.optimizations_applied == 0

    def test_null_handling(self):
        """Test optimization with null values."""
        optimizer = ExpressionOptimizer()

        # null + 5 = null (in PowerBuilder)
        expr = PBBinaryOperator(
            left=PBNullLiteral(),
            operator="+",
            right=PBNumberLiteral(value=5),
        )

        result = optimizer.optimize(expr)
        assert isinstance(result, PBNullLiteral)

    def test_deeply_nested_optimization(self):
        """Test optimization of deeply nested expressions."""
        optimizer = ExpressionOptimizer()

        # ((2 + 3) * (1 * x)) / 1 = 5 * x
        var = PBVariable(name="x")
        expr = PBBinaryOperator(
            left=PBBinaryOperator(
                left=PBBinaryOperator(
                    left=PBNumberLiteral(value=2),
                    operator="+",
                    right=PBNumberLiteral(value=3),
                ),
                operator="*",
                right=PBBinaryOperator(
                    left=PBNumberLiteral(value=1),
                    operator="*",
                    right=var,
                ),
            ),
            operator="/",
            right=PBNumberLiteral(value=1),
        )

        result = optimizer.optimize(expr)
        # Should simplify to 5 * x
        assert isinstance(result, PBBinaryOperator)
        assert isinstance(result.left, PBNumberLiteral)
        assert result.left.value == 5
        assert result.operator == "*"
        assert isinstance(result.right, PBVariable)
        assert result.right.name == "x"
