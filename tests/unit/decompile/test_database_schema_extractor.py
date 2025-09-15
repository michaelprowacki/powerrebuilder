"""Tests for database schema extraction functionality."""

import json
import tempfile
from pathlib import Path

from src.decompile.analyzers.schema_generator import (
    SchemaDocumentationGenerator,
)
from src.decompile.extractors.logic import BusinessLogicMapper
from src.decompile.extractors.schema_extractor import (
    DatabaseSchemaExtractor,
    TableInfo,
)


class TestDatabaseSchemaExtractor:
    """Test database schema extraction."""

    def test_extract_table_from_select(self):
        """Test extracting table names from SELECT statements."""
        extractor = DatabaseSchemaExtractor()

        # Create test SQL
        sql = "SELECT id, name FROM users WHERE active = 1"
        extractor._process_sql_statement(sql, "test_window", None, 1)

        assert "users" in extractor.tables
        assert "id" in extractor.tables["users"].columns
        assert "name" in extractor.tables["users"].columns
        assert extractor.tables["users"].operations["SELECT"] == 1

    def test_extract_table_from_insert(self):
        """Test extracting table names from INSERT statements."""
        extractor = DatabaseSchemaExtractor()

        sql = "INSERT INTO customers (name, email) VALUES (:name, :email)"
        extractor._process_sql_statement(sql, "test_window", None, 1)

        assert "customers" in extractor.tables
        assert "name" in extractor.tables["customers"].columns
        assert "email" in extractor.tables["customers"].columns
        assert extractor.tables["customers"].operations["INSERT"] == 1

    def test_extract_table_from_update(self):
        """Test extracting table names from UPDATE statements."""
        extractor = DatabaseSchemaExtractor()

        sql = "UPDATE orders SET status = :status WHERE id = :id"
        extractor._process_sql_statement(sql, "test_window", None, 1)

        assert "orders" in extractor.tables
        assert "status" in extractor.tables["orders"].columns
        assert extractor.tables["orders"].operations["UPDATE"] == 1

    def test_extract_table_from_delete(self):
        """Test extracting table names from DELETE statements."""
        extractor = DatabaseSchemaExtractor()

        sql = "DELETE FROM logs WHERE created_at < :cutoff_date"
        extractor._process_sql_statement(sql, "test_window", None, 1)

        assert "logs" in extractor.tables
        assert extractor.tables["logs"].operations["DELETE"] == 1

    def test_extract_join_relationships(self):
        """Test extracting relationships from JOIN clauses."""
        extractor = DatabaseSchemaExtractor()

        sql = """
        SELECT o.id, o.order_date, c.name
        FROM orders o
        JOIN customers c ON o.customer_id = c.id
        """
        extractor._process_sql_statement(sql, "test_window", None, 1)

        assert "orders" in extractor.tables
        assert "customers" in extractor.tables

    def test_extract_from_datawindow(self):
        """Test extracting schema from DataWindow syntax."""
        extractor = DatabaseSchemaExtractor()

        # Create test DataWindow content
        dw_content = """
        retrieve="SELECT employee.id, employee.name, department.name as dept_name
                  FROM employee, department
                  WHERE employee.dept_id = department.id"

        table(column=(name=employee.id) column=(name=employee.name) column=(name=department.name))
        """

        with tempfile.NamedTemporaryFile(mode="w", suffix=".srd", delete=False) as f:
            f.write(dw_content)
            temp_file = Path(f.name)

        try:
            extractor._process_file(temp_file)

            assert "employee" in extractor.tables
            assert "department" in extractor.tables
            assert "id" in extractor.tables["employee"].columns
            assert "name" in extractor.tables["employee"].columns

        finally:
            temp_file.unlink()

    def test_foreign_key_detection(self):
        """Test detection of foreign key relationships."""
        extractor = DatabaseSchemaExtractor()

        # Add tables with FK-like columns
        extractor.tables["orders"] = TableInfo(name="orders")
        extractor.tables["orders"].add_column("id")
        extractor.tables["orders"].add_column("customer_id")

        extractor.tables["customers"] = TableInfo(name="customers")
        extractor.tables["customers"].add_column("id")

        # Analyze relationships
        extractor._analyze_relationships()

        # Check if relationship was detected
        assert len(extractor.relationships) > 0
        rel = extractor.relationships[0]
        assert rel.from_table == "orders"
        assert rel.from_column == "customer_id"
        assert rel.to_table == "customers"
        assert rel.to_column == "id"

    def test_transaction_config_extraction(self):
        """Test extraction of transaction configurations."""
        extractor = DatabaseSchemaExtractor()

        pb_content = """
        transaction sqlca
        SQLCA.DBMS = "ODBC"
        SQLCA.Database = "mydb"
        SQLCA.ServerName = "localhost"
        """

        extractor._extract_transaction_config(pb_content, "test_app")

        assert "sqlca" in extractor.transaction_objects
        trans = extractor.transaction_objects["sqlca"]
        assert trans["properties"]["DBMS"] == "ODBC"
        assert trans["properties"]["Database"] == "mydb"
        assert trans["properties"]["ServerName"] == "localhost"

    def test_full_project_extraction(self):
        """Test extracting schema from a complete project structure."""
        # Create test project structure
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)

            # Create test window with SQL
            window_dir = project_path / "windows"
            window_dir.mkdir()

            window_content = """
            global type w_customer from window
            end type

            event open()
                SELECT id, name, email
                INTO :li_id, :ls_name, :ls_email
                FROM customers
                WHERE id = :al_customer_id;

                dw_orders.Retrieve(al_customer_id)
            end event
            """

            (window_dir / "w_customer.srw").write_text(window_content)

            # Create test DataWindow
            dw_dir = project_path / "datawindows"
            dw_dir.mkdir()

            dw_content = """
            retrieve="SELECT order_id, order_date, total_amount
                      FROM orders
                      WHERE customer_id = :customer_id"
            """

            (dw_dir / "d_orders.srd").write_text(dw_content)

            # Extract schema
            extractor = DatabaseSchemaExtractor()
            result = extractor.extract_schema_from_project(project_path)

            # Verify results
            assert result["statistics"]["total_tables"] >= 2
            assert "customers" in result["tables"]
            assert "orders" in result["tables"]

            # Check columns
            assert "id" in result["tables"]["customers"]["columns"]
            assert "name" in result["tables"]["customers"]["columns"]
            assert "email" in result["tables"]["customers"]["columns"]

            assert "order_id" in result["tables"]["orders"]["columns"]
            assert "order_date" in result["tables"]["orders"]["columns"]

            # Check operations
            assert result["statistics"]["operation_counts"]["SELECT"] >= 2


