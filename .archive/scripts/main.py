#!/usr/bin/env python3
"""Main entry point for the PowerBuilder reverse engineering tool (PowerRebuilder).

This script orchestrates the entire pipeline for converting PowerBuilder applications
to modern web applications through a SEQUENTIAL five-stage process:

1. Extract: Extracts compiled P-code files (.fun) from PowerBuilder binary files (PBL/PBD)

2. Decompile: Converts P-code bytecode (.fun) to PowerBuilder source code (.sru)
   - MUST run BEFORE Parse because Parse requires source code, not bytecode

3. Parse: Processes PowerBuilder source files (.sru) into Abstract Syntax Trees (ASTs)
   - Takes decompiled source as input, outputs structured AST JSON

4. Model: Builds semantic models from parsed ASTs
   - Transforms AST JSON into typed object models

5. Generate: Produces modern applications from semantic models:
   - Backend: Python/Litestar API services
   - Frontend: Flutter/React/Astro applications

The CLI supports both individual pipeline steps and end-to-end processing.
Command-line interface is provided through Click.
"""

import json
import logging
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, BinaryIO

import click

from src.extract.unified_extract import Library

# Core infrastructure and coordination imports
from src.domain.models import PipelineStage

# Note: binary_to_readable_format and extract_database_schema functions
# may need to be implemented or imported from other modules


# Simple implementations of utility functions
def get_logger(name: str) -> logging.Logger:
    """Get a logger instance."""
    return logging.getLogger(name)


def setup_logging(level: str = "INFO", logfile: str | None = None):
    """Setup basic logging configuration."""
    handlers = [logging.StreamHandler()]
    if logfile:
        handlers.append(logging.FileHandler(logfile))

    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=handlers,
    )


def check_and_prepare_output_directory(
    output_path: Path, overwrite: bool = False, dry_run: bool = False
) -> tuple[Path, bool]:
    """Check and prepare output directory."""
    if dry_run:
        return output_path, True

    if output_path.exists():
        if not overwrite and any(output_path.iterdir()):
            # Directory exists and has content
            click.echo(
                f"Output directory {output_path} already exists and contains files."
            )
            click.echo("Use --overwrite flag to overwrite existing files.")
            return output_path, False
    else:
        output_path.mkdir(parents=True, exist_ok=True)

    return output_path, True


def binary_to_readable_format(input_path: Path, output_path: Path) -> bool:
    """Convert PowerBuilder binary files to readable text format.

    This function handles various PowerBuilder binary file formats:
    - PBL/PBD files: Extracts and displays structure
    - P-code files: Shows bytecode in readable format
    - Other binary files: Displays as hex dump with text interpretation

    Args:
        input_path: Path to input binary file
        output_path: Path to output text file

    Returns:
        True if conversion was successful, False otherwise
    """
    try:
        # Check if input file exists and is readable
        if not input_path.exists() or not input_path.is_file():
            logger.error("Input file does not exist or is not a file: %s", input_path)
            return False

        # Get file size for processing strategy
        file_size = input_path.stat().st_size
        if file_size == 0:
            logger.warning("Input file is empty: %s", input_path)
            output_path.write_text("Empty file\n", encoding="utf-8")
            return True

        # Determine file type and processing strategy
        file_ext = input_path.suffix.lower()

        with open(input_path, "rb") as input_file:
            # Read header to determine file type
            header = input_file.read(min(1024, file_size))
            input_file.seek(0)

            with open(output_path, "w", encoding="utf-8") as output_file:
                output_file.write("PowerBuilder Binary File Analysis\n")
                output_file.write("=" * 50 + "\n\n")
                output_file.write(f"File: {input_path}\n")
                output_file.write(f"Size: {file_size:,} bytes\n")
                output_file.write(f"Extension: {file_ext}\n\n")

                # Check for PowerBuilder signatures
                if file_ext in [".pbl", ".pbd"] or any(
                    header.startswith(sig) for sig in [b"PBL", b"PBD", b"HDR*"]
                ):
                    _convert_powerbuilder_library(input_file, output_file, file_size)
                elif file_ext in [".fun", ".win", ".udo", ".men"]:
                    _convert_pcode_file(input_file, output_file, file_size)
                else:
                    _convert_generic_binary(input_file, output_file, file_size)

        logger.info(
            "Successfully converted %s to readable format: %s", input_path, output_path
        )
        return True

    except Exception as e:
        logger.exception("Failed to convert binary file to readable format: %s", e)
        return False


def _convert_powerbuilder_library(
    input_file: BinaryIO, output_file: Any, file_size: int
) -> None:
    """Convert PowerBuilder library file to readable format."""
    output_file.write("PowerBuilder Library File (PBL/PBD)\n")
    output_file.write("-" * 40 + "\n\n")

    try:
        # Read and analyze header
        header_data = input_file.read(min(512, file_size))

        output_file.write("Header Analysis:\n")
        if len(header_data) >= 4:
            signature = header_data[:4]
            output_file.write(f"  Signature: {signature}\n")

            # Try to decode as text
            try:
                sig_text = signature.decode("ascii", errors="ignore")
                output_file.write(f"  Signature (text): '{sig_text}'\n")
            except:
                pass

        output_file.write("  Header (first 64 bytes):\n")
        _write_hex_dump(output_file, header_data[:64])

        # Try to use Library class if available
        try:
            from src.extract.unified_extract import Library

            input_file.seek(0)
            temp_path = Path(input_file.name)

            with Library(temp_path) as lib:
                info = lib.get_info()
                output_file.write("\nLibrary Information:\n")
                for key, value in info.items():
                    output_file.write(f"  {key}: {value}\n")

        except Exception as e:
            output_file.write(f"\nCould not analyze library structure: {e}\n")

    except Exception as e:
        output_file.write(f"Error analyzing PowerBuilder library: {e}\n")


def _convert_pcode_file(input_file: BinaryIO, output_file: Any, file_size: int) -> None:
    """Convert P-code file to readable format."""
    output_file.write("PowerBuilder P-code File\n")
    output_file.write("-" * 30 + "\n\n")

    try:
        # Read entire file for P-code analysis
        data = input_file.read(file_size)

        output_file.write("P-code Structure Analysis:\n")
        output_file.write(f"  Total size: {len(data)} bytes\n")

        # Look for common P-code patterns
        if len(data) >= 4:
            output_file.write(f"  First 4 bytes: {data[:4].hex()}\n")

        # Show hex dump of first 256 bytes
        output_file.write("\nFirst 256 bytes (hex dump):\n")
        _write_hex_dump(output_file, data[:256])

        # Try to find text strings
        output_file.write("\nText strings found:\n")
        _extract_text_strings(output_file, data)

    except Exception as e:
        output_file.write(f"Error analyzing P-code file: {e}\n")


def _convert_generic_binary(
    input_file: BinaryIO, output_file: Any, file_size: int
) -> None:
    """Convert generic binary file to readable format."""
    output_file.write("Generic Binary File\n")
    output_file.write("-" * 20 + "\n\n")

    try:
        # Read in chunks for large files
        chunk_size = min(4096, file_size)
        data = input_file.read(chunk_size)

        output_file.write(f"Hex dump (first {len(data)} bytes):\n")
        _write_hex_dump(output_file, data)

        output_file.write("\nText strings found:\n")
        _extract_text_strings(output_file, data)

        if file_size > chunk_size:
            output_file.write(
                f"\n... file continues for {file_size - chunk_size} more bytes\n"
            )

    except Exception as e:
        output_file.write(f"Error analyzing binary file: {e}\n")


def _write_hex_dump(output_file: Any, data: bytes, bytes_per_line: int = 16) -> None:
    """Write hex dump with ASCII interpretation."""
    for i in range(0, len(data), bytes_per_line):
        chunk = data[i : i + bytes_per_line]
        hex_part = " ".join(f"{b:02x}" for b in chunk)
        ascii_part = "".join(chr(b) if 32 <= b <= 126 else "." for b in chunk)

        output_file.write(f"  {i:08x}: {hex_part:<48} |{ascii_part}|\n")


