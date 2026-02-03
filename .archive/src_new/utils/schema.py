"""Database Schema Extraction - Extract schema from PowerBuilder applications.

This module provides database schema extraction from PowerBuilder source files,
including DataWindows, SQL statements, and database operations.
"""

import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from src_new._patterns import FileHandler

logger = logging.getLogger(__name__)


class SchemaExtractor:
    """Extract database schema from PowerBuilder files."""

    def __init__(self):
        """Initialize schema extractor."""
        self.schema_data = {
            "extraction_date": "",
            "project_directory": "",
            "tables": {},
            "datawindows": {},
            "sql_statements": [],
            "functions": {},
            "statistics": {
                "files_processed": 0,
                "tables_found": 0,
                "datawindows_found": 0,
                "sql_statements_found": 0,
                "functions_found": 0,
            },
        }

    def extract_schema(
        self,
        project_dir: Path,
        output_dir: Path,
        output_format: str = "markdown",
        include_flows: bool = False,
    ) -> Dict[str, Any]:
        """Extract database schema from PowerBuilder project.

        Args:
            project_dir: Project directory
            output_dir: Output directory
            output_format: Output format (markdown/html/json)
            include_flows: Include data flow analysis

        Returns:
            Extracted schema data
        """
        self.schema_data["extraction_date"] = datetime.now().isoformat()
        self.schema_data["project_directory"] = str(project_dir)

        # Process PowerBuilder files
        pb_files = self._find_pb_files(project_dir)

        for file_path in pb_files:
            self._analyze_file(file_path)
            self.schema_data["statistics"]["files_processed"] += 1

        # Generate documentation
        self._generate_documentation(output_dir, output_format)

        return self.schema_data

    def _find_pb_files(self, project_dir: Path) -> List[Path]:
        """Find PowerBuilder source files.

        Args:
            project_dir: Project directory

        Returns:
            List of PowerBuilder files
        """
        patterns = ["*.sru", "*.srw", "*.srd", "*.srm", "*.srf", "*.srs"]
        files = []

        for pattern in patterns:
            files.extend(project_dir.rglob(pattern))

        return files

    def _analyze_file(self, file_path: Path) -> None:
        """Analyze a PowerBuilder file for database elements.

        Args:
            file_path: File to analyze
        """
        try:
            file_handler = FileHandler()
            content = file_handler.read_text(file_path)

            # Extract based on file type
            if file_path.suffix.lower() == ".srd":
                self._extract_datawindow_info(file_path, content)
            else:
                self._extract_sql_statements(file_path, content)
                self._extract_function_info(file_path, content)

        except Exception as e:
            logger.warning(f"Failed to analyze {file_path}: {e}")

    def _extract_datawindow_info(self, file_path: Path, content: str) -> None:
        """Extract DataWindow information.

        Args:
            file_path: DataWindow file path
            content: File content
        """
        dw_name = file_path.stem

        # Extract SQL
        sql_match = re.search(
            r'retrieve\s*=\s*"([^"]+)"', content, re.IGNORECASE | re.DOTALL
        )

        if sql_match:
            sql = sql_match.group(1)
            tables = self._extract_table_names(sql)

            self.datawindows[dw_name] = {
                "file_path": str(file_path),
                "sql": sql,
                "tables": tables,
            }

            # Update table references
            for table in tables:
                if table not in self.schema_data["tables"]:
                    self.schema_data["tables"][table] = {
                        "columns": set(),
                        "referenced_by": [],
                    }
                self.schema_data["tables"][table]["referenced_by"].append(dw_name)

            self.schema_data["statistics"]["datawindows_found"] += 1

    def _extract_sql_statements(self, file_path: Path, content: str) -> None:
        """Extract SQL statements from source.

        Args:
            file_path: Source file path
            content: File content
        """
        # SQL patterns
        sql_patterns = [
            r"(SELECT\s+.*?FROM\s+.*?)(?:;|\n\n|\Z)",
            r"(INSERT\s+INTO\s+.*?)(?:;|\n\n|\Z)",
            r"(UPDATE\s+.*?SET\s+.*?)(?:;|\n\n|\Z)",
            r"(DELETE\s+FROM\s+.*?)(?:;|\n\n|\Z)",
            r'EXECUTE\s+IMMEDIATE\s*["\']([^"\']+)["\']',
        ]

        for pattern in sql_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE | re.DOTALL)

            for match in matches:
                sql = match.group(1) if match.lastindex else match.group(0)
                sql = sql.strip()

                if len(sql) > 10:  # Minimum viable SQL
                    tables = self._extract_table_names(sql)
                    statement_type = self._determine_sql_type(sql)

                    self.schema_data["sql_statements"].append(
                        {
                            "file_path": str(file_path),
                            "statement": sql,
                            "statement_type": statement_type,
                            "tables_referenced": tables,
                        }
                    )

                    self.schema_data["statistics"]["sql_statements_found"] += 1

                    # Update table references
                    for table in tables:
                        if table not in self.schema_data["tables"]:
                            self.schema_data["tables"][table] = {
                                "columns": set(),
                                "referenced_by": [],
                            }

    def _extract_function_info(self, file_path: Path, content: str) -> None:
        """Extract function database operations.

        Args:
            file_path: Source file path
            content: File content
        """
        # Find functions with database operations
        function_pattern = r"(public|private|protected)?\s*function\s+(\w+)\s*\([^)]*\).*?end\s+function"
        matches = re.finditer(function_pattern, content, re.IGNORECASE | re.DOTALL)

        for match in matches:
            function_name = match.group(2)
            function_body = match.group(0)

            # Check for database operations
            db_ops = []
            if re.search(r"SELECT|INSERT|UPDATE|DELETE", function_body, re.IGNORECASE):
                db_ops.append("SQL")
            if re.search(r"COMMIT|ROLLBACK", function_body, re.IGNORECASE):
                db_ops.append("Transaction")
            if re.search(r"datawindow", function_body, re.IGNORECASE):
                db_ops.append("DataWindow")

            if db_ops:
                self.schema_data["functions"][function_name] = {
                    "file_path": str(file_path),
                    "operations": db_ops,
                    "tables": self._extract_table_names(function_body),
                }
                self.schema_data["statistics"]["functions_found"] += 1

    def _extract_table_names(self, sql: str) -> List[str]:
        """Extract table names from SQL.

        Args:
            sql: SQL statement

        Returns:
            List of table names
        """
        tables = []

        # Clean SQL
        sql = re.sub(r"--.*$", "", sql, flags=re.MULTILINE)  # Remove comments
        sql = re.sub(r"/\*.*?\*/", "", sql, flags=re.DOTALL)  # Remove block comments

        # Extract table names
        patterns = [
            r"FROM\s+(\w+)",
            r"JOIN\s+(\w+)",
            r"INTO\s+(\w+)",
            r"UPDATE\s+(\w+)",
            r"TABLE\s+(\w+)",
        ]

        for pattern in patterns:
            matches = re.findall(pattern, sql, re.IGNORECASE)
            tables.extend(matches)

        # Remove duplicates and system tables
        tables = list(set(tables))
        tables = [t for t in tables if not t.lower().startswith("sys")]

        return tables

    def _determine_sql_type(self, sql: str) -> str:
        """Determine SQL statement type.

        Args:
            sql: SQL statement

        Returns:
            Statement type
        """
        sql_upper = sql.upper().strip()

        if sql_upper.startswith("SELECT"):
            return "SELECT"
        elif sql_upper.startswith("INSERT"):
            return "INSERT"
        elif sql_upper.startswith("UPDATE"):
            return "UPDATE"
        elif sql_upper.startswith("DELETE"):
            return "DELETE"
        elif sql_upper.startswith("CREATE"):
            return "DDL"
        elif sql_upper.startswith("ALTER"):
            return "DDL"
        elif sql_upper.startswith("DROP"):
            return "DDL"
        else:
            return "OTHER"

    def _generate_documentation(self, output_dir: Path, output_format: str) -> None:
        """Generate schema documentation.

        Args:
            output_dir: Output directory
            output_format: Format (markdown/html/json)
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        file_handler = FileHandler()

        # Always save raw JSON
        json_file = output_dir / "database_schema.json"

        # Convert sets to lists for JSON serialization
        json_data = self.schema_data.copy()
        for table_data in json_data["tables"].values():
            if isinstance(table_data.get("columns"), set):
                table_data["columns"] = list(table_data["columns"])

        file_handler.write_json(json_file, json_data, indent=2)

        # Generate formatted documentation
        if output_format.lower() == "markdown":
            self._generate_markdown(output_dir)
        elif output_format.lower() == "html":
            self._generate_html(output_dir)

    def _generate_markdown(self, output_dir: Path) -> None:
        """Generate Markdown documentation.

        Args:
            output_dir: Output directory
        """
        file_handler = FileHandler()
        md_file = output_dir / "database_schema.md"

        content = []
        content.append("# PowerBuilder Database Schema Documentation\n")
        content.append(f"**Generated:** {self.schema_data['extraction_date']}\n")
        content.append(f"**Project:** {self.schema_data['project_directory']}\n")

        # Statistics
        stats = self.schema_data["statistics"]
        content.append("\n## Summary Statistics\n")
        content.append(f"- Files Processed: {stats['files_processed']}")
        content.append(f"- Tables Found: {len(self.schema_data['tables'])}")
        content.append(f"- DataWindows Found: {stats['datawindows_found']}")
        content.append(f"- SQL Statements: {stats['sql_statements_found']}")
        content.append(f"- Functions with DB Ops: {stats['functions_found']}")

        # Tables
        if self.schema_data["tables"]:
            content.append("\n## Database Tables\n")
            for table_name, table_info in self.schema_data["tables"].items():
                content.append(f"\n### {table_name}")
                if table_info.get("referenced_by"):
                    content.append("\n**Referenced by:**")
                    for ref in table_info["referenced_by"]:
                        content.append(f"- {ref}")

        # DataWindows
        if self.datawindows:
            content.append("\n## DataWindows\n")
            for dw_name, dw_info in self.datawindows.items():
                content.append(f"\n### {dw_name}")
                content.append(f"**File:** {dw_info['file_path']}")
                if dw_info.get("tables"):
                    content.append("**Tables:** " + ", ".join(dw_info["tables"]))

        # SQL Statements (first 20)
        if self.schema_data["sql_statements"]:
            content.append("\n## SQL Statements (Sample)\n")
            for i, sql_info in enumerate(self.schema_data["sql_statements"][:20], 1):
                content.append(f"\n### Statement {i} ({sql_info['statement_type']})")
                content.append(f"**File:** {sql_info['file_path']}")
                content.append("```sql")
                content.append(sql_info["statement"])
                content.append("```")
                if sql_info.get("tables_referenced"):
                    content.append(
                        "**Tables:** " + ", ".join(sql_info["tables_referenced"])
                    )

        file_handler.write_text(md_file, "\n".join(content))

    def _generate_html(self, output_dir: Path) -> None:
        """Generate HTML documentation.

        Args:
            output_dir: Output directory
        """
        file_handler = FileHandler()
        html_file = output_dir / "database_schema.html"

        html = []
        html.append("""<!DOCTYPE html>