class TestBusinessLogicMapper:
    """Test business logic mapping functionality."""

    def test_function_extraction(self):
        """Test extracting functions and their database operations."""
        mapper = BusinessLogicMapper()

        pb_content = """
        public function integer retrieve_customer(long al_id)
            string ls_name, ls_email

            SELECT name, email
            INTO :ls_name, :ls_email
            FROM customers
            WHERE id = :al_id;

            if sqlca.sqlcode = 0 then
                return 1
            else
                return -1
            end if
        end function
        """

        mapper._extract_functions(pb_content, "n_customer", "UserObject")

        assert "n_customer.retrieve_customer" in mapper.business_functions
        func = mapper.business_functions["n_customer.retrieve_customer"]
        assert func.name == "retrieve_customer"
        assert func.return_type == "integer"
        assert "al_id" in func.parameters
        assert "customers" in func.accessed_tables

    def test_ui_element_extraction(self):
        """Test extracting UI elements and their data bindings."""
        mapper = BusinessLogicMapper()

        window_content = """
        global type w_order_entry from window
        type dw_customer from datawindow within w_order_entry
        type dw_orders from datawindow within w_order_entry
        type cb_save from commandbutton within w_order_entry
        end type

        dw_customer.dataobject = "d_customer"
        dw_orders.dataobject = "d_order_list"

        event cb_save::clicked()
            dw_customer.Update()
            dw_orders.Update()
        end event
        """

        mapper._extract_window_controls(window_content, "w_order_entry")

        assert "w_order_entry.dw_customer" in mapper.ui_elements
        assert "w_order_entry.dw_orders" in mapper.ui_elements
        assert "w_order_entry.cb_save" in mapper.ui_elements

        # Check DataWindow properties
        dw_customer = mapper.ui_elements["w_order_entry.dw_customer"]
        assert dw_customer.data_source == "d_customer"
        assert dw_customer.type == "DataWindow"

    def test_data_flow_analysis(self):
        """Test analyzing data flows between components."""
        mapper = BusinessLogicMapper()

        # Set up test data
        mapper.business_functions["func1"] = mapper.BusinessFunction(
            name="func1",
            object_name="obj1",
            object_type="Function",
            accessed_tables={"customers", "orders"},
        )

        mapper.ui_elements["window1.dw1"] = mapper.UIElement(
            name="dw1",
            type="DataWindow",
            parent_object="window1",
            accessed_tables={"customers"},
        )

        # Analyze flows
        mapper._analyze_data_flows()

        # Check flows were created
        assert len(mapper.data_flows) > 0