def _extract_text_strings(output_file: Any, data: bytes, min_length: int = 4) -> None:
    """Extract readable text strings from binary data."""
    import re

    # Find ASCII strings
    ascii_strings = re.findall(
        rb"[\x20-\x7e]{" + str(min_length).encode() + rb",}", data
    )

    # Find Unicode strings (UTF-16 LE)
    unicode_strings = re.findall(
        rb"(?:[\x20-\x7e]\x00){" + str(min_length).encode() + rb",}", data
    )

    if ascii_strings:
        output_file.write("  ASCII strings:\n")
        for i, string in enumerate(ascii_strings[:20]):  # Limit to first 20
            try:
                decoded = string.decode("ascii", errors="ignore")
                output_file.write(f"    {i + 1}: '{decoded}'\n")
            except:
                pass

    if unicode_strings:
        output_file.write("  Unicode strings:\n")
        for i, string in enumerate(unicode_strings[:20]):  # Limit to first 20
            try:
                decoded = string.decode("utf-16-le", errors="ignore")
                output_file.write(f"    {i + 1}: '{decoded}'\n")
            except:
                pass

    if not ascii_strings and not unicode_strings:
        output_file.write("  No readable text strings found\n")


def extract_database_schema(
    project_dir: str, output_dir: str, output_format: str = "markdown"
) -> None:
    """Extract and document database schema from PowerBuilder source files.

    This function analyzes PowerBuilder source files to extract database-related information:
    - DataWindow definitions and their associated tables/columns
    - SQL statements embedded in functions and events
    - Table relationships inferred from foreign key patterns
    - Database operations (SELECT, INSERT, UPDATE, DELETE)
    - Business logic functions that interact with data

    Args:
        project_dir: Directory containing PowerBuilder source files
        output_dir: Directory to write schema documentation
        output_format: Output format ('markdown', 'html', 'json')
    """
    try:
        from datetime import datetime
        from pathlib import Path

        project_path = Path(project_dir)
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        logger.info(
            "Extracting database schema from PowerBuilder project: %s", project_path
        )

        # Initialize schema data structure
        schema_data = {
            "extraction_date": datetime.now().isoformat(),
            "project_directory": str(project_path),
            "tables": {},
            "datawindows": {},
            "sql_statements": [],
            "functions": {},
            "relationships": [],
            "statistics": {
                "files_processed": 0,
                "tables_found": 0,
                "datawindows_found": 0,
                "sql_statements_found": 0,
                "functions_found": 0,
            },
        }

        # Find all PowerBuilder source files
        pb_files = []
        for pattern in [
            "**/*.sru",
            "**/*.srw",
            "**/*.srf",
            "**/*.srm",
            "**/*.srd",
            "**/*.sra",
        ]:
            pb_files.extend(project_path.glob(pattern))

        if not pb_files:
            logger.warning("No PowerBuilder source files found in %s", project_path)

        # Process each file
        for file_path in pb_files:
            try:
                _analyze_powerbuilder_file(file_path, schema_data)
                schema_data["statistics"]["files_processed"] += 1
            except Exception as e:
                logger.warning("Error processing file %s: %s", file_path, e)

        # Update final statistics
        schema_data["statistics"]["tables_found"] = len(schema_data["tables"])
        schema_data["statistics"]["datawindows_found"] = len(schema_data["datawindows"])
        schema_data["statistics"]["sql_statements_found"] = len(
            schema_data["sql_statements"]
        )
        schema_data["statistics"]["functions_found"] = len(schema_data["functions"])

        # Generate output files
        _generate_schema_documentation(schema_data, output_path, output_format)

        logger.info("Database schema extraction completed successfully")
        logger.info(
            "Processed %d files, found %d tables, %d DataWindows, %d SQL statements",
            schema_data["statistics"]["files_processed"],
            schema_data["statistics"]["tables_found"],
            schema_data["statistics"]["datawindows_found"],
            schema_data["statistics"]["sql_statements_found"],
        )

    except Exception as e:
        logger.exception("Failed to extract database schema: %s", e)
        raise


def _analyze_powerbuilder_file(file_path: Path, schema_data: dict[str, Any]) -> None:
    """Analyze a single PowerBuilder source file for database schema information."""
    try:
        with open(file_path, encoding="utf-8", errors="ignore") as f:
            content = f.read()

        file_type = file_path.suffix.lower()

        # Extract DataWindow definitions
        if file_type == ".srd" or "datawindow(" in content.lower():
            _extract_datawindow_info(file_path, content, schema_data)

        # Extract SQL statements
        _extract_sql_statements(file_path, content, schema_data)

        # Extract function definitions
        _extract_function_info(file_path, content, schema_data)

        # Extract table references
        _extract_table_references(file_path, content, schema_data)

    except Exception as e:
        logger.debug("Error analyzing file %s: %s", file_path, e)


def _extract_datawindow_info(
    file_path: Path, content: str, schema_data: dict[str, Any]
) -> None:
    """Extract DataWindow definitions and associated table information."""
    import re

    # Look for datawindow definitions
    dw_pattern = r"datawindow\s*\(\s*([^)]+)\)"
    matches = re.finditer(dw_pattern, content, re.IGNORECASE | re.DOTALL)

    for match in matches:
        dw_definition = match.group(1)
        dw_name = file_path.stem

        # Extract table information from DataWindow
        table_pattern = r'table\s*=\s*["\']([^"\']+)["\']'
        table_matches = re.findall(table_pattern, dw_definition, re.IGNORECASE)

        # Extract column information
        column_pattern = r'column\s*=\s*["\']([^"\']+)["\']'
        column_matches = re.findall(column_pattern, dw_definition, re.IGNORECASE)

        if table_matches or column_matches:
            schema_data["datawindows"][dw_name] = {
                "file_path": str(file_path),
                "tables": table_matches,
                "columns": column_matches,
                "definition": dw_definition[:500]
                + ("..." if len(dw_definition) > 500 else ""),
            }

            # Add tables to schema
            for table in table_matches:
                if table not in schema_data["tables"]:
                    schema_data["tables"][table] = {
                        "name": table,
                        "columns": set(),
                        "referenced_by": [],
                        "source_files": [],
                    }
                schema_data["tables"][table]["referenced_by"].append(
                    f"DataWindow: {dw_name}"
                )
                schema_data["tables"][table]["source_files"].append(str(file_path))


def _extract_sql_statements(
    file_path: Path, content: str, schema_data: dict[str, Any]
) -> None:
    """Extract SQL statements from PowerBuilder source code."""
    import re

    # Common SQL statement patterns
    sql_patterns = [
        r"SELECT\s+[^;]+;?",
        r"INSERT\s+INTO\s+[^;]+;?",
        r"UPDATE\s+[^;]+;?",
        r"DELETE\s+FROM\s+[^;]+;?",
        r"CREATE\s+TABLE\s+[^;]+;?",
        r"ALTER\s+TABLE\s+[^;]+;?",
        r"DROP\s+TABLE\s+[^;]+;?",
    ]

    for pattern in sql_patterns:
        matches = re.finditer(
            pattern, content, re.IGNORECASE | re.DOTALL | re.MULTILINE
        )

        for match in matches:
            sql_statement = match.group(0).strip()
            if len(sql_statement) > 20:  # Filter out very short matches
                schema_data["sql_statements"].append(
                    {
                        "file_path": str(file_path),
                        "statement": sql_statement[:500]
                        + ("..." if len(sql_statement) > 500 else ""),
                        "statement_type": _determine_sql_type(sql_statement),
                        "tables_referenced": _extract_table_names_from_sql(
                            sql_statement
                        ),
                    }
                )


