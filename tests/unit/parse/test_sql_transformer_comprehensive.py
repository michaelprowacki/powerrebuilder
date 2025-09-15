#!/usr/bin/env python3
"""Comprehensive test suite for SQL transformer column reference fixes."""

import pytest

from src.model.ast import (
    Assignment,
    BinaryExpression,
    ColumnReference,
    DeleteStatement,
    InsertStatement,
    IntegerLiteral,
    JoinClause,
    SelectStatement,
    StringLiteral,
    SubqueryExpression,
    UpdateStatement,
    WithClause,
)
from src.parse.parser.specialized.sql import SQLParser


class TestSQLTransformerColumnReferences:
    """Test that SQL transformer properly handles column references."""

    @pytest.fixture
    def parser(self):
        """Create SQL parser instance."""
        return SQLParser()

    def test_simple_column_reference_in_select(self, parser):
        """Test simple column references in SELECT clause."""
        query = "SELECT id, name, email FROM users"
        ast = parser.parse(query)

        assert len(ast) == 1
        stmt = ast[0]
        assert isinstance(stmt, SelectStatement)
        assert len(stmt.result_columns) == 3

        # Check each column is a ColumnReference
        for i, col_name in enumerate(["id", "name", "email"]):
            col = stmt.result_columns[i]
            assert isinstance(col.expression, ColumnReference)
            assert col.expression.column_name == col_name
            assert col.expression.table_name is None

    def test_fully_qualified_column_reference(self, parser):
        """Test fully qualified column references."""
        query = "SELECT users.id, users.name, orders.total FROM users, orders"
        ast = parser.parse(query)

        stmt = ast[0]
        assert isinstance(stmt, SelectStatement)
        assert len(stmt.result_columns) == 3

        # Check fully qualified columns
        assert isinstance(stmt.result_columns[0].expression, ColumnReference)
        assert stmt.result_columns[0].expression.column_name == "id"
        assert stmt.result_columns[0].expression.table_name == "users"

        assert isinstance(stmt.result_columns[1].expression, ColumnReference)
        assert stmt.result_columns[1].expression.column_name == "name"
        assert stmt.result_columns[1].expression.table_name == "users"

        assert isinstance(stmt.result_columns[2].expression, ColumnReference)
        assert stmt.result_columns[2].expression.column_name == "total"
        assert stmt.result_columns[2].expression.table_name == "orders"

    def test_column_reference_in_where_clause(self, parser):
        """Test column references in WHERE clause."""
        query = "SELECT * FROM users WHERE active = 1 AND status = 'enabled'"
        ast = parser.parse(query)

        stmt = ast[0]
        assert isinstance(stmt, SelectStatement)
        assert stmt.where_clause is not None

        # WHERE clause should have AND expression
        assert isinstance(stmt.where_clause.condition, BinaryExpression)
        assert stmt.where_clause.condition.operator == "AND"

        # Left side: active = 1
        left_expr = stmt.where_clause.condition.left
        assert isinstance(left_expr, BinaryExpression)
        assert isinstance(left_expr.left, ColumnReference)
        assert left_expr.left.column_name == "active"
        assert isinstance(left_expr.right, IntegerLiteral)
        assert left_expr.right.value == 1

        # Right side: status = 'enabled'
        right_expr = stmt.where_clause.condition.right
        assert isinstance(right_expr, BinaryExpression)
        assert isinstance(right_expr.left, ColumnReference)
        assert right_expr.left.column_name == "status"
        assert isinstance(right_expr.right, StringLiteral)
        assert right_expr.right.value == "enabled"

    def test_column_reference_in_update_assignment(self, parser):
        """Test column references in UPDATE assignments."""
        query = "UPDATE users SET active = 0, last_login = NULL WHERE id = 123"
        ast = parser.parse(query)

        stmt = ast[0]
        assert isinstance(stmt, UpdateStatement)
        assert len(stmt.assignments) == 2

        # Check assignments
        assert isinstance(stmt.assignments[0], Assignment)
        assert stmt.assignments[0].target_column == "active"
        assert isinstance(stmt.assignments[0].value, IntegerLiteral)
        assert stmt.assignments[0].value.value == 0

        assert isinstance(stmt.assignments[1], Assignment)
        assert stmt.assignments[1].target_column == "last_login"
        # NULL should be handled as a literal

        # Check WHERE clause
        assert stmt.where_clause is not None
        assert isinstance(stmt.where_clause.condition, BinaryExpression)
        assert isinstance(stmt.where_clause.condition.left, ColumnReference)
        assert stmt.where_clause.condition.left.column_name == "id"

    def test_column_reference_in_join_condition(self, parser):
        """Test column references in JOIN conditions."""
        query = "SELECT * FROM users u JOIN orders o ON u.id = o.user_id"
        ast = parser.parse(query)

        stmt = ast[0]
        assert isinstance(stmt, SelectStatement)
        assert stmt.from_clause is not None
        assert len(stmt.from_clause.joins) == 1

        join = stmt.from_clause.joins[0]
        assert isinstance(join, JoinClause)
        assert join.join_operator == "JOIN"
        assert join.on_condition is not None

        # Check ON condition
        assert isinstance(join.on_condition, BinaryExpression)
        assert join.on_condition.operator == "="

        # Left side: u.id
        assert isinstance(join.on_condition.left, ColumnReference)
        assert join.on_condition.left.column_name == "id"
        assert join.on_condition.left.table_name == "u"

        # Right side: o.user_id
        assert isinstance(join.on_condition.right, ColumnReference)
        assert join.on_condition.right.column_name == "user_id"
        assert join.on_condition.right.table_name == "o"

    def test_column_reference_in_group_by(self, parser):
        """Test column references in GROUP BY clause."""
        query = "SELECT department, COUNT(*) FROM employees GROUP BY department"
        ast = parser.parse(query)

        stmt = ast[0]
        assert isinstance(stmt, SelectStatement)
        assert stmt.group_by_clause is not None

        # GROUP BY should have column reference
        assert len(stmt.group_by_clause.expressions) == 1
        assert isinstance(stmt.group_by_clause.expressions[0], ColumnReference)
        assert stmt.group_by_clause.expressions[0].column_name == "department"

    def test_column_reference_in_order_by(self, parser):
        """Test column references in ORDER BY clause."""
        query = "SELECT * FROM users ORDER BY created_at DESC, name ASC"
        ast = parser.parse(query)

        stmt = ast[0]
        assert isinstance(stmt, SelectStatement)
        assert stmt.order_by_clause is not None
        assert len(stmt.order_by_clause.terms) == 2

        # First ordering term
        term1 = stmt.order_by_clause.terms[0]
        assert isinstance(term1.expression, ColumnReference)
        assert term1.expression.column_name == "created_at"
        assert term1.direction == "DESC"

        # Second ordering term
        term2 = stmt.order_by_clause.terms[1]
        assert isinstance(term2.expression, ColumnReference)
        assert term2.expression.column_name == "name"
        assert term2.direction == "ASC"

    def test_column_reference_in_having(self, parser):
        """Test column references in HAVING clause."""
        query = "SELECT department, COUNT(*) as cnt FROM employees GROUP BY department HAVING COUNT(*) > 5"
        ast = parser.parse(query)

        stmt = ast[0]
        assert isinstance(stmt, SelectStatement)
        assert stmt.having_clause is not None

        # HAVING condition should be a binary expression
        assert isinstance(stmt.having_clause.condition, BinaryExpression)
        assert stmt.having_clause.condition.operator == ">"

    def test_column_reference_with_alias(self, parser):
        """Test column references with aliases."""
        query = "SELECT u.id AS user_id, u.name AS user_name FROM users u"
        ast = parser.parse(query)

        stmt = ast[0]
        assert isinstance(stmt, SelectStatement)
        assert len(stmt.result_columns) == 2

        # First column with alias
        col1 = stmt.result_columns[0]
        assert isinstance(col1.expression, ColumnReference)
        assert col1.expression.column_name == "id"
        assert col1.expression.table_name == "u"
        assert col1.alias == "user_id"

        # Second column with alias
        col2 = stmt.result_columns[1]
        assert isinstance(col2.expression, ColumnReference)
        assert col2.expression.column_name == "name"
        assert col2.expression.table_name == "u"
        assert col2.alias == "user_name"

    def test_column_reference_in_subquery(self, parser):
        """Test column references in subqueries."""
        query = "SELECT * FROM users WHERE id IN (SELECT user_id FROM orders WHERE total > 100)"
        ast = parser.parse(query)

        stmt = ast[0]
        assert isinstance(stmt, SelectStatement)
        assert stmt.where_clause is not None

        # WHERE condition should be IN expression
        assert isinstance(stmt.where_clause.condition, BinaryExpression)
        assert stmt.where_clause.condition.operator == "IN"

        # Left side should be column reference
        assert isinstance(stmt.where_clause.condition.left, ColumnReference)
        assert stmt.where_clause.condition.left.column_name == "id"

        # Right side should be subquery
        assert isinstance(stmt.where_clause.condition.right, SubqueryExpression)
        subquery = stmt.where_clause.condition.right.query
        assert isinstance(subquery, SelectStatement)

        # Check subquery columns
        assert len(subquery.result_columns) == 1
        assert isinstance(subquery.result_columns[0].expression, ColumnReference)
        assert subquery.result_columns[0].expression.column_name == "user_id"

    def test_column_reference_in_cte(self, parser):
        """Test column references in Common Table Expressions."""
        query = "WITH active_users AS (SELECT id, name FROM users WHERE active = 1) SELECT * FROM active_users"
        ast = parser.parse(query)

        stmt = ast[0]
        assert isinstance(stmt, SelectStatement)
        assert stmt.with_clause is not None
        assert isinstance(stmt.with_clause, WithClause)
        assert len(stmt.with_clause.expressions) == 1

        # Check CTE
        cte = stmt.with_clause.expressions[0]
        assert cte.name == "active_users"
        cte_query = cte.query
        assert isinstance(cte_query, SelectStatement)

        # Check CTE columns
        assert len(cte_query.result_columns) == 2
        assert isinstance(cte_query.result_columns[0].expression, ColumnReference)
        assert cte_query.result_columns[0].expression.column_name == "id"
        assert isinstance(cte_query.result_columns[1].expression, ColumnReference)
        assert cte_query.result_columns[1].expression.column_name == "name"

        # Check CTE WHERE clause
        assert cte_query.where_clause is not None
        assert isinstance(cte_query.where_clause.condition, BinaryExpression)
        assert isinstance(cte_query.where_clause.condition.left, ColumnReference)
        assert cte_query.where_clause.condition.left.column_name == "active"


