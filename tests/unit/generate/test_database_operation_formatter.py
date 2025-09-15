"""Test suite for DatabaseOperationFormatter."""

import pytest

from src.generate.converters.flutter.api import (
    DatabaseOperation,
    DatabaseOperationFormatter,
)


class TestDatabaseOperationFormatter:
    """Test cases for database operation formatting."""

    def setup_method(self):
        """Set up test instances."""
        self.flutter_formatter = DatabaseOperationFormatter(target="flutter")
        self.python_formatter = DatabaseOperationFormatter(target="python")

    def test_initialization(self):
        """Test formatter initialization."""
        assert self.flutter_formatter.target == "flutter"
        assert self.python_formatter.target == "python"

        # Test default target
        default_formatter = DatabaseOperationFormatter()
        assert default_formatter.target == "flutter"

    def test_parse_select_operation(self):
        """Test parsing SELECT operations."""
        # Simple SELECT
        op = self.flutter_formatter._parse_operation(
            "SELECT emp_id, emp_name FROM employee WHERE dept_id = :dept_id",
        )

        assert op is not None
        assert op.operation_type == "SELECT"
        assert op.table_name == "employee"
        assert "emp_id" in op.columns
        assert "emp_name" in op.columns
        assert "dept_id = :dept_id" in op.conditions

        # SELECT with INTO
        op = self.flutter_formatter._parse_operation(
            "SELECT COUNT(*) INTO :li_count FROM orders",
        )

        assert op is not None
        assert op.operation_type == "SELECT"
        assert op.table_name == "orders"
        assert "li_count" in op.variables

    def test_parse_insert_operation(self):
        """Test parsing INSERT operations."""
        op = self.flutter_formatter._parse_operation(
            "INSERT INTO employee (emp_id, emp_name, salary) VALUES (:id, :name, :salary)",
        )

        assert op is not None
        assert op.operation_type == "INSERT"
        assert op.table_name == "employee"
        assert "emp_id" in op.columns
        assert "emp_name" in op.columns
        assert "salary" in op.columns
        assert len(op.variables) == 3

    def test_parse_update_operation(self):
        """Test parsing UPDATE operations."""
        op = self.flutter_formatter._parse_operation(
            "UPDATE employee SET salary = :new_salary WHERE emp_id = :emp_id",
        )

        assert op is not None
        assert op.operation_type == "UPDATE"
        assert op.table_name == "employee"
        assert "salary" in op.columns
        assert "emp_id = :emp_id" in op.conditions

    def test_parse_delete_operation(self):
        """Test parsing DELETE operations."""
        op = self.flutter_formatter._parse_operation(
            "DELETE FROM employee WHERE emp_id = :emp_id AND active = 0",
        )

        assert op is not None
        assert op.operation_type == "DELETE"
        assert op.table_name == "employee"
        assert "emp_id = :emp_id AND active = 0" in op.conditions

    def test_format_flutter_select(self):
        """Test formatting SELECT operation for Flutter."""
        operations = ["SELECT emp_id, emp_name FROM employee WHERE dept_id = :dept_id"]

        result = self.flutter_formatter.format_database_operations(operations)

        assert len(result) > 0
        assert any("await" in line for line in result)
        assert any("database.query" in line for line in result)
        assert any("try" in line for line in result)

    def test_format_python_select(self):
        """Test formatting SELECT operation for Python."""
        operations = ["SELECT emp_id, emp_name FROM employee WHERE dept_id = :dept_id"]

        result = self.python_formatter.format_database_operations(operations)

        assert len(result) > 0
        assert any("session.query" in line or "select(" in line for line in result)
        assert any("Employee" in line for line in result)

    def test_format_transaction_block_flutter(self):
        """Test formatting transaction block for Flutter."""
        operations = [
            "BEGIN TRANSACTION",
            "UPDATE account SET balance = balance - :amount WHERE id = :from_id",
            "UPDATE account SET balance = balance + :amount WHERE id = :to_id",
            "COMMIT",
        ]

        result = self.flutter_formatter.format_database_operations(operations)

        assert len(result) > 0
        assert any("transaction" in line.lower() for line in result)
        assert any("try" in line for line in result)
        assert any("catch" in line for line in result)
        assert any("rollback" in line.lower() for line in result)

    def test_format_transaction_block_python(self):
        """Test formatting transaction block for Python."""
        operations = [
            "BEGIN TRANSACTION",
            "INSERT INTO log (message) VALUES (:message)",
            "UPDATE status SET last_update = :timestamp",
            "COMMIT",
        ]

        result = self.python_formatter.format_database_operations(operations)

        assert len(result) > 0
        assert any(
            "with session" in line or "session.begin()" in line for line in result
        )
        assert any("try:" in line for line in result)
        assert any("except" in line for line in result)

    def test_format_cursor_operations_flutter(self):
        """Test formatting cursor operations for Flutter."""
        operations = [
            "DECLARE emp_cursor CURSOR FOR SELECT emp_id, emp_name FROM employee",
            "OPEN emp_cursor",
            "FETCH emp_cursor INTO :emp_id, :emp_name",
            "CLOSE emp_cursor",
        ]

        result = self.flutter_formatter.format_database_operations(operations)

        assert len(result) > 0
        assert any("query" in line for line in result)
        assert any("forEach" in line or "for" in line for line in result)

    def test_format_cursor_operations_python(self):
        """Test formatting cursor operations for Python."""
        operations = [
            "DECLARE order_cursor CURSOR FOR SELECT * FROM orders WHERE status = 'pending'",
            "OPEN order_cursor",
            "FETCH order_cursor INTO :order_rec",
            "CLOSE order_cursor",
        ]

        result = self.python_formatter.format_database_operations(operations)

        assert len(result) > 0
        assert any("query" in line or "select" in line for line in result)
        assert any("for" in line for line in result)

    def test_format_with_context(self):
        """Test formatting with context information."""
        operations = [
            "SELECT emp_name INTO :ls_name FROM employee WHERE emp_id = :li_id"
        ]

        context = {
            "variables": {
                "ls_name": {"type": "String", "python_type": "str"},
                "li_id": {"type": "int", "python_type": "int"},
            },
            "table_mappings": {
                "employee": "Employee",  # Model class name
            },
        }

        flutter_result = self.flutter_formatter.format_database_operations(
            operations, context
        )
        python_result = self.python_formatter.format_database_operations(
            operations, context
        )

        assert len(flutter_result) > 0
        assert len(python_result) > 0
        assert any("Employee" in line for line in python_result)

    def test_format_stored_procedure_call(self):
        """Test formatting stored procedure calls."""
        operations = ["EXECUTE sp_update_salary(:emp_id, :new_salary)"]

        flutter_result = self.flutter_formatter.format_database_operations(operations)
        python_result = self.python_formatter.format_database_operations(operations)

        assert len(flutter_result) > 0
        assert len(python_result) > 0
        assert any(
            "call" in line.lower() or "execute" in line.lower()
            for line in flutter_result
        )
        assert any(
            "execute" in line.lower() or "func" in line.lower()
            for line in python_result
        )

    def test_format_dynamic_sql(self):
        """Test formatting dynamic SQL operations."""
        operations = [
            "PREPARE dynamic_stmt FROM :sql_string",
            "EXECUTE dynamic_stmt USING :param1, :param2",
        ]

        result = self.flutter_formatter.format_database_operations(operations)

        assert len(result) > 0
        assert any(
            "prepare" in line.lower() or "dynamic" in line.lower() for line in result
        )

    def test_empty_operations(self):
        """Test handling empty operations list."""
        result = self.flutter_formatter.format_database_operations([])
        assert result == []

    def test_invalid_operation(self):
        """Test handling invalid operations."""
        operations = ["INVALID SQL STATEMENT HERE"]

        result = self.flutter_formatter.format_database_operations(operations)

        # Should either return empty or comment
        assert len(result) == 0 or any("//" in line or "#" in line for line in result)

    def test_database_operation_dataclass(self):
        """Test DatabaseOperation dataclass."""
        op = DatabaseOperation(
            operation_type="SELECT",
            table_name="users",
            columns=["id", "name"],
            conditions="active = 1",
        )

        assert op.operation_type == "SELECT"
        assert op.table_name == "users"
        assert len(op.columns) == 2
        assert op.conditions == "active = 1"
        assert op.variables == []  # Should default to empty list

    def test_complex_join_operation(self):
        """Test formatting complex JOIN operations."""
        operations = [
            """SELECT e.emp_name, d.dept_name, m.emp_name as manager_name
               FROM employee e
               INNER JOIN department d ON e.dept_id = d.dept_id
               LEFT JOIN employee m ON e.manager_id = m.emp_id
               WHERE e.active = 1 AND d.location = :location""",
        ]

        result = self.flutter_formatter.format_database_operations(operations)

        assert len(result) > 0
        # Should handle the complex query appropriately
        assert any("join" in line.lower() or "query" in line.lower() for line in result)

    def test_batch_operations(self):
        """Test formatting batch operations."""
        operations = [
            "BEGIN BATCH",
            "INSERT INTO log (event) VALUES (:event1)",
            "INSERT INTO log (event) VALUES (:event2)",
            "INSERT INTO log (event) VALUES (:event3)",
            "END BATCH",
        ]

        flutter_result = self.flutter_formatter.format_database_operations(operations)
        python_result = self.python_formatter.format_database_operations(operations)

        assert len(flutter_result) > 0
        assert len(python_result) > 0
        # Should recognize batch pattern
        assert any(
            "batch" in line.lower() or "bulk" in line.lower()
            for line in flutter_result + python_result
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