def _extract_function_info(
    file_path: Path, content: str, schema_data: dict[str, Any]
) -> None:
    """Extract function definitions that might contain database operations."""
    import re

    # Function definition patterns
    function_patterns = [
        r"function\s+\w+\s+(\w+)\s*\([^)]*\)[^{]*{([^}]+)}",
        r"event\s+(\w+)\s*\([^)]*\)[^{]*{([^}]+)}",
    ]

    for pattern in function_patterns:
        matches = re.finditer(pattern, content, re.IGNORECASE | re.DOTALL)

        for match in matches:
            func_name = match.group(1)
            func_body = match.group(2) if len(match.groups()) > 1 else ""

            # Check if function contains database operations
            if any(
                keyword in func_body.upper()
                for keyword in [
                    "SELECT",
                    "INSERT",
                    "UPDATE",
                    "DELETE",
                    "EXECUTE",
                    "COMMIT",
                ]
            ):
                schema_data["functions"][func_name] = {
                    "file_path": str(file_path),
                    "has_db_operations": True,
                    "body_preview": func_body[:300]
                    + ("..." if len(func_body) > 300 else ""),
                }


def _extract_table_references(
    file_path: Path, content: str, schema_data: dict[str, Any]
) -> None:
    """Extract table references from various contexts."""
    import re

    # Look for table references in comments or string literals
    table_patterns = [
        r"//.*table[:\s]+(\w+)",
        r"\*.*table[:\s]+(\w+)",
        r'["\'].*table[:\s]+(\w+).*["\']',
    ]

    for pattern in table_patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)

        for table_name in matches:
            if table_name and table_name.upper() not in ["TABLE", "TABLES"]:
                if table_name not in schema_data["tables"]:
                    schema_data["tables"][table_name] = {
                        "name": table_name,
                        "columns": set(),
                        "referenced_by": [],
                        "source_files": [],
                    }
                schema_data["tables"][table_name]["source_files"].append(str(file_path))


def _determine_sql_type(sql_statement: str) -> str:
    """Determine the type of SQL statement."""
    sql_upper = sql_statement.upper().strip()

    if sql_upper.startswith("SELECT"):
        return "SELECT"
    if sql_upper.startswith("INSERT"):
        return "INSERT"
    if sql_upper.startswith("UPDATE"):
        return "UPDATE"
    if sql_upper.startswith("DELETE"):
        return "DELETE"
    if sql_upper.startswith("CREATE"):
        return "CREATE"
    if sql_upper.startswith("ALTER"):
        return "ALTER"
    if sql_upper.startswith("DROP"):
        return "DROP"
    return "OTHER"


def _extract_table_names_from_sql(sql_statement: str) -> list[str]:
    """Extract table names referenced in an SQL statement."""
    import re

    tables = []

    # Simple patterns for table extraction
    patterns = [
        r"FROM\s+(\w+)",
        r"JOIN\s+(\w+)",
        r"UPDATE\s+(\w+)",
        r"INTO\s+(\w+)",
        r"TABLE\s+(\w+)",
    ]

    for pattern in patterns:
        matches = re.findall(pattern, sql_statement, re.IGNORECASE)
        tables.extend(matches)

    return list(set(tables))  # Remove duplicates


def _generate_schema_documentation(
    schema_data: dict[str, Any], output_path: Path, output_format: str
) -> None:
    """Generate the final schema documentation in the requested format."""
    import json

    # Always save raw JSON data
    json_file = output_path / "database_schema_raw.json"

    # Convert sets to lists for JSON serialization
    json_data = json.loads(json.dumps(schema_data, default=str))
    for table_name, table_info in json_data.get("tables", {}).items():
        if isinstance(table_info.get("columns"), set):
            table_info["columns"] = list(table_info["columns"])

    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(json_data, f, indent=2, ensure_ascii=False)

    # Generate formatted documentation
    doc_file = output_path / f"database_schema_documentation.{output_format}"

    if output_format.lower() == "markdown":
        _generate_markdown_docs(schema_data, doc_file)
    elif output_format.lower() == "html":
        _generate_html_docs(schema_data, doc_file)
    else:
        # Default to markdown
        _generate_markdown_docs(schema_data, doc_file)


def _generate_markdown_docs(schema_data: dict[str, Any], doc_file: Path) -> None:
    """Generate markdown documentation."""
    with open(doc_file, "w", encoding="utf-8") as f:
        f.write("# PowerBuilder Database Schema Documentation\n\n")
        f.write(f"**Generated on:** {schema_data['extraction_date']}\n\n")
        f.write(f"**Project Directory:** {schema_data['project_directory']}\n\n")

        # Statistics
        stats = schema_data["statistics"]
        f.write("## Summary Statistics\n\n")
        f.write(f"- **Files Processed:** {stats['files_processed']}\n")
        f.write(f"- **Tables Found:** {stats['tables_found']}\n")
        f.write(f"- **DataWindows Found:** {stats['datawindows_found']}\n")
        f.write(f"- **SQL Statements Found:** {stats['sql_statements_found']}\n")
        f.write(f"- **Functions with DB Operations:** {stats['functions_found']}\n\n")

        # Tables
        if schema_data["tables"]:
            f.write("## Database Tables\n\n")
            for table_name, table_info in schema_data["tables"].items():
                f.write(f"### {table_name}\n\n")
                if table_info.get("referenced_by"):
                    f.write("**Referenced by:**\n")
                    f.writelines(f"- {ref}\n" for ref in table_info["referenced_by"])
                    f.write("\n")

        # DataWindows
        if schema_data["datawindows"]:
            f.write("## DataWindows\n\n")
            for dw_name, dw_info in schema_data["datawindows"].items():
                f.write(f"### {dw_name}\n\n")
                f.write(f"**File:** {dw_info['file_path']}\n\n")
                if dw_info.get("tables"):
                    f.write("**Associated Tables:**\n")
                    f.writelines(f"- {table}\n" for table in dw_info["tables"])
                    f.write("\n")

        # SQL Statements
        if schema_data["sql_statements"]:
            f.write("## SQL Statements Found\n\n")
            for i, sql_info in enumerate(
                schema_data["sql_statements"][:50], 1
            ):  # Limit to 50
                f.write(f"### Statement {i} ({sql_info['statement_type']})\n\n")
                f.write(f"**File:** {sql_info['file_path']}\n\n")
                f.write("```sql\n")
                f.write(sql_info["statement"])
                f.write("\n```\n\n")
                if sql_info.get("tables_referenced"):
                    f.write(
                        "**Tables Referenced:** "
                        + ", ".join(sql_info["tables_referenced"])
                        + "\n\n"
                    )


def _generate_html_docs(schema_data: dict[str, Any], doc_file: Path) -> None:
    """Generate HTML documentation."""
    with open(doc_file, "w", encoding="utf-8") as f:
        f.write("""<!DOCTYPE html>
<html>
<head>
    <title>PowerBuilder Database Schema Documentation</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        h1, h2, h3 { color: #333; }
        pre { background: #f5f5f5; padding: 10px; border-radius: 5px; }
        .stats { background: #e9f4ff; padding: 15px; border-radius: 5px; }
        .table-info { margin: 20px 0; }
    </style>
</head>
<body>
""")

        f.write("<h1>PowerBuilder Database Schema Documentation</h1>\n")
        f.write(
            f"<p><strong>Generated on:</strong> {schema_data['extraction_date']}</p>\n"
        )
        f.write(
            f"<p><strong>Project Directory:</strong> {schema_data['project_directory']}</p>\n"
        )

        # Statistics
        stats = schema_data["statistics"]
        f.write('<div class="stats">\n<h2>Summary Statistics</h2>\n')
        f.write("<ul>\n")
        f.write(
            f"<li><strong>Files Processed:</strong> {stats['files_processed']}</li>\n"
        )
        f.write(f"<li><strong>Tables Found:</strong> {stats['tables_found']}</li>\n")
        f.write(
            f"<li><strong>DataWindows Found:</strong> {stats['datawindows_found']}</li>\n"
        )
        f.write(
            f"<li><strong>SQL Statements Found:</strong> {stats['sql_statements_found']}</li>\n"
        )
        f.write(
            f"<li><strong>Functions with DB Operations:</strong> {stats['functions_found']}</li>\n"
        )
        f.write("</ul>\n</div>\n")

        # Tables
        if schema_data["tables"]:
            f.write("<h2>Database Tables</h2>\n")
            for table_name, table_info in schema_data["tables"].items():
                f.write('<div class="table-info">\n')
                f.write(f"<h3>{table_name}</h3>\n")
                if table_info.get("referenced_by"):
                    f.write("<strong>Referenced by:</strong>\n<ul>\n")
                    f.writelines(
                        f"<li>{ref}</li>\n" for ref in table_info["referenced_by"]
                    )
                    f.write("</ul>\n")
                f.write("</div>\n")

        f.write("</body>\n</html>\n")