class TestSchemaDocumentationGenerator:
    """Test documentation generation."""

    def test_markdown_generation(self):
        """Test generating markdown documentation."""
        generator = SchemaDocumentationGenerator()

        # Create test mapping data
        mapping_data = {
            "database_schema": {
                "tables": {
                    "customers": {
                        "name": "customers",
                        "columns": ["id", "name", "email"],
                        "primary_keys": ["id"],
                        "foreign_keys": {},
                        "indexes": [],
                        "used_in_objects": ["w_customer", "d_customer"],
                        "operations": {"SELECT": 5, "INSERT": 2, "UPDATE": 3},
                    },
                },
                "relationships": [],
                "operations": [],
                "connection_strings": {},
                "transaction_objects": {},
                "statistics": {
                    "total_tables": 1,
                    "total_columns": 3,
                    "total_relationships": 0,
                    "total_operations": 10,
                    "operation_counts": {"SELECT": 5, "INSERT": 2, "UPDATE": 3},
                },
            },
            "business_functions": {},
            "ui_elements": {},
            "data_flows": [],
            "function_hierarchy": {},
            "statistics": {
                "total_functions": 0,
                "total_ui_elements": 0,
                "total_data_flows": 0,
            },
        }

        # Generate documentation
        doc = generator.generate_documentation(mapping_data, "markdown")

        # Verify content
        assert "# PowerBuilder Application Database Schema" in doc
        assert "## Executive Summary" in doc
        assert "## Database Schema" in doc
        assert "### Table: `customers`" in doc
        assert "| id | - | PK |" in doc
        assert "- **SELECT**: 5 occurrences" in doc

    def test_html_generation(self):
        """Test generating HTML documentation."""
        generator = SchemaDocumentationGenerator()

        mapping_data = {
            "database_schema": {
                "tables": {},
                "statistics": {},
            },
            "statistics": {},
        }

        # Generate HTML
        doc = generator.generate_documentation(mapping_data, "html")

        # Verify HTML structure
        assert "<!DOCTYPE html>" in doc
        assert "<title>PowerBuilder Database Schema Documentation</title>" in doc
        assert "<style>" in doc

    def test_json_generation(self):
        """Test generating JSON documentation."""
        generator = SchemaDocumentationGenerator()

        mapping_data = {
            "database_schema": {
                "tables": {},
                "statistics": {},
            },
            "statistics": {},
        }

        # Generate JSON
        doc = generator.generate_documentation(mapping_data, "json")

        # Verify JSON structure
        data = json.loads(doc)
        assert "metadata" in data
        assert "data" in data
        assert "generated_at" in data["metadata"]