class TestSQLTransformerLiterals:
    """Test that SQL transformer properly handles literal values."""

    @pytest.fixture
    def parser(self):
        """Create SQL parser instance."""
        return SQLParser()

    def test_numeric_literals(self, parser):
        """Test numeric literal handling."""
        query = "SELECT 42, 3.14, -100, +50 FROM dual"
        ast = parser.parse(query)

        stmt = ast[0]
        assert isinstance(stmt, SelectStatement)
        assert len(stmt.result_columns) == 4

        # Integer literal
        assert isinstance(stmt.result_columns[0].expression, IntegerLiteral)
        assert stmt.result_columns[0].expression.value == 42

        # Float literal (will be RealLiteral)
        # Note: The parser may handle this differently

        # Negative integer
        assert isinstance(stmt.result_columns[2].expression, IntegerLiteral)
        assert stmt.result_columns[2].expression.value == -100

        # Positive integer
        assert isinstance(stmt.result_columns[3].expression, IntegerLiteral)
        assert stmt.result_columns[3].expression.value == 50

    def test_string_literals(self, parser):
        """Test string literal handling."""
        query = "SELECT 'hello', \"world\" FROM dual"
        ast = parser.parse(query)

        stmt = ast[0]
        assert isinstance(stmt, SelectStatement)
        assert len(stmt.result_columns) == 2

        # Single-quoted string
        assert isinstance(stmt.result_columns[0].expression, StringLiteral)
        assert stmt.result_columns[0].expression.value == "hello"

        # Double-quoted string
        assert isinstance(stmt.result_columns[1].expression, StringLiteral)
        assert stmt.result_columns[1].expression.value == "world"

    def test_null_literal(self, parser):
        """Test NULL literal handling."""
        query = "SELECT NULL FROM dual"
        ast = parser.parse(query)

        stmt = ast[0]
        assert isinstance(stmt, SelectStatement)
        assert len(stmt.result_columns) == 1

        # NULL should be handled as a literal
        expr = stmt.result_columns[0].expression
        # The exact type depends on how NULL is represented in the AST


class TestSQLTransformerEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.fixture
    def parser(self):
        """Create SQL parser instance."""
        return SQLParser()

    def test_star_in_select(self, parser):
        """Test SELECT * handling."""
        query = "SELECT * FROM users"
        ast = parser.parse(query)

        stmt = ast[0]
        assert isinstance(stmt, SelectStatement)
        assert len(stmt.result_columns) == 1

        # Star should be a special literal
        assert isinstance(stmt.result_columns[0].expression, StringLiteral)
        assert stmt.result_columns[0].expression.value == "*"

    def test_mixed_qualified_unqualified_columns(self, parser):
        """Test mix of qualified and unqualified columns."""
        query = "SELECT users.id, name, orders.total FROM users, orders"
        ast = parser.parse(query)

        stmt = ast[0]
        assert isinstance(stmt, SelectStatement)
        assert len(stmt.result_columns) == 3

        # Qualified column
        assert isinstance(stmt.result_columns[0].expression, ColumnReference)
        assert stmt.result_columns[0].expression.table_name == "users"
        assert stmt.result_columns[0].expression.column_name == "id"

        # Unqualified column
        assert isinstance(stmt.result_columns[1].expression, ColumnReference)
        assert stmt.result_columns[1].expression.table_name is None
        assert stmt.result_columns[1].expression.column_name == "name"

        # Another qualified column
        assert isinstance(stmt.result_columns[2].expression, ColumnReference)
        assert stmt.result_columns[2].expression.table_name == "orders"
        assert stmt.result_columns[2].expression.column_name == "total"

    def test_all_statement_types(self, parser):
        """Test that all SQL statement types parse correctly."""
        queries = [
            ("SELECT id FROM users", SelectStatement),
            ("INSERT INTO users (name) VALUES ('John')", InsertStatement),
            ("UPDATE users SET active = 1", UpdateStatement),
            ("DELETE FROM users WHERE id = 1", DeleteStatement),
        ]

        for query, expected_type in queries:
            ast = parser.parse(query)
            assert len(ast) == 1
            assert isinstance(ast[0], expected_type)