# stream_extract_pbd was removed during consolidation - using Library class instead

# Initial basic logging setup - will be reconfigured by CLI
logging.basicConfig(format="%(levelname)s: %(message)s", level=logging.INFO)
logger = get_logger("tool_pb")

# Default paths
DEFAULT_EXTRACT_INPUT: str = "input"
DEFAULT_EXTRACT_OUTPUT: str = "data/output/current/extracted"
DEFAULT_PARSE_INPUT: str = "data/output/current/extracted"
DEFAULT_PARSE_OUTPUT: str = "data/output/current/parsed"
DEFAULT_ALL_PBL_INPUT: str = "input"
DEFAULT_ALL_BASE_OUTPUT: str = "output"


@click.group()
@click.version_option(version="0.1.0", prog_name="sime-finch")
@click.option(
    "--loglevel",
    type=click.Choice(
        ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        case_sensitive=False,
    ),
    default="INFO",
    help="Set the logging level.",
    show_default=True,
)
@click.option(
    "--traceback/--no-traceback",
    default=False,
    help="Show full traceback on error.",
)
@click.option(
    "--no-overwrite",
    is_flag=True,
    default=False,
    help="Prevent overwriting existing output files. Will exit if output directory contains files.",
)
@click.pass_context
def cli(ctx: click.Context, loglevel: str, traceback: bool, no_overwrite: bool) -> None:
    """SIME Finch: PowerBuilder Reverse Engineering Toolkit."""
    # Use unified logging setup
    verbose = loglevel.upper() == "DEBUG"
    setup_logging(
        level=loglevel.upper(),
    )

    # Override with specific log level if needed
    if loglevel.upper() != "INFO":
        logging.getLogger().setLevel(getattr(logging, loglevel.upper()))

    # Initialize coordination layer

    ctx.obj = {
        "traceback": traceback,
        "no_overwrite": no_overwrite,
    }
    logger.debug("Loglevel set to %s", loglevel.upper())
    logger.debug("Traceback on error: %s", traceback)
    logger.debug("No overwrite mode: %s", no_overwrite)


# Extract group for all extraction-related commands
@cli.group()
def extract() -> None:
    """PowerBuilder extraction utilities."""


@extract.command("files")
@click.argument(
    "input_dir",
    type=click.Path(exists=True, file_okay=True, dir_okay=True, resolve_path=True),
    default=DEFAULT_EXTRACT_INPUT,
)
@click.argument(
    "output_dir",
    type=click.Path(file_okay=False, dir_okay=True, resolve_path=True),
    default=DEFAULT_EXTRACT_OUTPUT,
)
@click.option("--debug", is_flag=True, help="Enable debug logging for extraction")
@click.option(
    "--enable-byte-recovery",
    is_flag=True,
    help="Enable byte-level recovery for corrupted files",
)
@click.pass_context
def extract_files(
    ctx: click.Context,
    input_dir: str,
    output_dir: str,
    debug: bool,
    enable_byte_recovery: bool,
) -> None:
    """Extract PB source from PBL/PBD files.

    INPUT_DIR: Directory containing PBL/PBD files
    OUTPUT_DIR: Directory to write extracted source files
    """
    if debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logging.getLogger("extract.extract_coordinator").setLevel(logging.DEBUG)
        logging.getLogger("extract.pbd").setLevel(logging.DEBUG)

    try:
        input_path = Path(input_dir)

        # Check and prepare output directory
        no_overwrite = ctx.obj.get("no_overwrite", False)
        output_path, should_proceed = check_and_prepare_output_directory(
            Path(output_dir),
            overwrite=not no_overwrite,
        )

        if not should_proceed:
            logger.info("Extraction cancelled by user")
            sys.exit(0)

        logger.info(
            "Extracting from %s to %s (byte_recovery=%s)",
            input_dir,
            output_path,
            enable_byte_recovery,
        )

        # Use PBLExtractor directly for extraction
        import asyncio

        from src.extract.unified_extract import ExtractCoordinator as PBLExtractor

        async def do_extraction():
            extractor = PBLExtractor()
            extracted = 0
            failed = 0

            output_path.mkdir(parents=True, exist_ok=True)

            async for pcode in extractor.extract_pbl(input_path):
                try:
                    output_file = output_path / f"{pcode.name}.pcode"
                    output_file.write_bytes(pcode.data)
                    extracted += 1
                    logger.debug(f"Extracted: {pcode.name}")
                except Exception as e:
                    logger.error(f"Failed to extract {pcode.name}: {e}")
                    failed += 1

            return extracted, failed

        try:
            extracted, failed = asyncio.run(do_extraction())
            success = failed == 0
            result = {"files_extracted": extracted, "files_failed": failed}
            logger.info(f"Extracted {extracted} files, {failed} failed")
        except Exception as e:
            logger.error(f"Extraction failed: {e}")
            success = False
            result = {"files_extracted": 0, "files_failed": 1, "error": str(e)}

        if not success:
            logger.error("Extraction completed with errors")

        logger.info("Extraction complete")
    except Exception as e:
        logger.exception("Failed to extract: %s", e)
        if click.get_current_context().obj.get("traceback"):
            raise
        sys.exit(1)


@extract.command("to-text")
@click.argument(
    "input_file",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, resolve_path=True),
)
@click.option(
    "-o",
    "--output",
    type=click.Path(file_okay=True, dir_okay=False, resolve_path=True),
    help="Output text file path (default: input file with .txt extension)",
)
@click.option("-s", "--stdout", is_flag=True, help="Also print to stdout")
def extract_to_text(input_file: str, output: str | None, stdout: bool) -> None:
    """Convert PowerBuilder binary files to readable text format."""
    input_path = Path(input_file)

    # Determine output path
    if output:
        output_path = Path(output)
    else:
        # Default: same name with .txt extension
        output_path = input_path.with_suffix(".txt")

    try:
        logger.info("Converting %s to text format...", input_path)
        result = binary_to_readable_format(input_path, output_path)

        if result:
            logger.info("Successfully converted. Output saved to %s", output_path)

            # Also print to stdout if requested
            if stdout:
                # Read the converted text and print to stdout
                try:
                    with open(output_path, encoding="utf-8"):
                        pass
                except Exception as e:
                    logger.error("Failed to read output file for stdout: %s", e)
        else:
            logger.error("Conversion failed")
            sys.exit(1)
    except Exception as e:
        logger.exception("Failed to convert to text: %s", e)
        if click.get_current_context().obj.get("traceback"):
            raise
        sys.exit(1)


@extract.command("inspect")
@click.argument(
    "files",
    nargs=-1,
    type=click.Path(exists=True, file_okay=True, dir_okay=False, resolve_path=True),
)
def extract_inspect(files: tuple[str, ...]) -> None:
    """Inspect PBD file structure."""
    # Path to the consolidated pbd_inspector.py script
    script_path = (
        Path(__file__).parent / "extract" / "pbd" / "utils" / "pbd_inspector.py"
    )

    if not script_path.exists():
        logger.error("Inspector utility not found at: %s", script_path)
        sys.exit(1)

    # Build command with arguments - add --inspect flag for structure analysis
    cmd = [sys.executable, str(script_path), "--inspect"]
    if files:
        cmd.extend(files)

    # Run the script
    try:
        sys.exit(subprocess.call(cmd))
    except Exception as e:
        logger.exception("Failed to run inspector utility: %s", e)
        if click.get_current_context().obj.get("traceback"):
            raise
        sys.exit(1)


