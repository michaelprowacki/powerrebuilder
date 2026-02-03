"""Database Analysis - Extract and analyze database schemas from PowerBuilder.

This module provides advanced database schema extraction, SQL parsing,
and migration generation capabilities.
"""

import json
import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class SQLType(str, Enum):
    """SQL statement types."""

    SELECT = "SELECT"
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    CREATE = "CREATE"
    ALTER = "ALTER"
    DROP = "DROP"
    EXECUTE = "EXECUTE"
    CALL = "CALL"
    UNKNOWN = "UNKNOWN"


class DataType(str, Enum):
    """Database column data types."""

    INTEGER = "INTEGER"
    BIGINT = "BIGINT"
    DECIMAL = "DECIMAL"
    FLOAT = "FLOAT"
    VARCHAR = "VARCHAR"
    CHAR = "CHAR"
    TEXT = "TEXT"
    DATE = "DATE"
    TIME = "TIME"
    TIMESTAMP = "TIMESTAMP"
    BOOLEAN = "BOOLEAN"
    BLOB = "BLOB"
    JSON = "JSON"
    UNKNOWN = "UNKNOWN"


@dataclass
class Column:
    """Database column definition."""

    name: str
    data_type: DataType
    length: Optional[int] = None
    precision: Optional[int] = None
    scale: Optional[int] = None
    nullable: bool = True
    default_value: Optional[str] = None
    primary_key: bool = False
    foreign_key: Optional[str] = None
    unique: bool = False
    comment: Optional[str] = None


@dataclass
class Index:
    """Database index definition."""

    name: str
    columns: List[str]
    unique: bool = False
    clustered: bool = False
    type: str = "BTREE"


@dataclass
class ForeignKey:
    """Foreign key relationship."""

    name: str
    columns: List[str]
    reference_table: str
    reference_columns: List[str]
    on_delete: str = "CASCADE"
    on_update: str = "CASCADE"


@dataclass
class Table:
    """Database table definition."""

    name: str
    schema: Optional[str] = None
    columns: List[Column] = field(default_factory=list)
    indexes: List[Index] = field(default_factory=list)
    foreign_keys: List[ForeignKey] = field(default_factory=list)
    primary_key: Optional[List[str]] = None
    comment: Optional[str] = None

    @property
    def full_name(self) -> str:
        """Get full table name with schema."""
        if self.schema:
            return f"{self.schema}.{self.name}"
        return self.name


@dataclass
class StoredProcedure:
    """Stored procedure definition."""

    name: str
    parameters: List[Dict[str, Any]] = field(default_factory=list)
    return_type: Optional[str] = None
    body: Optional[str] = None
    called_by: List[str] = field(default_factory=list)


@dataclass
class SQLStatement:
    """Parsed SQL statement."""

    type: SQLType
    statement: str
    tables: List[str] = field(default_factory=list)
    columns: List[str] = field(default_factory=list)
    conditions: List[str] = field(default_factory=list)
    source_file: Optional[str] = None
    line_number: Optional[int] = None


@dataclass
class DatabaseSchema:
    """Complete database schema."""

    name: str
    tables: Dict[str, Table] = field(default_factory=dict)
    stored_procedures: Dict[str, StoredProcedure] = field(default_factory=dict)
    views: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    sequences: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    sql_statements: List[SQLStatement] = field(default_factory=list)
    datawindows: Dict[str, Dict[str, Any]] = field(default_factory=dict)