<html>
<head>
    <title>PowerBuilder Database Schema</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        h1, h2, h3 { color: #333; }
        pre { background: #f5f5f5; padding: 10px; border-radius: 5px; overflow-x: auto; }
        .stats { background: #e9f4ff; padding: 15px; border-radius: 5px; }
        .table-info { margin: 20px 0; border-left: 3px solid #007acc; padding-left: 15px; }
        code { background: #f0f0f0; padding: 2px 4px; border-radius: 3px; }
    </style>
</head>
<body>
""")

        html.append("<h1>PowerBuilder Database Schema Documentation</h1>")
        html.append(
            f"<p><strong>Generated:</strong> {self.schema_data['extraction_date']}</p>"
        )
        html.append(
            f"<p><strong>Project:</strong> {self.schema_data['project_directory']}</p>"
        )

        # Statistics
        stats = self.schema_data["statistics"]
        html.append('<div class="stats">')
        html.append("<h2>Summary Statistics</h2>")
        html.append("<ul>")
        html.append(f"<li>Files Processed: {stats['files_processed']}</li>")
        html.append(f"<li>Tables Found: {len(self.schema_data['tables'])}</li>")
        html.append(f"<li>DataWindows: {stats['datawindows_found']}</li>")
        html.append(f"<li>SQL Statements: {stats['sql_statements_found']}</li>")
        html.append(
            f"<li>Functions with DB Operations: {stats['functions_found']}</li>"
        )
        html.append("</ul>")
        html.append("</div>")

        # Tables
        if self.schema_data["tables"]:
            html.append("<h2>Database Tables</h2>")
            for table_name, table_info in self.schema_data["tables"].items():
                html.append('<div class="table-info">')
                html.append(f"<h3>{table_name}</h3>")
                if table_info.get("referenced_by"):
                    html.append("<p><strong>Referenced by:</strong></p>")
                    html.append("<ul>")
                    for ref in table_info["referenced_by"]:
                        html.append(f"<li>{ref}</li>")
                    html.append("</ul>")
                html.append("</div>")

        html.append("</body></html>")

        file_handler.write_text(html_file, "\n".join(html))