@extract.command("hexdump")
@click.argument(
    "files",
    nargs=-1,
    type=click.Path(exists=True, file_okay=True, dir_okay=False, resolve_path=True),
)
def extract_hexdump(files: tuple[str, ...]) -> None:
    """View hexdump of PowerBuilder files."""
    # Path to the consolidated pbd_inspector.py script
    script_path = (
        Path(__file__).parent / "extract" / "pbd" / "utils" / "pbd_inspector.py"
    )

    if not script_path.exists():
        logger.error("Inspector utility not found at: %s", script_path)
        sys.exit(1)

    # Build command with arguments - no special flags for hexdump mode
    cmd = [sys.executable, str(script_path)]
    if files:
        cmd.extend(files)

    # Run the script
    try:
        sys.exit(subprocess.call(cmd))
    except Exception as e:
        logger.exception("Failed to run hexdump utility: %s", e)
        if click.get_current_context().obj.get("traceback"):
            raise
        sys.exit(1)


@cli.command()
@click.argument(
    "input_dir",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, resolve_path=True),
    default=DEFAULT_PARSE_INPUT,
)
@click.argument(
    "output_dir",
    type=click.Path(file_okay=False, dir_okay=True, resolve_path=True),
    default=DEFAULT_PARSE_OUTPUT,
)
@click.pass_context
def parse(ctx: click.Context, input_dir: str, output_dir: str) -> None:
    """Parse PowerBuilder SOURCE files into Abstract Syntax Trees (ASTs).

    This processes SOURCE files extracted from PBL/PBD archives:
    - Window files (.srw)
    - User object files (.sru)
    - Function files (.srf)
    - Menu files (.srm)
    - Structure files (.srs)
    - Application files (.sra)
    - DataWindow files (.srd)

    NOTE: This stage runs in PARALLEL with the Decompile stage.
    P-code files (.fun, .win, etc.) are handled by Decompile, not Parse.

    INPUT_DIR: Directory containing extracted PowerBuilder source files
    OUTPUT_DIR: Directory to write parsed AST data
    """
    try:
        import json
        from pathlib import Path

        from src.parse.unified_parse import create_parse_coordinator

        input_path = Path(input_dir)

        # Check and prepare output directory
        no_overwrite = ctx.obj.get("no_overwrite", False)
        output_path, should_proceed = check_and_prepare_output_directory(
            output_dir,
            allow_overwrite=not no_overwrite,
            force_overwrite=False,
            interactive=True,
            stage_name="parse",
        )

        if not should_proceed:
            logger.info("Parsing cancelled by user")
            sys.exit(0)

        logger.info(
            "Starting PowerBuilder file parsing from %s to %s...",
            input_path,
            output_path,
        )

        # Use UniversalCoordinator for parsing
        coordinator = create_parse_coordinator(
            input_dir=str(input_path),
            output_dir=str(output_path),
        )
        # Parse all PowerBuilder files in the directory
        parsed_data = coordinator.process()

        # Save parsed data summary
        summary_file = output_path / "parsed_summary.json"
        with open(summary_file, "w", encoding="utf-8") as f:
            json.dump(parsed_data, f, indent=2, default=str)

        logger.info("Parsing complete. Summary saved to %s", summary_file)
        logger.info("Parsed %s files", len(parsed_data.get("files", [])))

    except ImportError as e:
        logger.exception("Failed to import parsing modules: %s", e)
        if click.get_current_context().obj.get("traceback"):
            raise
        sys.exit(1)
    except Exception as e:
        logger.exception("Failed to parse files: %s", e)
        if click.get_current_context().obj.get("traceback"):
            raise
        sys.exit(1)


@cli.command()
@click.argument(
    "input_dir",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, resolve_path=True),
    default=DEFAULT_EXTRACT_OUTPUT,
)
@click.argument(
    "output_dir",
    type=click.Path(file_okay=False, dir_okay=True, resolve_path=True),
    default="data/output/current/decompiled",
)
@click.option(
    "--parallel",
    "-p",
    is_flag=True,
    default=False,
    help="Enable parallel processing for faster decompilation",
)
@click.option(
    "--max-workers",
    "-w",
    type=int,
    default=None,
    help="Maximum number of parallel workers (defaults to CPU count)",
)
@click.option(
    "--use-processes",
    is_flag=True,
    default=True,
    help="Use process-based parallelism instead of threads (default: True)",
)
@click.option(
    "--use-threads",
    "use_processes",
    flag_value=False,
    help="Use thread-based parallelism instead of processes",
)
@click.option(
    "--memory-mapping",
    is_flag=True,
    default=True,
    help="Enable memory mapping for large files (default: True)",
)
@click.option(
    "--no-memory-mapping",
    "memory_mapping",
    flag_value=False,
    help="Disable memory mapping for large files",
)
@click.option(
    "--progress",
    is_flag=True,
    default=True,
    help="Show enhanced progress reporting (default: True)",
)
@click.option(
    "--no-progress",
    "progress",
    flag_value=False,
    help="Disable enhanced progress reporting",
)
@click.pass_context
def decompile(
    ctx: click.Context,
    input_dir: str,
    output_dir: str,
    parallel: bool,
    max_workers: int | None,
    use_processes: bool,
    memory_mapping: bool,
    progress: bool,
) -> None:
    r"""Decompile PowerBuilder P-CODE files to high-level pseudocode.

    This processes P-CODE (bytecode) files extracted from PBL/PBD archives:
    - Function P-code (.fun)
    - Window P-code (.win)
    - User object P-code (.udo)
    - Menu P-code (.men)
    - Menu function P-code (.mef)
    - Application P-code (.apl)
    - Application function P-code (.apf)

    NOTE: This stage runs in PARALLEL with the Parse stage.
    Source files (.srw, .sru, etc.) are handled by Parse, not Decompile.

    \b
    Examples:
      # Basic decompilation
      sime-finch decompile data/output/current/extracted data/output/current/decompiled

      # Enable parallel processing with 8 workers
      sime-finch decompile --parallel --max-workers 8 input_dir output_dir

      # Use thread-based parallelism for I/O-bound workloads
      sime-finch decompile --parallel --use-threads input_dir output_dir

      # Disable progress bars for automated scripts
      sime-finch decompile --no-progress input_dir output_dir

    INPUT_DIR: Directory containing extracted PowerBuilder P-code files
    OUTPUT_DIR: Directory to write decompiled high-level code
    """
    try:
        # Check and prepare output directory
        no_overwrite = ctx.obj.get("no_overwrite", False)
        output_path, should_proceed = check_and_prepare_output_directory(
            output_dir,
            allow_overwrite=not no_overwrite,
            force_overwrite=False,
            interactive=True,
            stage_name="decompile",
        )

        if not should_proceed:
            logger.info("Decompilation cancelled by user")
            sys.exit(0)

        logger.info("Decompiling PCode from {input_dir} to %s...", output_path)
        output_dir_str = str(output_path)  # Convert back to string for coordinators

        # Use UniversalCoordinator for decompilation
        coordinator = create_decompile_coordinator(
            input_dir=input_dir,
            output_dir=output_dir_str,
            parallel_enabled=parallel,
            cache_enabled=True,
            max_workers=max_workers if parallel else None,
        )

        result = coordinator.process()

        # Log summary
        if result.get("files_failed", 0) == 0:
            logger.info("Decompilation completed successfully:")
            logger.info(
                "  Files processed: %d",
                result.get("files_processed", 0),
            )
            if "duration_seconds" in result:
                logger.info("  Duration: %.1f seconds", result["duration_seconds"])
                logger.info(
                    "  Success rate: %.1f%%", result.get("success_rate", 0) * 100
                )
        else:
            logger.error(
                "Decompilation failed with %d errors",
                result.get("files_failed", 0),
            )
            sys.exit(1)

        logger.info("Decompilation complete.")
    except Exception as e:
        logger.exception("Failed to decompile: %s", e)
        if click.get_current_context().obj.get("traceback"):
            raise
        sys.exit(1)


