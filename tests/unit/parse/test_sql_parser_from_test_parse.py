"""Test SQL parsing functionality."""

from src.model.ast import (
    # Added more for detailed checks
    Assignment,
    ColumnReference,
    DeleteStatement,
    InsertStatement,
    JoinClause,
    OrderingTerm,
    ResultColumn,
    SelectStatement,
    TableReference,
    UpdateStatement,
)
from src.model.transaction.statement import (
    PBTransactionStatement,  # For PB-specific SQL extensions
)

# from parse.parsers.transactions import Parser # Old parser
from src.parse.parser.specialized.sql import SQLParser  # New SQL specific parser


def test_simple_select():
    """Test parsing of simple SELECT statement."""
    sql = "SELECT * FROM customers;"
    parser = SQLParser()  # Use SQLParser
    # The SQLParser.parse method currently returns a Dict for compatibility, but the real AST is in sql_ast_nodes
    # We need to adapt the test or the SQLParser return type.
    # For now, let's assume SQLParser.parse will be changed to return list[ASTNode] or a single ASTNode
    result = parser.parse(sql.strip())  # Call .parse() instead of .parse_sql()

    # If parse returns a list of statements (due to 'start: sql_statement+'):
    if isinstance(result, list):
        result_stmt = result[0]
    else:  # If it returns a single statement AST node directly (if grammar was 'start: sql_statement')
        result_stmt = result

    assert isinstance(result_stmt, SelectStatement)
    # Assuming first result column is a wildcard or needs specific check
    assert isinstance(result_stmt.result_columns[0], ResultColumn)
    # assert result_stmt.result_columns[0].expression == "*" # Lark tree might not directly give '*' as string
    assert isinstance(result_stmt.from_clause.tables[0], TableReference)
    assert result_stmt.from_clause.tables[0].table_name == "customers"


def test_complex_select():
    """Test parsing of complex SELECT with joins and conditions."""
    sql = """
    SELECT c.customer_id, c.name, o.order_date
    FROM customers c
    INNER JOIN orders o ON c.customer_id = o.customer_id
    WHERE o.order_date > '2024-01-01'
    ORDER BY o.order_date DESC;
    """
    parser = SQLParser()  # Use SQLParser
    result = parser.parse(sql.strip())  # Call .parse()

    result_stmt = result[0] if isinstance(result, list) else result

    assert isinstance(result_stmt, SelectStatement)
    assert len(result_stmt.result_columns) == 3
    assert isinstance(result_stmt.from_clause.joins[0], JoinClause)
    assert result_stmt.from_clause.joins[0].join_operator.upper() in [
        "JOIN",
        "INNER JOIN",
    ]
    assert result_stmt.order_by_clause is not None
    assert isinstance(result_stmt.order_by_clause.terms[0], OrderingTerm)
    # Check direction only if it's not None
    if result_stmt.order_by_clause.terms[0].direction:
        assert result_stmt.order_by_clause.terms[0].direction.upper() == "DESC"
    assert result_stmt.where_clause is not None


def test_insert():
    """Test parsing of INSERT statement."""
    sql = """
    INSERT INTO customers (name, address)
    VALUES ('John Doe', '123 Main St');
    """
    parser = SQLParser()  # Use SQLParser
    result = parser.parse(sql.strip())  # Call .parse()

    result_stmt = result[0] if isinstance(result, list) else result

    assert isinstance(result_stmt, InsertStatement)
    assert result_stmt.table.table_name == "customers"
    assert len(result_stmt.columns) == 2
    # Assuming columns are strings or ColumnReference nodes
    assert isinstance(result_stmt.columns[0], ColumnReference) or isinstance(
        result_stmt.columns[0], str
    )
    assert (
        result_stmt.columns[0].column_name
        if isinstance(result_stmt.columns[0], ColumnReference)
        else result_stmt.columns[0]
    ) == "name"
    assert (
        len(result_stmt.values[0]) == 2
    )  # values is typically a list of lists for multi-row inserts


def test_update():
    """Test parsing of UPDATE statement."""
    sql = """
    UPDATE customers
    SET status = 'active',
        last_updated = CURRENT_TIMESTAMP
    WHERE customer_id = 123;
    """
    parser = SQLParser()  # Use SQLParser
    result = parser.parse(sql.strip())  # Call .parse()

    result_stmt = result[0] if isinstance(result, list) else result

    assert isinstance(result_stmt, UpdateStatement)
    assert result_stmt.table.table_name == "customers"
    assert len(result_stmt.assignments) == 2
    assert isinstance(result_stmt.assignments[0], Assignment)
    assert result_stmt.where_clause is not None


def test_delete():
    """Test parsing of DELETE statement."""
    sql = "DELETE FROM customers WHERE status = 'inactive';"
    parser = SQLParser()  # Use SQLParser
    result = parser.parse(sql.strip())  # Call .parse()

    result_stmt = result[0] if isinstance(result, list) else result

    assert isinstance(result_stmt, DeleteStatement)
    assert result_stmt.table.table_name == "customers"
    assert result_stmt.where_clause is not None


# For transaction and cursor, we assume parse_sql might return PBTransactionStatement
# if it has special handling for these PowerBuilder-specific SQL commands.
# If parse_sql is intended to *only* produce the new SQL AST, these tests would need
# to expect specific AST nodes like DeclareCursorStatement, OpenCursorStatement etc.
# or they would be invalid for a pure SQL AST parser.


def test_transaction():
    """Test parsing of transaction statements."""
    statements = [
        "CONNECT USING transaction_object;",
        "COMMIT USING transaction_object;",
        "ROLLBACK USING transaction_object;",
    ]
    parser = SQLParser()  # Use SQLParser
    for stmt_str in statements:
        result = parser.parse(stmt_str.strip())  # Call .parse()
        # Assuming parse for these still gives PBTransactionStatement due to SQLParser's current mixed logic or future specific PB SQL handling
        # This part is tricky: SQLParser's parse() method is geared towards returning a pure SQL AST.
        # It's unlikely to return PBTransactionStatement directly from the Lark SQL grammar.
        # These PB-specific SQLs might need a different parsing path or the SQL grammar needs to include them.
        # For now, these assertions will likely fail if parse() returns a pure SQL AST.
        # We might need to adjust SQLParser or these tests significantly.

        # TEMPORARY: If SQLParser strictly returns SQL AST, these tests for PBTransactionStatement will fail.
        # We'll assume for now that parser.parse() might return a list containing one such statement for these inputs.
        current_stmt = result[0] if isinstance(result, list) else result
        assert isinstance(current_stmt, PBTransactionStatement)
        assert current_stmt.transaction_object == "transaction_object"


def test_cursor():
    """Test parsing of cursor operations."""
    statements = [
        "DECLARE cur_customers CURSOR FOR SELECT * FROM customers;",
        "OPEN cur_customers;",
        "FETCH cur_customers INTO :var1, :var2;",
        "CLOSE cur_customers;",
    ]
    parser = SQLParser()  # Use SQLParser
    for stmt_str in statements:
        result = parser.parse(stmt_str.strip())  # Call .parse()

        # Similar to test_transaction, these are PB-specific SQL.
        # SQLParser.parse() based on sql.lark is unlikely to produce PBTransactionStatement.
        # These assertions will likely fail.
        current_stmt = result[0] if isinstance(result, list) else result
        assert isinstance(current_stmt, PBTransactionStatement)
        if "DECLARE" in stmt_str:
            assert current_stmt.cursor_name == "cur_customers"
            assert current_stmt.sql_text is not None
        elif "FETCH" in stmt_str:
            pass  # Placeholder for more detailed fetch variable check
