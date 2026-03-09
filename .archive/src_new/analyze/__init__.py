"""Analysis Feature - Advanced code analysis capabilities.

This package provides comprehensive analysis tools including database schema
extraction, SQL analysis, and code complexity metrics.
"""

from .complexity import (
    CodeSmell,
    CodeSmellType,
    ComplexityAnalyzer,
    ComplexityLevel,
    FileMetrics,
    MethodMetrics,
    ClassMetrics,
)
from .database import (
    Column,
    DatabaseSchema,
    DataType,
    ForeignKey,
    Index,
    SchemaExtractor,
    SQLParser,
    SQLStatement,
    SQLType,
    StoredProcedure,
    Table,
)

__all__ = [
    # Complexity analysis
    "ComplexityAnalyzer",
    "ComplexityLevel",
    "CodeSmell",
    "CodeSmellType",
    "FileMetrics",
    "MethodMetrics",
    "ClassMetrics",
    # Database analysis
    "SchemaExtractor",
    "SQLParser",
    "DatabaseSchema",
    "Table",
    "Column",
    "Index",
    "ForeignKey",
    "StoredProcedure",
    "SQLStatement",
    "SQLType",
    "DataType",
]