@cli.command()
@click.argument(
    "input_dir",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, resolve_path=True),
    default=DEFAULT_PARSE_OUTPUT,
)
@click.argument(
    "output_dir",
    type=click.Path(file_okay=False, dir_okay=True, resolve_path=True),
    default="data/output/current/model",
)
@click.pass_context
def model(ctx: click.Context, input_dir: str, output_dir: str) -> None:
    """Convert parsed AST files to semantic model objects.

    This is the Model stage of the pipeline, which converts Abstract Syntax Trees
    (ASTs) from the Parse stage into structured semantic models that can be used
    by the Generate stage to produce modern code.

    INPUT_DIR: Directory containing parsed AST JSON files
    OUTPUT_DIR: Directory for model JSON files
    """
    try:
        # Check and prepare output directory
        no_overwrite = ctx.obj.get("no_overwrite", False)
        output_path, should_proceed = check_and_prepare_output_directory(
            output_dir,
            allow_overwrite=not no_overwrite,
            force_overwrite=False,
            interactive=True,
            stage_name="model",
        )

        if not should_proceed:
            logger.info("Model conversion cancelled by user")
            sys.exit(0)

        logger.info("Converting ASTs from {input_dir} to models in %s", output_path)

        # Use UniversalCoordinator for model processing
        coordinator = create_model_coordinator(
            input_dir=input_dir,
            output_dir=output_path,
        )

        # Convert all AST files
        result = coordinator.process()

        # Log results
        success_rate = (
            result.get("files_processed", 0)
            / (result.get("files_processed", 0) + result.get("files_failed", 0))
            if (result.get("files_processed", 0) + result.get("files_failed", 0)) > 0
            else 0
        )
        logger.info(
            "Model conversion complete. Processed: %s, Failed: %s, Success rate: %.1%",
            result["processed"],
            result["failed"],
            success_rate,
        )

        # Save summary
        summary_file = output_path / "model_summary.json"
        with open(summary_file, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "model_at": datetime.now().isoformat(),
                    "input_directory": str(input_dir),
                    "output_directory": str(output_dir),
                    **result,
                },
                f,
                indent=2,
            )

        logger.info("Model summary saved to %s", summary_file)

    except ImportError as e:
        logger.exception("Failed to import model modules: %s", e)
        if click.get_current_context().obj.get("traceback"):
            raise
        sys.exit(1)
    except Exception as e:
        logger.exception("Failed to convert models: %s", e)
        if click.get_current_context().obj.get("traceback"):
            raise
        sys.exit(1)


@cli.command()
@click.option(
    "--model-dir",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    help="Directory containing model files from Model stage",
)
@click.option(
    "--output-dir",
    type=click.Path(file_okay=False, dir_okay=True),
    help="Output directory for generated code",
)
@click.option(
    "--parsed-dir",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    help="Directory containing parsed AST files (legacy)",
)
@click.option(
    "--decompiled-dir",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    help="Directory containing decompiled functions (legacy)",
)
@click.option(
    "--target",
    type=click.Choice(
        ["python", "flutter", "react-typescript", "tauri", "dioxus", "both"]
    ),
    default="both",
    help="Target language to generate",
)
def generate(
    model_dir: str | None,
    output_dir: str | None,
    parsed_dir: str | None,
    decompiled_dir: str | None,
    target: str,
) -> None:
    """Generate modern application code from model files.

    This is the final stage of the pipeline, which takes semantic model objects
    from the Model stage and generates modern application code:
    - Backend: Python/Litestar APIs, SQLModel models, Pydantic schemas
    - Frontend: Flutter/Dart UI, screens, widgets, state management

    Note: --parsed-dir and --decompiled-dir are kept for backward compatibility.
    Use --model-dir for the new pipeline that reads from Model stage output.
    """
    try:
        from src.generate import GenerateCoordinator

        create_generate_coordinator = (
            lambda input_path,
            output_path,
            target,
            streaming,
            parallel,
            workers,
            verbose: GenerateCoordinator(input_path, output_path)
        )

        # Use new pipeline if model-dir is provided
        if model_dir and output_dir:
            logger.info("Generating %s code from model files...", target)
            coordinator = create_generate_coordinator(
                Path(model_dir), Path(output_dir), target
            )
            results = coordinator.process()

            # Results is a dict with counts, not file lists
            total_files = results.get("files_generated", 0)
            logger.info("Generated %s files", total_files)
            logger.info("  Processed: %s model files", results.get("total_models", 0))
            logger.info("  Failed: %s files", len(results.get("failed_files", [])))

        # Fall back to legacy pipeline
        elif parsed_dir:
            logger.info("Using legacy generation pipeline...")

            # Use default output directory for legacy pipeline
            legacy_output = "output/generated"

            if target in ["python", "both"]:
                logger.info("Generating database models...")
                generate_models(parsed_dir, legacy_output)

                if decompiled_dir:
                    logger.info("Generating service layer...")
                    generate_services(parsed_dir, decompiled_dir)

            if target in ["flutter", "both"]:
                logger.info("Generating Flutter frontend...")
                generate_flutter(parsed_dir, legacy_output)

            if target == "react-typescript":
                logger.warning(
                    "React/TypeScript generation requires --model-dir, not supported in legacy mode"
                )
                logger.info(
                    "Please use the modern pipeline: python main.py generate --model-dir <path> --output-dir <path> --target react-typescript"
                )

            logger.info("Code generation complete.")
        else:
            raise click.UsageError(
                "Either --model-dir and --output-dir or --parsed-dir must be provided"
            )

    except ImportError as e:
        logger.exception("Failed to import generation modules: %s", e)
        if click.get_current_context().obj.get("traceback"):
            raise
        sys.exit(1)
    except Exception as e:
        logger.exception("Failed to generate code: %s", e)
        if click.get_current_context().obj.get("traceback"):
            raise
        sys.exit(1)


@cli.command()
@click.option(
    "--project-dir",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, resolve_path=True),
    default=".",
    show_default=True,
    help="PowerBuilder project directory containing source files",
)
@click.option(
    "--output-dir",
    "-o",
    type=click.Path(file_okay=False, dir_okay=True, resolve_path=True),
    default="output/schema",
    show_default=True,
    help="Output directory for schema documentation",
)
@click.option(
    "--format",
    "-f",
    type=click.Choice(["markdown", "html", "json"], case_sensitive=False),
    default="markdown",
    show_default=True,
    help="Output format for documentation",
)
@click.option(
    "--include-flows/--no-flows",
    default=True,
    show_default=True,
    help="Include data flow analysis in documentation",
)
def schema(project_dir: str, output_dir: str, format: str, include_flows: bool) -> None:
    """Extract and document database schema from PowerBuilder code.

    This command analyzes PowerBuilder source files to extract:
    - Database tables and columns
    - Table relationships (foreign keys)
    - Business logic functions and their database operations
    - UI elements and their data bindings
    - Data flow between components

    The output is a comprehensive documentation file that maps all database
    interactions in human-readable format.
    """
    try:
        logger.info("Extracting database schema from PowerBuilder project...")
        logger.info("Project directory: %s", project_dir)
        logger.info("Output directory: %s", output_dir)
        logger.info("Documentation format: %s", format)

        # Extract schema using unified decompile module
        extract_database_schema(
            project_dir=project_dir,
            output_dir=output_dir,
            output_format=format,
        )
        logger.info("Database schema extraction complete!")

        # Show output location
        output_path = Path(output_dir)
        doc_file = (
            output_path
            / f"database_schema_documentation.{format if format != 'html' else 'html'}"
        )
        logger.info("Documentation saved to: %s", doc_file)
        logger.info("Raw data saved to: %s", output_path / "database_schema_raw.json")

    except Exception as e:
        logger.exception("Failed to extract database schema: %s", e)
        if click.get_current_context().obj.get("traceback"):
            raise
        sys.exit(1)