class SQLParser:
    """Parse SQL statements and extract schema information."""

    def __init__(self):
        """Initialize SQL parser."""
        self.patterns = self._compile_patterns()

    def _compile_patterns(self) -> Dict[str, re.Pattern]:
        """Compile regex patterns for SQL parsing.

        Returns:
            Dictionary of compiled patterns
        """
        return {
            "select": re.compile(
                r"SELECT\s+(.+?)\s+FROM\s+(\w+(?:\.\w+)?)", re.IGNORECASE | re.DOTALL
            ),
            "insert": re.compile(
                r"INSERT\s+INTO\s+(\w+(?:\.\w+)?)\s*\(([^)]+)\)", re.IGNORECASE
            ),
            "update": re.compile(
                r"UPDATE\s+(\w+(?:\.\w+)?)\s+SET\s+(.+?)(?:\s+WHERE|$)",
                re.IGNORECASE | re.DOTALL,
            ),
            "delete": re.compile(r"DELETE\s+FROM\s+(\w+(?:\.\w+)?)", re.IGNORECASE),
            "create_table": re.compile(
                r"CREATE\s+TABLE\s+(\w+(?:\.\w+)?)\s*\((.+?)\)",
                re.IGNORECASE | re.DOTALL,
            ),
            "join": re.compile(
                r"(?:INNER|LEFT|RIGHT|FULL)?\s*JOIN\s+(\w+(?:\.\w+)?)", re.IGNORECASE
            ),
            "where": re.compile(
                r"WHERE\s+(.+?)(?:\s+ORDER\s+BY|\s+GROUP\s+BY|$)",
                re.IGNORECASE | re.DOTALL,
            ),
        }

    def parse_sql(self, sql: str, source_file: Optional[str] = None) -> SQLStatement:
        """Parse a SQL statement.

        Args:
            sql: SQL statement to parse
            source_file: Source file containing the SQL

        Returns:
            Parsed SQL statement
        """
        sql = sql.strip()
        statement = SQLStatement(
            type=self._determine_type(sql),
            statement=sql,
            source_file=source_file,
        )

        # Extract tables
        statement.tables = self._extract_tables(sql)

        # Extract columns
        statement.columns = self._extract_columns(sql)

        # Extract conditions
        if "WHERE" in sql.upper():
            where_match = self.patterns["where"].search(sql)
            if where_match:
                statement.conditions.append(where_match.group(1).strip())

        return statement

    def _determine_type(self, sql: str) -> SQLType:
        """Determine SQL statement type.

        Args:
            sql: SQL statement

        Returns:
            SQL type
        """
        sql_upper = sql.upper().strip()

        for sql_type in SQLType:
            if sql_upper.startswith(sql_type.value):
                return sql_type

        return SQLType.UNKNOWN

    def _extract_tables(self, sql: str) -> List[str]:
        """Extract table names from SQL.

        Args:
            sql: SQL statement

        Returns:
            List of table names
        """
        tables = []

        # FROM clause
        from_match = re.search(r"FROM\s+(\w+(?:\.\w+)?)", sql, re.IGNORECASE)
        if from_match:
            tables.append(from_match.group(1))

        # JOIN clauses
        for join_match in self.patterns["join"].finditer(sql):
            tables.append(join_match.group(1))

        # INSERT INTO
        insert_match = self.patterns["insert"].search(sql)
        if insert_match:
            tables.append(insert_match.group(1))

        # UPDATE
        update_match = self.patterns["update"].search(sql)
        if update_match:
            tables.append(update_match.group(1))

        return list(set(tables))  # Remove duplicates

    def _extract_columns(self, sql: str) -> List[str]:
        """Extract column names from SQL.

        Args:
            sql: SQL statement

        Returns:
            List of column names
        """
        columns = []

        # SELECT columns
        select_match = self.patterns["select"].search(sql)
        if select_match:
            select_list = select_match.group(1)
            if select_list.strip() != "*":
                # Parse column list
                for col in select_list.split(","):
                    col = col.strip()
                    # Remove aliases
                    col = re.sub(r"\s+AS\s+\w+", "", col, flags=re.IGNORECASE)
                    # Extract column name
                    if "." in col:
                        col = col.split(".")[-1]
                    columns.append(col)

        # INSERT columns
        insert_match = self.patterns["insert"].search(sql)
        if insert_match:
            col_list = insert_match.group(2)
            for col in col_list.split(","):
                columns.append(col.strip())

        return list(set(columns))  # Remove duplicates