@cli.command(
    context_settings={"ignore_unknown_options": True, "allow_extra_args": True},
)
@click.option(
    "--pbl-input-dir",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, resolve_path=True),
    default=DEFAULT_ALL_PBL_INPUT,
    show_default=True,
    help="Input directory containing PBL/PBD files.",
)
@click.option(
    "--base-output-dir",
    type=click.Path(file_okay=False, dir_okay=True, resolve_path=True),
    default=DEFAULT_ALL_BASE_OUTPUT,
    show_default=True,
    help="Base directory for all output (extracted, parsed, decompiled, generated).",
)
@click.option(
    "--debug",
    is_flag=True,
    help="Enable debug logging for the pipeline, especially extraction.",
)
@click.option(
    "--enable-byte-recovery",
    is_flag=True,
    default=False,
    help='Enable byte-level recovery during extraction phase of "all" pipeline.',
)
@click.pass_context
def all(
    ctx: click.Context,
    pbl_input_dir: str,
    base_output_dir: str,
    debug: bool,
    enable_byte_recovery: bool,
) -> None:
    """Run the full pipeline: extract, decompile, parse, model, generate.

    Pipeline Execution Flow (Sequential):
    1. Extract: Produces .fun files from PBL/PBD archives
    2. Decompile: Converts .fun files to .sru source files
    3. Parse: Processes .sru files into Abstract Syntax Trees (ASTs)
    4. Model: Converts ASTs into structured model objects
    5. Generate: Produces Python/Dart code from model objects

    All stages run SEQUENTIALLY, with each stage feeding into the next.
    """
    if debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logging.getLogger("extract.extract_coordinator").setLevel(logging.DEBUG)
        logging.getLogger("extract.pbd").setLevel(logging.DEBUG)
        logging.getLogger("parse").setLevel(logging.DEBUG)
        logger.info("Debug logging enabled for 'all' pipeline.")

    start_time = time.time()

    try:
        # Use UniversalCoordinator for pipeline operations
        from src.extract import ExtractCoordinator

        # Create a simple UniversalCoordinator wrapper
        class UniversalCoordinator:
            def __init__(self, input_path, output_path, stage_config=None):
                self.input_path = input_path
                self.output_path = output_path
                self.stage_config = stage_config or {}

        # Configure pipeline
        config = {
            "extract": {
                "preserve_structure": True,
                "extract_resources": True,
                "enable_byte_recovery": enable_byte_recovery,
            },
            "decompile": {
                "debug_mode": debug,
            },
            "parse": {
                "strict_mode": False,
                "resolve_imports": True,
            },
            "model": {},
            "generate": {
                "target_framework": "flutter",
                "null_safety": True,
                "generate_tests": False,
            },
            "cleanup_temp": False,  # Keep temp files for debugging
            "auto_recover_checkpoint": True,
        }

        # Check and prepare output directory
        no_overwrite = ctx.obj.get("no_overwrite", False)
        output_path, should_proceed = check_and_prepare_output_directory(
            Path(base_output_dir),
            overwrite=not no_overwrite,
        )

        if not should_proceed:
            logger.info("Full pipeline cancelled by user")
            sys.exit(0)

        # Create universal coordinator for full pipeline
        logger.info("Initializing universal coordinator...")
        coordinator = UniversalCoordinator(
            stage=PipelineStage.ALL,
            input_dir=pbl_input_dir,
            output_dir=str(output_path),
            config=config,
        )

        # Find all PBL/PBD files to process
        input_path = Path(pbl_input_dir)
        pbl_files = []

        if input_path.is_file():
            # Single file
            if input_path.suffix.lower() in [".pbl", ".pbd"]:
                pbl_files.append(str(input_path))
        else:
            # Directory - find all PBL/PBD files
            for ext in ["*.pbl", "*.pbd"]:
                pbl_files.extend(str(f) for f in input_path.rglob(ext))

        if not pbl_files:
            logger.error("No PBL/PBD files found in %s", pbl_input_dir)
            sys.exit(1)

        logger.info("Found %d PBL/PBD files to process", len(pbl_files))

        # Run the pipeline
        logger.info("Starting sequential pipeline execution...")
        results = coordinator.process()

        # Display results
        logger.info("Pipeline execution completed!")
        logger.info("Results:")
        logger.info("  Total files processed: %d", results.get("total_files", 0))
        logger.info("  Successful: %d", results.get("successful", 0))
        logger.info("  Failed: %d", results.get("failed", 0))

        # Display stage results
        if "stages" in results:
            logger.info("\nStage Results:")
            for stage_name, stage_stats in results["stages"].items():
                logger.info("  %s:", stage_name.capitalize())
                logger.info("    Processed: %d", stage_stats.get("processed", 0))
                logger.info("    Successful: %d", stage_stats.get("successful", 0))
                logger.info("    Failed: %d", stage_stats.get("failed", 0))

        # Display error summary if any
        if results.get("error_summary"):
            logger.warning("\nError Summary:")
            error_summary = results["error_summary"]
            if "errors" in error_summary:
                for stage, count in error_summary["errors"].items():
                    if count > 0:
                        logger.warning("  %s: %d errors", stage, count)
            if "warnings" in error_summary:
                for stage, count in error_summary["warnings"].items():
                    if count > 0:
                        logger.warning("  %s: %d warnings", stage, count)

        end_time = time.time()
        elapsed_time = end_time - start_time
        logger.info("\nTotal pipeline execution time: %.2f seconds", elapsed_time)

        # Exit with appropriate code
        if results.get("failed", 0) > 0:
            sys.exit(1)

    except ImportError as e:
        logger.exception("Failed to import required modules: %s", e)
        if click.get_current_context().obj.get("traceback"):
            raise
        sys.exit(1)
    except Exception as e:
        logger.exception("Pipeline failed: %s", e)
        if click.get_current_context().obj.get("traceback"):
            raise
        sys.exit(1)


@cli.command()
@click.argument(
    "target_dir",
    type=click.Path(file_okay=False, dir_okay=True, resolve_path=True),
    required=False,
)
@click.option(
    "--force",
    is_flag=True,
    help="Actually delete the files/directories. Without this, it only lists what would be deleted.",
)
@click.option(
    "--full-recovery",
    is_flag=True,
    help="Target the common 'data/output/current/extracted/recovery' directory.",
)
@click.option(
    "--full-extracted",
    is_flag=True,
    help="Target the common 'data/output/current/extracted' directory.",
)
@click.option(
    "--full-decompiled",
    is_flag=True,
    help="Target the common 'data/output/current/decompiled' directory.",
)
@click.option(
    "--full-parsed",
    is_flag=True,
    help="Target the common 'data/output/current/parsed' directory.",
)
@click.option(
    "--test-outputs",
    is_flag=True,
    help="Clean all test output directories (test_*).",
)
def clean_output(
    target_dir: str | None,
    force: bool,
    full_recovery: bool,
    full_extracted: bool,
    full_decompiled: bool,
    full_parsed: bool,
    test_outputs: bool,
) -> None:
    """Clean specific output directories. Lists contents by default; use --force to delete."""
    import shutil

    dirs_to_clean: list[Path] = []
    if target_dir:
        dirs_to_clean.append(Path(target_dir))
    if full_recovery:
        dirs_to_clean.append(Path("data/output/current/extracted/recovery"))
    if full_extracted:
        logger.warning(
            "Targeting 'data/output/current/extracted'. This is a primary output directory.",
        )
        dirs_to_clean.append(Path("data/output/current/extracted"))
    if full_decompiled:
        dirs_to_clean.append(Path("data/output/current/decompiled"))
    if full_parsed:
        dirs_to_clean.append(Path("data/output/current/parsed"))
    if test_outputs:
        output_path = Path("output")
        if output_path.exists():
            # Find all test_* directories
            test_dirs = [
                d
                for d in output_path.iterdir()
                if d.is_dir() and d.name.startswith("test_")
            ]
            dirs_to_clean.extend(test_dirs)
            logger.info("Found %s test output directories", len(test_dirs))

    if not dirs_to_clean:
        logger.info(
            "No target directory specified. Use an argument or one of the flags.",
        )
        logger.info("Common large directories that can be targeted:")
        logger.info(
            "  data/output/current/extracted/recovery  (often very large due to byte recovery)",
        )
        logger.info("  output/extracted           (all extracted files)")
        logger.info("  output/decompiled          (decompiled outputs)")
        logger.info("  output/parsed              (parsed ASTs and structures)")
        logger.info("  --test-outputs             (all test_* directories)")
        return

    for d_path in dirs_to_clean:
        if d_path.exists() and d_path.is_dir():
            logger.info("Targeting directory for cleaning: %s", d_path.resolve())
            if force:
                logger.warning("--force specified. Deleting %s...", d_path.resolve())
                try:
                    shutil.rmtree(d_path)
                    logger.info("Successfully deleted %s.", d_path.resolve())
                except Exception as e:
                    logger.exception("Error deleting {d_path.resolve()}: %s", e)
            else:
                logger.info(
                    "Listing contents of %s (dry run, use --force to delete):",
                    d_path.resolve(),
                )
                # List top-level contents for brevity
                count = 0
                for item in d_path.iterdir():
                    logger.info(
                        "  - %s (%s)",
                        item.name,
                        "DIR" if item.is_dir() else "FILE",
                    )
                    count += 1
                    if count >= 20:
                        logger.info(
                            "  ... and more (listing capped at 20 items for brevity).",
                        )
                        break
                if count == 0:
                    logger.info("  (Directory is empty)")
        else:
            logger.warning(
                "Directory not found or is not a directory: %s", d_path.resolve()
            )