class SchemaExtractor:
    """Extract database schema from PowerBuilder code."""

    def __init__(self):
        """Initialize schema extractor."""
        self.sql_parser = SQLParser()
        self.schema = DatabaseSchema(name="extracted_schema")

    def extract_from_directory(self, directory: Path) -> DatabaseSchema:
        """Extract schema from all files in directory.

        Args:
            directory: Directory to process

        Returns:
            Extracted database schema
        """
        logger.info("Extracting database schema from %s", directory)

        for file_path in directory.rglob("*"):
            if file_path.is_file() and file_path.suffix in [
                ".sru",
                ".srw",
                ".srm",
                ".srd",
                ".pbl",
                ".sql",
            ]:
                self._process_file(file_path)

        # Analyze relationships
        self._analyze_relationships()

        logger.info(
            "Extracted schema: %d tables, %d procedures, %d SQL statements",
            len(self.schema.tables),
            len(self.schema.stored_procedures),
            len(self.schema.sql_statements),
        )

        return self.schema

    def _process_file(self, file_path: Path) -> None:
        """Process a single file for schema information.

        Args:
            file_path: File to process
        """
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")

            # Extract DataWindows
            self._extract_datawindows(content, file_path)

            # Extract SQL statements
            self._extract_sql_statements(content, file_path)

            # Extract stored procedure calls
            self._extract_procedure_calls(content, file_path)

        except Exception as e:
            logger.warning("Failed to process %s: %s", file_path, e)

    def _extract_datawindows(self, content: str, file_path: Path) -> None:
        """Extract DataWindow definitions.

        Args:
            content: File content
            file_path: Source file path
        """
        # Pattern for DataWindow SQL
        pattern = r"datawindow\s*\(.*?sql\s*=\s*['\"](.+?)['\"].*?\)"
        matches = re.finditer(pattern, content, re.IGNORECASE | re.DOTALL)

        for match in matches:
            sql = match.group(1)
            # Parse the SQL
            statement = self.sql_parser.parse_sql(sql, str(file_path))
            self.schema.sql_statements.append(statement)

            # Add tables to schema
            for table_name in statement.tables:
                if table_name not in self.schema.tables:
                    self.schema.tables[table_name] = Table(name=table_name)

    def _extract_sql_statements(self, content: str, file_path: Path) -> None:
        """Extract embedded SQL statements.

        Args:
            content: File content
            file_path: Source file path
        """
        # Patterns for embedded SQL
        patterns = [
            r"EXECUTE\s+IMMEDIATE\s+['\"](.+?)['\"]",
            r"SELECT\s+.+?\s+FROM\s+.+?(?:;|$)",
            r"INSERT\s+INTO\s+.+?(?:;|$)",
            r"UPDATE\s+.+?\s+SET\s+.+?(?:;|$)",
            r"DELETE\s+FROM\s+.+?(?:;|$)",
        ]

        for pattern in patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE | re.DOTALL)
            for match in matches:
                sql = match.group(0) if "EXECUTE" not in pattern else match.group(1)
                statement = self.sql_parser.parse_sql(sql, str(file_path))
                self.schema.sql_statements.append(statement)

                # Add tables to schema
                for table_name in statement.tables:
                    if table_name not in self.schema.tables:
                        self.schema.tables[table_name] = Table(name=table_name)

    def _extract_procedure_calls(self, content: str, file_path: Path) -> None:
        """Extract stored procedure calls.

        Args:
            content: File content
            file_path: Source file path
        """
        # Pattern for stored procedure calls
        patterns = [
            r"EXECUTE\s+(\w+)(?:\s*\(|;)",
            r"CALL\s+(\w+)(?:\s*\(|;)",
            r"{\s*call\s+(\w+).*?}",
        ]

        for pattern in patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                proc_name = match.group(1)
                if proc_name not in self.schema.stored_procedures:
                    self.schema.stored_procedures[proc_name] = StoredProcedure(
                        name=proc_name
                    )
                self.schema.stored_procedures[proc_name].called_by.append(
                    str(file_path)
                )

    def _analyze_relationships(self) -> None:
        """Analyze and infer table relationships."""
        # Infer foreign keys from column names
        for table_name, table in self.schema.tables.items():
            for column in table.columns:
                # Look for ID columns that might be foreign keys
                if column.name.endswith("_id") or column.name.endswith("_ID"):
                    # Try to find referenced table
                    ref_table = column.name[:-3]  # Remove _id suffix
                    if ref_table in self.schema.tables:
                        # Create foreign key
                        fk = ForeignKey(
                            name=f"fk_{table_name}_{column.name}",
                            columns=[column.name],
                            reference_table=ref_table,
                            reference_columns=["id"],
                        )
                        table.foreign_keys.append(fk)
                        column.foreign_key = ref_table

    def export_to_sql(self, output_path: Path, dialect: str = "postgresql") -> None:
        """Export schema as SQL DDL.

        Args:
            output_path: Output file path
            dialect: SQL dialect (postgresql, mysql, sqlite)
        """
        ddl = []

        # Generate CREATE TABLE statements
        for table in self.schema.tables.values():
            ddl.append(self._generate_create_table(table, dialect))

        # Write to file
        output_path.write_text("\n\n".join(ddl))
        logger.info("Exported schema DDL to %s", output_path)

    def _generate_create_table(self, table: Table, dialect: str) -> str:
        """Generate CREATE TABLE statement.

        Args:
            table: Table definition
            dialect: SQL dialect

        Returns:
            CREATE TABLE statement
        """
        lines = [f"CREATE TABLE {table.full_name} ("]

        # Columns
        col_defs = []
        for column in table.columns:
            col_def = f"    {column.name} {column.data_type.value}"

            if column.length:
                col_def += f"({column.length})"
            elif column.precision:
                col_def += f"({column.precision}"
                if column.scale:
                    col_def += f", {column.scale}"
                col_def += ")"

            if not column.nullable:
                col_def += " NOT NULL"

            if column.default_value:
                col_def += f" DEFAULT {column.default_value}"

            if column.primary_key:
                col_def += " PRIMARY KEY"

            col_defs.append(col_def)

        lines.append(",\n".join(col_defs))
        lines.append(");")

        return "\n".join(lines)

    def export_to_json(self, output_path: Path) -> None:
        """Export schema as JSON.

        Args:
            output_path: Output file path
        """
        schema_dict = {
            "name": self.schema.name,
            "tables": {
                name: {
                    "columns": [
                        {
                            "name": col.name,
                            "type": col.data_type.value,
                            "nullable": col.nullable,
                            "primary_key": col.primary_key,
                            "foreign_key": col.foreign_key,
                        }
                        for col in table.columns
                    ],
                    "foreign_keys": [
                        {
                            "columns": fk.columns,
                            "references": fk.reference_table,
                        }
                        for fk in table.foreign_keys
                    ],
                }
                for name, table in self.schema.tables.items()
            },
            "stored_procedures": {
                name: {
                    "parameters": proc.parameters,
                    "called_by": proc.called_by,
                }
                for name, proc in self.schema.stored_procedures.items()
            },
            "sql_statements": [
                {
                    "type": stmt.type.value,
                    "tables": stmt.tables,
                    "columns": stmt.columns,
                    "source": stmt.source_file,
                }
                for stmt in self.schema.sql_statements
            ],
        }

        with output_path.open("w") as f:
            json.dump(schema_dict, f, indent=2)

        logger.info("Exported schema JSON to %s", output_path)