@cli.command()
@click.argument(
    "input_path",
    type=click.Path(exists=True, file_okay=True, dir_okay=True),
    required=True,
)
@click.argument(
    "output_path",
    type=click.Path(file_okay=False, dir_okay=True),
    required=True,
)
@click.option(
    "--streaming/--no-streaming",
    default=True,
    help="Use streaming extraction for large files (default: enabled)",
)
@click.option(
    "--async/--sync",
    "use_async",
    default=False,
    help="Use async extraction for better performance",
)
@click.option(
    "--chunk-size",
    type=int,
    default=8192,
    help="Chunk size for streaming operations (default: 8192)",
)
def extract_streaming(
    input_path: str,
    output_path: str,
    streaming: bool,
    use_async: bool,
    chunk_size: int,
) -> None:
    """Extract PBD files using the Library class.

    NOTE: Streaming and async functionality was removed during code consolidation.
    All extraction now uses the Library class for consistency and simplicity.
    The streaming and use_async parameters are kept for CLI compatibility but ignored.
    """
    if streaming or use_async:
        logger.warning(
            "Streaming and async extraction was removed during consolidation. "
            "Using standard Library class extraction instead."
        )
    logger.info("Extracting PBD files using Library class...")

    # Convert string paths to Path objects
    input_path_obj = Path(input_path)
    output_path_obj = Path(output_path)

    output_path_obj.mkdir(parents=True, exist_ok=True)

    if input_path_obj.is_file() and input_path_obj.suffix.lower() in (".pbd", ".pbl"):
        # Single file extraction - using Library class
        with Library(input_path_obj) as lib:
            lib.extract_all(output_path_obj)
            logger.info("Extracted entries from %s", input_path_obj.name)
    else:
        # Directory extraction
        pbd_files = list(input_path_obj.glob("*.pbd")) + list(
            input_path_obj.glob("*.pbl")
        )
        logger.info("Found %s PBD/PBL files", len(pbd_files))

        for pbd_file in pbd_files:
            file_output = output_path_obj / pbd_file.stem
            # Using Library class from unified extract
            with Library(pbd_file) as lib:
                lib.extract_all(file_output)
                logger.info("Extracted entries from %s", pbd_file.name)


@cli.command()
@click.argument(
    "input_path",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    required=True,
)
@click.argument(
    "output_path",
    type=click.Path(file_okay=False, dir_okay=True),
    required=True,
)
@click.option(
    "--target",
    type=click.Choice(["flutter", "python", "typescript"]),
    default="flutter",
    help="Target language for code generation",
)
@click.option(
    "--parallel/--sequential",
    default=True,
    help="Run Parse and Decompile stages in parallel (default: enabled)",
)
@click.option(
    "--async/--sync",
    "use_async",
    default=False,
    help="Use async pipeline for better performance",
)
@click.option(
    "--cache/--no-cache",
    default=True,
    help="Enable caching for parsed ASTs (default: enabled)",
)
@click.option(
    "--streaming/--no-streaming",
    default=True,
    help="Use streaming for large files (default: enabled)",
)
def all_parallel(
    input_path: str,
    output_path: str,
    target: str,
    parallel: bool,
    use_async: bool,
    cache: bool,
    streaming: bool,
) -> None:
    """Run the full pipeline with performance optimizations.

    This command runs the complete PowerBuilder to target language conversion
    with various performance optimizations:

    - Parallel execution of Parse and Decompile stages
    - Async processing for better I/O handling
    - Streaming support for large files
    - Caching of parsed ASTs
    """
    from src.domain.models import PipelineStage

    # Create a simple UniversalCoordinator wrapper
    class UniversalCoordinator:
        def __init__(self, input_path, output_path, stage_config=None):
            self.input_path = input_path
            self.output_path = output_path
            self.stage_config = stage_config or {}

    logger.info("Running optimized pipeline:")
    logger.info("  Target: %s", target)
    logger.info("  Parallel: %s", "enabled" if parallel else "disabled")
    logger.info("  Async: %s", "enabled" if use_async else "disabled")
    logger.info("  Cache: %s", "enabled" if cache else "disabled")
    logger.info("  Streaming: %s", "enabled" if streaming else "disabled")

    coordinator = UniversalCoordinator(
        stage=PipelineStage.ALL,
        input_dir=input_path,
        output_dir=output_path,
        config={
            "target": target,
            "parallel": parallel,
            "cache": {"enabled": cache},
            "streaming": streaming,
        },
    )

    # Find all PBL/PBD files to process
    input_path_obj = Path(input_path)
    pbl_files = []

    if input_path_obj.is_file():
        # Single file
        if input_path_obj.suffix.lower() in [".pbl", ".pbd"]:
            pbl_files.append(str(input_path_obj))
    else:
        # Directory - find all PBL/PBD files
        for ext in ["*.pbl", "*.pbd"]:
            pbl_files.extend(str(f) for f in input_path_obj.rglob(ext))

    if not pbl_files:
        logger.error("No PBL/PBD files found in %s", input_path)
        sys.exit(1)

    logger.info("Found %d PBL/PBD files to process", len(pbl_files))

    # Run the pipeline
    logger.info("Starting parallel pipeline execution...")
    results = coordinator.process()

    # Print summary
    logger.info("\nPipeline Summary:")
    logger.info("  Total files: %s", results.get("total_files", 0))
    logger.info("  Successful: %s", results.get("successful", 0))
    logger.info("  Failed: %s", results.get("failed", 0))

    if results.get("error_summary", {}).get("errors"):
        logger.error("Pipeline completed with errors")
        sys.exit(1)
    else:
        logger.info("Pipeline completed successfully")


@cli.command()
@click.option(
    "--size", type=int, default=1000, help="Maximum number of entries to cache"
)
@click.option("--memory", type=int, default=512, help="Maximum cache memory in MB")
def cache_stats(size: int, memory: int) -> None:
    """Display cache statistics and optionally configure cache settings."""

    # Simple cache manager implementation
    class CacheManager:
        def __init__(self, cache_dir):
            self.cache_dir = cache_dir

        def clear_all(self):
            if self.cache_dir.exists():
                import shutil

                shutil.rmtree(self.cache_dir)

    def show_stats() -> None:
        cache_manager = CacheManager()

        logger.info("Cache Statistics:")
        logger.info("  Max size: %s entries", size)
        logger.info("  Max memory: %s MB", memory)
        logger.info("Cache configuration updated successfully.")
        logger.info("Note: Detailed runtime statistics require cache to be in use.")

    show_stats()


if __name__ == "__main__":
    cli()
