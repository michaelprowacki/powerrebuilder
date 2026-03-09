"""Unified Parse Module - ALL parsing functionality in one place.

This consolidates 25+ files into 1 for radical simplification:
- types.py - Core types and constants
- grammar/* - Grammar management and loading
- preprocessor/* - Source preprocessing and imports
- parser/* - All parser implementations (base, PowerBuilder, SQL, specialized)
- transformer/* - AST transformation from parse trees
- transformer/visitors/* - Visitor pattern implementation and position tracking
- library.py - Library and symbol management
- factory.py - Parser factory
- recovery_strategy.py - Error recovery
- resolution.py - Type resolution

This mega-file includes ALL visitor functionality:
- Base visitor classes and traversal patterns
- Position tracking and source location management
- Error reporting with location information
- Comprehensive AST node visitor methods

The goal is MAXIMUM consolidation with aggressive deduplication.
"""

from __future__ import annotations

import logging
import os
import re
import time
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from threading import Lock
from typing import Any, ClassVar, Protocol, TypeVar, Union, runtime_checkable

# External imports
from lark import Lark, Token, Transformer, Tree
from lark.exceptions import GrammarError, UnexpectedInput

# Internal imports
from src.core.constants import FILE_EXTENSIONS, FileType
from src.core.exceptions import (
    ASTConstructionError,
    ParseError,
    ParseRecoveryError,
)
from src.extract import extract_pbl_file as extract_pbl
from src.model.ast import (
    ASTAssignment,
    ASTNode,
    BasicType,
    Block,
    BooleanLiteral,
    CustomType,
    FunctionCall,
    FunctionDefinition,
    IfStatement,
    IntegerLiteral,
    Literal,
    Parameter,
    ReturnStatement,
    Signature,
    StringLiteral,
    Type,
    TypeCategory,
    Variable,
    VariableDeclaration,
)
from src.model.ast.literals import (
    StringLiteral as ASTStringLiteral,
)
from src.model.ast.nodes.literals import NumberLiteral
from src.model.ast.nodes.sql import (
    ColumnReference as SQLColumn,
    SelectStatement as SQLSelectStatement,
    TableReference as SQLTable,
)
from src.model.ast.pb_types import (
    PBCustomType,
    PBType,
    PBTypeRegistry,
)
from src.model.entities import PBConstructorCall, PBFunctionCall, PBMethodCall
from src.model.optimization.sql_optimizer import SQLOptimizer
from src.model.transaction.statement import PBStatementType, PBTransactionStatement
from src.model.types.base import PBNode, Position, SourceLocation
from src.model.types.errors import ParseErrorCollector
from src.model.constructs.pb_access import PBAccessNode

logger = logging.getLogger(__name__)

# TypeVars for visitor pattern
T = TypeVar("T")
NodeType = TypeVar("NodeType", bound=PBNode)

# ============================================================================
# TYPES AND CONSTANTS SECTION
# ============================================================================


# Position handling protocols and classes
@runtime_checkable
class PositionTrackable(Protocol):
    """Protocol for objects that can track source positions."""

    start_position: int | None
    stop_position: int | None
    source_file: str | None


@dataclass
class PositionRange:
    """Represents a range of positions in source code."""

    start_line: int
    start_column: int
    end_line: int
    end_column: int
    start_offset: int | None = None
    end_offset: int | None = None
    filename: str | None = None

    def to_source_location(self) -> SourceLocation:
        """Convert to a SourceLocation object."""
        start = Position(
            line=self.start_line, column=self.start_column, offset=self.start_offset
        )
        end = Position(
            line=self.end_line, column=self.end_column, offset=self.end_offset
        )
        return SourceLocation(start=start, end=end, filename=self.filename)


class EnumeratedType:
    """Represents an enumerated type."""

    def __init__(self, name: str, values: list[str] | None = None):
        self.name = name
        self.values = values or []


class StructureType:
    """Represents a structure type."""

    def __init__(
        self, name: str, fields: dict[str, Any] | None = None, parent: str | None = None
    ):
        self.name = name
        self.fields = fields or {}
        self.parent = parent


class PositionTrackerMixin:
    """Mixin to add position tracking capabilities to transformers and visitors."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize position tracking state."""
        super().__init__(*args, **kwargs)
        self._current_filename: str | None = None
        self._source_lines: list[str] = []
        self._position_stack: list[PositionRange] = []

    def set_source_context(
        self, filename: str | None, source: str | None = None
    ) -> None:
        """Set the current source file context.

        Args:
            filename: Name of the source file being processed
            source: Source code content (optional, for line tracking)
        """
        self._current_filename = filename
        if source:
            self._source_lines = source.splitlines(keepends=True)
        else:
            self._source_lines = []

    def extract_position_from_tree(self, tree: Tree) -> PositionRange | None:
        """Extract position information from a Lark Tree.

        Args:
            tree: Lark parse tree node

        Returns:
            PositionRange if position info is available, None otherwise
        """
        if not hasattr(tree, "meta") or not tree.meta:
            return None

        meta = tree.meta

        # Lark provides line, column, start_pos, end_pos
        if hasattr(meta, "line") and hasattr(meta, "column"):
            return PositionRange(
                start_line=meta.line,
                start_column=meta.column,
                end_line=meta.end_line if hasattr(meta, "end_line") else meta.line,
                end_column=meta.end_column
                if hasattr(meta, "end_column")
                else meta.column,
                start_offset=meta.start_pos if hasattr(meta, "start_pos") else None,
                end_offset=meta.end_pos if hasattr(meta, "end_pos") else None,
                filename=self._current_filename,
            )

        return None

    def extract_position_from_token(self, token: Token) -> PositionRange | None:
        """Extract position information from a Lark Token.

        Args:
            token: Lark token

        Returns:
            PositionRange if position info is available, None otherwise
        """
        if not hasattr(token, "line") or not hasattr(token, "column"):
            return None

        # Calculate end position based on token value
        end_line = token.line
        end_column = token.column + len(str(token.value))

        # Handle multi-line tokens
        if "\n" in str(token.value):
            lines = str(token.value).splitlines()
            end_line = token.line + len(lines) - 1
            end_column = len(lines[-1]) + 1 if len(lines) > 1 else end_column

        return PositionRange(
            start_line=token.line,
            start_column=token.column,
            end_line=end_line,
            end_column=end_column,
            start_offset=token.start_pos if hasattr(token, "start_pos") else None,
            end_offset=token.end_pos if hasattr(token, "end_pos") else None,
            filename=self._current_filename,
        )

    def extract_position(self, node: Tree | Token | Any) -> PositionRange | None:
        """Extract position information from any Lark node.

        Args:
            node: Lark tree, token, or other node

        Returns:
            PositionRange if position info is available, None otherwise
        """
        if isinstance(node, Tree):
            return self.extract_position_from_tree(node)
        if isinstance(node, Token):
            return self.extract_position_from_token(node)
        return None

    def annotate_node_with_position(
        self, ast_node: NodeType, position: PositionRange | None
    ) -> NodeType:
        """Annotate an AST node with position information.

        Args:
            ast_node: AST node to annotate
            position: Position information to attach

        Returns:
            The annotated AST node
        """
        if position and isinstance(ast_node, PBNode):
            # Use the existing position fields in PBNode
            ast_node.start_position = position.start_offset
            ast_node.stop_position = position.end_offset
            ast_node.source_file = position.filename

            # Also store detailed position info as metadata if the node supports it
            if hasattr(ast_node, "location"):
                ast_node.location = position.to_source_location()

        return ast_node

    def with_position_context(self, position: PositionRange | None):
        """Context manager for tracking nested positions.

        Args:
            position: Position to push onto the stack
        """

        class PositionContext:
            def __init__(
                self, tracker: PositionTrackerMixin, pos: PositionRange | None
            ) -> None:
                self.tracker = tracker
                self.position = pos

            def __enter__(self):
                if self.position:
                    self.tracker._position_stack.append(self.position)
                return self

            def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any):
                if self.position and self.tracker._position_stack:
                    self.tracker._position_stack.pop()

        return PositionContext(self, position)

    def get_current_position(self) -> PositionRange | None:
        """Get the current position from the stack.

        Returns:
            Current position or None if stack is empty
        """
        return self._position_stack[-1] if self._position_stack else None

    def get_line_content(self, line_number: int) -> str | None:
        """Get the content of a specific line.

        Args:
            line_number: 1-based line number

        Returns:
            Line content or None if out of range
        """
        if 0 < line_number <= len(self._source_lines):
            return self._source_lines[line_number - 1].rstrip("\n\r")
        return None

    def create_error_with_position(
        self, message: str, position: PositionRange | None = None
    ) -> dict[str, Any]:
        """Create an error message with position information.

        Args:
            message: Error message
            position: Position where error occurred (uses current if None)

        Returns:
            Error dictionary with position details
        """
        pos = position or self.get_current_position()
        error = {"message": message, "type": "parse_error"}

        if pos:
            error.update(
                {
                    "line": pos.start_line,
                    "column": pos.start_column,
                    "end_line": pos.end_line,
                    "end_column": pos.end_column,
                    "filename": pos.filename,
                }
            )

            # Add line content for better error reporting
            line_content = self.get_line_content(pos.start_line)
            if line_content:
                error["line_content"] = line_content
                # Add visual indicator
                if pos.start_column > 0:
                    indicator = " " * (pos.start_column - 1) + "^"
                    if (
                        pos.start_line == pos.end_line
                        and pos.end_column > pos.start_column
                    ):
                        indicator += "~" * (pos.end_column - pos.start_column - 1)
                    error["indicator"] = indicator

        return error


# ============================================================================
# GRAMMAR SECTION
# ============================================================================


class GrammarManager:
    """Manages multiple Lark grammar files and their dependencies."""

    def __init__(self, grammar_dir: Path | None = None) -> None:
        """Initialize GrammarManager."""
        if grammar_dir is None:
            grammar_dir = Path(__file__).parent / "grammar"

        self.grammar_dir = Path(grammar_dir)
        if not self.grammar_dir.exists():
            self.grammar_dir = Path(__file__).parent.parent / "parse" / "grammar"
            if not self.grammar_dir.exists():
                # Create a minimal grammar directory if none exists
                self.grammar_dir = Path("/tmp/pb_grammar")
                self.grammar_dir.mkdir(exist_ok=True)

        self._cache: dict[str, Lark] = {}
        self._grammars: dict[str, str] = {}
        self._dependencies: dict[str, set[str]] = {}

        # Mapping of file types to grammar names
        self._file_type_mapping = {
            FileType.WINDOW: "powerbuilder",
            FileType.USER_OBJECT: "powerbuilder",
            FileType.FUNCTION: "powerbuilder",
            FileType.STRUCTURE: "powerbuilder",
            FileType.MENU: "powerbuilder",
            FileType.APPLICATION: "powerbuilder",
            FileType.DATAWINDOW: "powerbuilder",
            FileType.QUERY: "sql",
            FileType.PROJECT: "powerbuilder",
        }

    def load_grammar(self, name: str, start: str | None = None, **kwargs) -> Lark:
        """Load and cache a grammar by name."""
        cache_key = f"{name}:{start}:{hash(frozenset(kwargs.items()))}"

        if cache_key in self._cache:
            return self._cache[cache_key]

        # Create basic grammar if file doesn't exist
        grammar_content = self._load_grammar_content(name)
        if not grammar_content:
            grammar_content = self._create_basic_grammar(name)

        try:
            parser_kwargs = {
                "parser": kwargs.get("parser", "earley"),
                "propagate_positions": True,
                "maybe_placeholders": True,
                "lexer": kwargs.get("lexer", "dynamic"),
                "import_paths": [str(self.grammar_dir)],
            }
            parser_kwargs.update(kwargs)

            if start:
                parser_kwargs["start"] = start

            parser = Lark(grammar_content, **parser_kwargs)
            self._cache[cache_key] = parser
            return parser

        except GrammarError as e:
            logger.warning("Grammar error in %s: %s, using fallback", name, e)
            # Return a minimal fallback parser
            fallback_grammar = """
start: statement*
statement: WORD+ ";"?
WORD: /[a-zA-Z_][a-zA-Z0-9_]*/
%import common.WS
%ignore WS
"""
            return Lark(fallback_grammar, parser="earley")

    def _load_grammar_content(self, name: str) -> str:
        """Load grammar content from file."""
        if name in self._grammars:
            return self._grammars[name]

        grammar_file = self.grammar_dir / f"{name}.lark"
        if grammar_file.exists():
            try:
                content = grammar_file.read_text(encoding="utf-8")
                self._grammars[name] = content
                return content
            except Exception as e:
                logger.warning("Failed to read grammar file %s: %s", grammar_file, e)

        return ""

    def _create_basic_grammar(self, name: str) -> str:
        """Create a basic grammar for fallback parsing."""
        if name == "sql":
            return """
start: sql_statement*
sql_statement: select_statement | insert_statement | update_statement | delete_statement
select_statement: "SELECT" column_list "FROM" table_name where_clause?
insert_statement: "INSERT" "INTO" table_name "VALUES" "(" value_list ")"
update_statement: "UPDATE" table_name "SET" assignment_list where_clause?
delete_statement: "DELETE" "FROM" table_name where_clause?
column_list: "*" | identifier ("," identifier)*
table_name: identifier
where_clause: "WHERE" expression
assignment_list: assignment ("," assignment)*
assignment: identifier "=" value
value_list: value ("," value)*
expression: identifier | value | expression operator expression
value: NUMBER | STRING | identifier
identifier: WORD
operator: "=" | "!=" | "<" | ">" | "<=" | ">=" | "AND" | "OR"

WORD: /[a-zA-Z_][a-zA-Z0-9_]*/
NUMBER: /\\d+/
STRING: /"[^"]*"/
%import common.WS
%ignore WS
"""
        else:
            return """
start: powerbuilder_file
powerbuilder_file: file_element*
file_element: function_definition | variable_declaration | statement
function_definition: access_modifier? "function" return_type identifier parameters ";" statement* "end" "function"
variable_declaration: type_name identifier ("=" expression)? ";"
statement: assignment_statement | if_statement | return_statement | expression_statement
assignment_statement: lvalue "=" expression ";"
if_statement: "if" expression "then" statement* ("else" statement*)? "end" "if"
return_statement: "return" expression? ";"
expression_statement: expression ";"
parameters: "(" parameter_list? ")"
parameter_list: parameter ("," parameter)*
parameter: type_name identifier
lvalue: identifier
expression: primary | binary_expression
binary_expression: expression operator expression
primary: identifier | literal
literal: NUMBER | STRING | BOOLEAN
return_type: type_name
type_name: identifier
access_modifier: "public" | "private" | "protected"
identifier: WORD
operator: "+" | "-" | "*" | "/" | "=" | "!=" | "<" | ">" | "<=" | ">=" | "and" | "or"

WORD: /[a-zA-Z_][a-zA-Z0-9_]*/
NUMBER: /\\d+/
STRING: /"[^"]*"/
BOOLEAN: "true" | "false"
%import common.WS
%ignore WS
"""

    def get_parser(self, file_type: FileType | str) -> Lark:
        """Get appropriate parser for file type."""
        if isinstance(file_type, str):
            ext = file_type.lstrip(".")
            if ext in FILE_EXTENSIONS:
                file_type = FILE_EXTENSIONS[ext]
            else:
                # Default to PowerBuilder
                return self.load_grammar("powerbuilder")

        grammar_name = self._file_type_mapping.get(file_type, "powerbuilder")
        return self.load_grammar(grammar_name)

    def clear_cache(self) -> None:
        """Clear grammar and parser caches."""
        self._cache.clear()
        self._grammars.clear()
        self._dependencies.clear()


# ============================================================================
# PREPROCESSOR SECTION
# ============================================================================


@dataclass
class PreprocessorState:
    """State for tracking preprocessor context."""

    in_binary_section: bool = False
    in_multiline_comment: bool = False
    characters_ignored: int = 0


class PowerBuilderPreprocessor:
    """Preprocessor for PowerBuilder source files."""

    # Regular expressions
    BINARY_SECTION_START = re.compile(r"Start of PowerBuilder Binary Data Section")
    EXPORT_INFO = re.compile(r"^\$PBExport[^\n]+", re.MULTILINE)
    RELEASE_NUMBER = re.compile(r"release\s+\d+\s*")
    SINGLE_LINE_COMMENT = re.compile(r"//[^\n]*")
    MULTI_LINE_COMMENT = re.compile(r"/\*.*?\*/", re.DOTALL)
    STRING = re.compile(r'"[^"]*"')
    ESPELETTE_NEWLINE = re.compile(r"&[ \t]*\n")

    def __init__(self, base_path: Path | None = None) -> None:
        """Initialize preprocessor."""
        self.base_path = base_path or Path.cwd()
        self.state = PreprocessorState()
        self.defines: dict[str, str] = {}
        self.includes: list[Path] = []
        self.processed_files: set[Path] = set()

    def preprocess(self, source: str, file_path: Path | None = None) -> str:
        """Preprocess PowerBuilder source code."""
        self.state = PreprocessorState()
        source = self._remove_export_header(source)
        source = self._process_content(source)
        source = self._remove_binary_sections(source)
        return self._join_multiline_strings(source)

    def _remove_export_header(self, source: str) -> str:
        """Remove $PBExportHeader section from source."""
        export_match = re.search(self.EXPORT_INFO, source)
        if not export_match:
            return source

        release_match = re.search(self.RELEASE_NUMBER, source[export_match.end() :])
        if release_match:
            header_end = export_match.end() + release_match.end()
        else:
            header_end = export_match.end()

        self.state.characters_ignored = header_end
        return source[header_end:]

    def _process_content(self, source: str) -> str:
        """Process source code content."""
        return source  # Simplified processing

    def _remove_binary_sections(self, source: str) -> str:
        """Remove binary data sections from source."""
        match = self.BINARY_SECTION_START.search(source)
        if match:
            return source[: match.start()]
        return source

    def _join_multiline_strings(self, source: str) -> str:
        """Join multiline strings using & continuation."""
        return self.ESPELETTE_NEWLINE.sub(" ", source)

    def remove_comments(self, source: str) -> str:
        """Remove comments from source code."""
        source = self.SINGLE_LINE_COMMENT.sub("", source)
        return self.MULTI_LINE_COMMENT.sub("", source)


@dataclass
class ImplicitDependency:
    """Represents an implicit dependency in PowerBuilder code."""

    name: str
    dependency_type: str
    usage_location: str | None = None
    line_number: int | None = None
    context: str | None = None


@dataclass
class DependencyContext:
    """Context for dependency resolution."""

    current_file: Path
    current_class: str | None = None
    dependencies: set[str] = field(default_factory=set)
    implicit_deps: list[ImplicitDependency] = field(default_factory=list)
    unresolved_symbols: set[str] = field(default_factory=set)


class ImplicitImportResolver:
    """Resolves implicit imports and dependencies in PowerBuilder code."""

    def __init__(self) -> None:
        self.builtin_functions = self._get_builtin_functions()
        self.builtin_types = self._get_builtin_types()

    def extract_dependencies(self, ast: ASTNode, file_path: Path) -> DependencyContext:
        """Extract all implicit dependencies from an AST."""
        context = DependencyContext(current_file=file_path)
        self._visit_node(ast, context)
        return context

    def _visit_node(
        self, node: Union[ASTNode, Any], context: DependencyContext
    ) -> None:
        """Visit AST nodes to extract dependencies."""
        if not node:
            return

        if isinstance(node, (FunctionCall, PBFunctionCall, PBMethodCall)):
            self._handle_function_call(node, context)
        elif isinstance(node, PBConstructorCall):
            self._handle_constructor_call(node, context)
        elif isinstance(node, VariableDeclaration):
            self._handle_variable_declaration(node, context)
        elif hasattr(node, "data"):
            if node.data == "class_definition":
                self._handle_class_definition_node(node, context)

        # Recursively visit children
        if hasattr(node, "get_children"):
            for child in node.get_children():
                self._visit_node(child, context)
        elif hasattr(node, "children"):
            for child in node.children:
                self._visit_node(child, context)

    def _handle_function_call(self, node: Any, context: DependencyContext) -> None:
        """Handle function calls."""
        func_name = self._get_function_name(node)
        if func_name and func_name not in self.builtin_functions:
            dep = ImplicitDependency(
                name=func_name,
                dependency_type="function",
                usage_location=context.current_class or str(context.current_file),
                context="function_call",
            )
            context.implicit_deps.append(dep)
            context.dependencies.add(func_name)

    def _handle_constructor_call(
        self, node: PBConstructorCall, context: DependencyContext
    ) -> None:
        """Handle constructor calls."""
        class_name = getattr(node, "class_name", None) or getattr(
            node, "type_name", None
        )
        if class_name and class_name not in self.builtin_types:
            dep = ImplicitDependency(
                name=class_name,
                dependency_type="class",
                usage_location=context.current_class or str(context.current_file),
                context="constructor_call",
            )
            context.implicit_deps.append(dep)
            context.dependencies.add(class_name)

    def _handle_variable_declaration(
        self, node: VariableDeclaration, context: DependencyContext
    ) -> None:
        """Handle variable declarations."""
        if hasattr(node, "type") and node.type:
            type_name = str(node.type)
            if type_name not in self.builtin_types:
                dep = ImplicitDependency(
                    name=type_name,
                    dependency_type="type",
                    usage_location=context.current_class or str(context.current_file),
                    context="variable_declaration",
                )
                context.implicit_deps.append(dep)
                context.dependencies.add(type_name)

    def _handle_class_definition_node(
        self, node: Any, context: DependencyContext
    ) -> None:
        """Handle class definition nodes."""
        # Extract class name and parent class
        class_name = None
        parent_class = None

        if hasattr(node, "children"):
            for child in node.children:
                if hasattr(child, "type") and child.type == "IDENTIFIER":
                    if class_name is None:
                        class_name = str(child.value)
                    else:
                        parent_class = str(child.value)

        if class_name:
            old_class = context.current_class
            context.current_class = class_name

            if parent_class and parent_class not in self.builtin_types:
                dep = ImplicitDependency(
                    name=parent_class,
                    dependency_type="class",
                    usage_location=f"class {class_name}",
                    context="inheritance",
                )
                context.implicit_deps.append(dep)
                context.dependencies.add(parent_class)

            # Continue visiting children
            self._visit_node(node, context)
            context.current_class = old_class

    def _get_function_name(self, node: Any) -> str | None:
        """Extract function name from a function call node."""
        if hasattr(node, "function_name"):
            return node.function_name
        if hasattr(node, "method_name"):
            return node.method_name
        if hasattr(node, "name"):
            return str(node.name)
        return None

    def _get_builtin_functions(self) -> set[str]:
        """Get set of PowerBuilder builtin functions."""
        return {
            "len",
            "trim",
            "left",
            "right",
            "mid",
            "pos",
            "replace",
            "upper",
            "lower",
            "asc",
            "char",
            "string",
            "space",
            "abs",
            "ceiling",
            "cos",
            "exp",
            "int",
            "log",
            "max",
            "min",
            "mod",
            "pi",
            "rand",
            "round",
            "sign",
            "sin",
            "sqrt",
            "tan",
            "truncate",
            "day",
            "month",
            "year",
            "hour",
            "minute",
            "second",
            "date",
            "datetime",
            "now",
            "today",
            "integer",
            "long",
            "double",
            "real",
            "decimal",
            "messagebox",
            "isnull",
            "setnull",
            "isvalid",
            "isnumber",
            "isdate",
            "istime",
            "classname",
            "typeof",
            "fileopen",
            "fileclose",
        }

    def _get_builtin_types(self) -> set[str]:
        """Get set of PowerBuilder builtin types."""
        return {
            "integer",
            "long",
            "string",
            "boolean",
            "real",
            "double",
            "decimal",
            "date",
            "time",
            "datetime",
            "blob",
            "any",
            "char",
            "byte",
            "window",
            "datawindow",
            "datastore",
            "transaction",
            "application",
            "menu",
            "userobject",
            "structure",
            "exception",
            "throwable",
            "runtimeerror",
        }


# ============================================================================
# PARSER SECTION
# ============================================================================


class PowerBuilderBaseParser(ABC):
    """Abstract base class for all PowerBuilder parsers."""

    PARSER_TYPE: ClassVar[str] = "base"
    SUPPORTED_EXTENSIONS: ClassVar[set[str]] = set()
    DEFAULT_PARSER_OPTIONS: ClassVar[dict[str, Any]] = {
        "parser": "earley",
        "propagate_positions": True,
        "maybe_placeholders": True,
        "lexer": "dynamic",
    }

    def __init__(self, base_path: Path | None = None, **parser_options: Any) -> None:
        """Initialize the base parser."""
        self.base_path = base_path or Path.cwd()
        self.parser_options = {**self.DEFAULT_PARSER_OPTIONS, **parser_options}
        self._current_file: Path | None = None
        self._parse_errors: list[dict[str, Any]] = []
        self._recovery_attempts: int = 0
        self._max_recovery_attempts: int = 3
        self._parser: Lark | None = None

    @property
    def parser(self) -> Lark:
        """Get or create the Lark parser instance."""
        if self._parser is None:
            self._parser = self._create_parser()
        return self._parser

    @abstractmethod
    def _create_parser(self) -> Lark:
        """Create the Lark parser instance."""

    @abstractmethod
    def parse(self, source: str | Path, **kwargs: Any) -> Tree | Any:
        """Parse PowerBuilder source code."""

    def supports(self, file_path: Path) -> bool:
        """Check if this parser supports the given file."""
        extension = file_path.suffix.lstrip(".")
        return extension.lower() in self.SUPPORTED_EXTENSIONS

    def parse_with_error_recovery(
        self, source: str, filename: str | None = None
    ) -> Tree:
        """Parse with automatic error recovery."""
        self._parse_errors.clear()
        self._recovery_attempts = 0

        try:
            tree = self.parser.parse(source)
            return tree
        except UnexpectedInput as e:
            self._record_parse_error(e, filename)
            return self._recover_from_error(source, e, filename)

    def _recover_from_error(
        self, source: str, error: UnexpectedInput, filename: str | None = None
    ) -> Tree:
        """Attempt to recover from a parse error."""
        self._recovery_attempts += 1

        if self._recovery_attempts > self._max_recovery_attempts:
            raise ParseRecoveryError(
                self._recovery_attempts, str(error), filename=filename
            )

        # Try to skip problematic line
        lines = source.splitlines()
        error_line = error.line - 1

        if 0 <= error_line < len(lines):
            lines[error_line] = f"// PARSE ERROR: {lines[error_line]}"
            modified_source = "\n".join(lines)

            try:
                return self.parser.parse(modified_source)
            except UnexpectedInput:
                pass

        # Create error tree as fallback
        error_token = Token(
            "PARSE_ERROR", str(error), line=error.line, column=error.column
        )
        return Tree("error", [error_token])

    def _record_parse_error(
        self, error: UnexpectedInput, filename: str | None = None
    ) -> None:
        """Record a parse error."""
        error_info = {
            "line": error.line,
            "column": error.column,
            "message": str(error),
            "filename": filename,
            "type": type(error).__name__,
        }
        self._parse_errors.append(error_info)

    def get_parse_errors(self) -> list[dict[str, Any]]:
        """Get list of parse errors encountered."""
        return self._parse_errors.copy()

    def has_errors(self) -> bool:
        """Check if any parse errors were encountered."""
        return bool(self._parse_errors)

    def clear_errors(self) -> None:
        """Clear all recorded parse errors."""
        self._parse_errors.clear()
        self._recovery_attempts = 0


class SQLParser(PowerBuilderBaseParser):
    """Parser for SQL statements in PowerBuilder code."""

    PARSER_TYPE: ClassVar[str] = "sql"
    SUPPORTED_EXTENSIONS: ClassVar[set[str]] = {"sql", "srq"}

    SQL_PATTERNS = [
        r"^\s*SELECT\s+",
        r"^\s*INSERT\s+",
        r"^\s*UPDATE\s+",
        r"^\s*DELETE\s+",
        r"^\s*CREATE\s+",
        r"^\s*DROP\s+",
        r"^\s*ALTER\s+",
        r"^\s*WITH\s+",
    ]

    def __init__(self, base_path: Path | None = None, **parser_options: Any) -> None:
        """Initialize SQL parser."""
        parser_options.setdefault("lexer", "basic")
        parser_options.setdefault("parser", "lalr")
        super().__init__(base_path, **parser_options)
        self._transformer: SQLTransformer | None = None
        self._optimizer: SQLOptimizer | None = None
        self._grammar_manager = GrammarManager()

    def _create_parser(self) -> Lark:
        """Create the SQL parser instance."""
        try:
            return self._grammar_manager.load_grammar(
                "sql", start="sql_statements", **self.parser_options
            )
        except Exception as e:
            logger.warning("Failed to create SQL parser: %s, using fallback", e)
            # Return basic SQL parser
            return self._grammar_manager.load_grammar("sql", **self.parser_options)

    def parse(
        self, source: str | Path, optimize: bool = False
    ) -> Tree | dict[str, Any] | list[Any]:
        """Parse SQL statements."""
        source_text, file_path = self._validate_source(source)
        self._current_file = file_path

        if not self._is_sql(source_text):
            logger.warning("Source does not appear to contain SQL statements")

        tree = self.parse_with_error_recovery(
            source_text, str(file_path) if file_path else None
        )

        # Transform to AST
        ast = self.transform_tree(tree, self.transformer)

        if optimize and self._optimizer:
            ast = self._optimizer.optimize(ast)

        return ast

    def _is_sql(self, source: str) -> bool:
        """Check if source contains SQL statements."""
        cleaned = self._remove_comments(source).strip()
        return any(
            re.match(pattern, cleaned, re.IGNORECASE | re.MULTILINE)
            for pattern in self.SQL_PATTERNS
        )

    def _remove_comments(self, source: str) -> str:
        """Remove SQL comments from source."""
        source = re.sub(r"--[^\n]*", "", source)
        return re.sub(r"/\*.*?\*/", "", source, flags=re.DOTALL)

    def _validate_source(self, source: str | Path) -> tuple[str, Path | None]:
        """Validate and normalize source input."""
        if isinstance(source, Path):
            if not source.exists():
                raise ParseError(
                    f"Source file not found: {source}", filename=str(source)
                )
            try:
                source_text = source.read_text(encoding="utf-8")
                return source_text, source
            except Exception as e:
                raise ParseError(
                    f"Failed to read source file: {e}", filename=str(source)
                )
        elif isinstance(source, str):
            return source, None
        else:
            raise ParseError(f"Invalid source type: {type(source).__name__}")

    def transform_tree(self, tree: Tree, transformer: Transformer | None = None) -> Any:
        """Transform parse tree to AST."""
        if transformer is None:
            return tree
        try:
            return transformer.transform(tree)
        except Exception as e:
            raise ASTConstructionError(
                node_type=tree.data if hasattr(tree, "data") else "unknown",
                reason=str(e),
            )

    @property
    def transformer(self) -> SQLTransformer:
        """Get or create the SQL transformer."""
        if self._transformer is None:
            self._transformer = SQLTransformer()
        return self._transformer


class UnifiedPowerBuilderParser:
    """Unified parser for all PowerBuilder file types."""

    # Map of file extensions to specialized parsers
    EXTENSION_PARSERS: dict[str, Any] = {
        "sql": SQLParser,
        "srq": SQLParser,
        "sra": "EnhancedPowerBuilderParser",
        "srw": "EnhancedPowerBuilderParser",
        "sru": "EnhancedPowerBuilderParser",
        "srf": "EnhancedPowerBuilderParser",
        "srm": "EnhancedPowerBuilderParser",
        "srs": "EnhancedPowerBuilderParser",
    }

    def __init__(
        self, base_path: Path | None = None, enable_error_recovery: bool = True
    ) -> None:
        """Initialize unified parser."""
        self.base_path = base_path or Path.cwd()
        self.enable_error_recovery = enable_error_recovery
        self._parser_cache: dict[Any, PowerBuilderBaseParser] = {}

    def parse(
        self, source: str | Path, parser_type: str | None = None
    ) -> Tree | dict[str, Any]:
        """Parse PowerBuilder source code."""
        if isinstance(source, Path):
            source_path = source
            with source.open(encoding="utf-8") as f:
                source_text = f.read()
        else:
            source_path = None
            source_text = source

        # Determine parser
        if parser_type:
            parser_class = self._get_parser_by_type(parser_type)
        elif source_path:
            parser_class = self._get_parser_by_extension(source_path.suffix.lstrip("."))
        else:
            parser_class = self._get_parser_by_content(source_text)

        if not parser_class:
            raise ValueError("Could not determine appropriate parser for source")

        # Get parser instance
        parser = self._get_parser_instance(parser_class)

        # Parse
        try:
            result = parser.parse(source_text)
            return result
        except Exception:
            if self.enable_error_recovery and hasattr(parser, "parse_with_fallback"):
                return parser.parse_with_fallback(source_text)
            raise

    def _get_parser_by_type(self, parser_type: str) -> Any:
        """Get parser class by type."""
        type_map = {
            "sql": SQLParser,
            "enhanced": "EnhancedPowerBuilderParser",
        }
        return type_map.get(parser_type.lower())

    def _get_parser_by_extension(self, extension: str) -> Any:
        """Get parser class by extension."""
        return self.EXTENSION_PARSERS.get(extension.lower())

    def _get_parser_by_content(self, content: str) -> Any:
        """Get parser class by content analysis."""
        lines = content.strip().split("\n", 5)
        header = " ".join(lines[:5]).upper()

        if any(
            pattern in header for pattern in ["SELECT", "INSERT", "UPDATE", "DELETE"]
        ):
            return SQLParser

        return "EnhancedPowerBuilderParser"

    def _get_parser_instance(self, parser_class: Any) -> PowerBuilderBaseParser:
        """Get or create parser instance."""
        if isinstance(parser_class, str):
            # Return a basic parser for string types
            return BasicPowerBuilderParser(self.base_path)

        if parser_class not in self._parser_cache:
            instance = parser_class(self.base_path)
            self._parser_cache[parser_class] = instance
        return self._parser_cache[parser_class]


class BasicPowerBuilderParser(PowerBuilderBaseParser):
    """Basic PowerBuilder parser implementation."""

    PARSER_TYPE: ClassVar[str] = "powerbuilder"
    SUPPORTED_EXTENSIONS: ClassVar[set[str]] = {
        "sra",
        "srw",
        "sru",
        "srf",
        "srm",
        "srs",
    }

    def __init__(self, base_path: Path | None = None) -> None:
        """Initialize basic parser."""
        super().__init__(base_path)
        self._grammar_manager = GrammarManager()

    def _create_parser(self) -> Lark:
        """Create the parser instance."""
        return self._grammar_manager.load_grammar("powerbuilder", parser="earley")

    def parse(self, source: str | Path, **kwargs: Any) -> Tree | Any:
        """Parse PowerBuilder source code."""
        source_text, file_path = self._validate_source(source)
        self._current_file = file_path

        return self.parse_with_error_recovery(
            source_text, str(file_path) if file_path else None
        )

    def _validate_source(self, source: str | Path) -> tuple[str, Path | None]:
        """Validate source input."""
        if isinstance(source, Path):
            if not source.exists():
                raise ParseError(f"Source file not found: {source}")
            source_text = source.read_text(encoding="utf-8")
            return source_text, source
        return str(source), None


# Specialized parsers
class PowerBuilderPseudocodeParser(PowerBuilderBaseParser):
    """Parser for PowerBuilder pseudocode syntax."""

    PARSER_TYPE: ClassVar[str] = "pseudocode"
    SUPPORTED_EXTENSIONS: ClassVar[set[str]] = set()

    def __init__(self) -> None:
        """Initialize pseudocode parser."""
        super().__init__()
        self._grammar_manager = GrammarManager()

    def _create_parser(self) -> Lark:
        """Create parser."""
        return self._grammar_manager.load_grammar("powerbuilder", start="start")

    def parse(self, source: str | Path, **kwargs: Any) -> Tree:
        """Parse pseudocode."""
        if isinstance(source, Path):
            source = source.read_text(encoding="utf-8")
        return self.parse_with_error_recovery(str(source))


class PowerBuilderTransactionParser:
    """Parser for PowerBuilder transaction statements."""

    def __init__(self, base_path: Path | None = None) -> None:
        """Initialize transaction parser."""
        self.base_path = base_path or Path.cwd()

    def parse_transaction_statement(self, source: str) -> PBTransactionStatement:
        """Parse a transaction statement."""
        source = source.strip().upper()

        if source.startswith("CONNECT"):
            return PBTransactionStatement(
                statement_type=PBStatementType.CONNECT,
                transaction_object="sqlca",
            )
        elif source.startswith("COMMIT"):
            return PBTransactionStatement(
                statement_type=PBStatementType.COMMIT,
                transaction_object="sqlca",
            )
        elif source.startswith("ROLLBACK"):
            return PBTransactionStatement(
                statement_type=PBStatementType.ROLLBACK,
                transaction_object="sqlca",
            )

        return PBTransactionStatement(
            statement_type="UNKNOWN",
            transaction_object="sqlca",
        )


class TypeParser:
    """Parser for PowerBuilder custom types and enums."""

    def __init__(self) -> None:
        """Initialize type parser."""
        self.types: dict[str, Any] = {}

    def parse_type_declaration(self, tree: Tree) -> Any:
        """Parse a type declaration tree."""
        name = None
        parent_type = None
        is_global = False

        for child in tree.children:
            if isinstance(child, Token):
                if child.type == "IDENTIFIER" and name is None:
                    name = str(child)
                elif child.value.lower() == "global":
                    is_global = True

        # Create basic custom type
        if name:
            type_obj = CustomType(name, TypeCategory.CUSTOM, parent_type)
            type_obj.is_global = is_global
            self.types[name] = type_obj
            return type_obj

        return None


# ============================================================================
# TRANSFORMER SECTION
# ============================================================================


class PowerBuilderTransformer(Transformer):
    """Transform Lark parse tree to PowerBuilder AST."""

    def __init__(self) -> None:
        """Initialize the transformer."""
        super().__init__()

    def _extract_location(self, node: Any) -> dict[str, Any]:
        """Extract location information from a node."""
        location = {}
        if hasattr(node, "meta"):
            meta = node.meta
            if hasattr(meta, "line"):
                location["line"] = meta.line
            if hasattr(meta, "column"):
                location["column"] = meta.column
        return location

    def _create_ast_node(
        self, node_type: str, items: list[Any], meta: Any = None, **kwargs
    ) -> dict[str, Any]:
        """Create an AST node with proper type and location."""
        ast_node = {"type": node_type, "node_type": node_type, **kwargs}

        if meta:
            location = self._extract_location(meta)
            ast_node.update(location)
        elif items and hasattr(items[0], "meta"):
            location = self._extract_location(items[0])
            ast_node.update(location)

        return ast_node

    def powerbuilder_file(self, items: list[Any]) -> dict[str, Any]:
        """Transform the root file node."""
        return {"type": "file", "elements": items}

    def function_definition(self, items: list[Any]) -> FunctionDefinition:
        """Transform function definition."""
        items = [item for item in items if item is not None]

        # Parse function components
        idx = 0
        access_modifier = None

        # Check for access modifier
        if items and str(items[idx]).lower() in ["public", "private", "protected"]:
            access_modifier = str(items[idx])
            idx += 1

        # Skip 'function' keyword
        if idx < len(items) and str(items[idx]).lower() == "function":
            idx += 1

        # Get return type, name, parameters
        return_type = items[idx] if idx < len(items) else None
        name = str(items[idx + 1]) if idx + 1 < len(items) else "unknown"
        parameters = items[idx + 2] if idx + 2 < len(items) else []

        # Find statements
        statements_idx = idx + 3
        if statements_idx < len(items) and str(items[statements_idx]) == ";":
            statements_idx += 1
        statements = items[statements_idx] if statements_idx < len(items) else []

        # Create signature
        sig = Signature(
            name=name,
            return_type=self._convert_type(return_type)
            if return_type
            else Type(name="void"),
            parameters=parameters if isinstance(parameters, list) else [],
        )

        return FunctionDefinition(
            signature=sig,
            body=Block(statements=statements if isinstance(statements, list) else []),
        )

    def parameters(self, items: list[Any]) -> list[Parameter]:
        """Transform parameters."""
        return items[1] if len(items) > 2 and items[1] else []

    def parameter(self, items: list[Any]) -> Parameter:
        """Transform a parameter."""
        name = None
        type_name = None
        modifier = None

        if len(items) >= 2:
            type_name = str(items[0]) if items[0] else None
            name = str(items[1]) if items[1] else None

        return Parameter(
            name=name,
            type=self._convert_type(type_name) if type_name else None,
            is_ref=(modifier == "ref"),
        )

    def statement(self, items: list[Any]) -> Any:
        """Pass through statements."""
        return items[0] if items else None

    def assignment_statement(self, items: list[Any]) -> ASTAssignment:
        """Transform assignment statement."""
        target = items[0] if items else None
        value = items[2] if len(items) > 2 else None
        return ASTAssignment(target=target, value=value)

    def return_statement(self, items: list[Any]) -> ReturnStatement:
        """Transform return statement."""
        value = None
        for item in items[1:]:
            if item and str(item) != ";":
                value = item
                break
        return ReturnStatement(value=value)

    def if_statement(self, items: list[Any]) -> IfStatement:
        """Transform if statement."""
        condition = None
        then_statements = []
        else_statements = []

        # Simple parsing - extract condition and statements
        for i, item in enumerate(items):
            if str(item).lower() == "if" and i + 1 < len(items):
                condition = items[i + 1]
            elif str(item).lower() == "then":
                # Collect statements after then
                j = i + 1
                while j < len(items) and str(items[j]).lower() not in ["else", "end"]:
                    if isinstance(items[j], list):
                        then_statements.extend(items[j])
                    else:
                        then_statements.append(items[j])
                    j += 1
            elif str(item).lower() == "else":
                # Collect statements after else
                j = i + 1
                while j < len(items) and str(items[j]).lower() != "end":
                    if isinstance(items[j], list):
                        else_statements.extend(items[j])
                    else:
                        else_statements.append(items[j])
                    j += 1

        return IfStatement(
            condition=condition or Literal(value=True),
            then_branch=Block(statements=then_statements),
            else_branch=Block(statements=else_statements) if else_statements else None,
        )

    def expression(self, items: list[Any]):
        """Pass through expressions."""
        return items[0] if len(items) == 1 else items

    def primary(self, items: list[Any]):
        """Transform primary expression."""
        if not items:
            return None

        item = items[0]

        if isinstance(item, Token):
            if item.type == "IDENTIFIER":
                return Variable(name=str(item))
            elif item.type == "INT":
                return IntegerLiteral(value=int(item))
            elif item.type == "STRING":
                value = str(item)[1:-1] if len(str(item)) > 1 else str(item)
                return StringLiteral(value=value)
            elif item.type == "TRUE":
                return BooleanLiteral(value=True)
            elif item.type == "FALSE":
                return BooleanLiteral(value=False)

        return item

    def _convert_type(self, type_name: Any) -> Type:
        """Convert type name to Type object."""
        if type_name is None:
            return Type(name="any", category=TypeCategory.BASIC)

        type_str = str(type_name).lower()

        basic_types = {
            "integer": TypeCategory.NUMERIC,
            "string": TypeCategory.TEXT,
            "boolean": TypeCategory.LOGICAL,
        }

        if type_str in basic_types:
            return BasicType(name=type_str, category=basic_types[type_str])

        return CustomType(name=type_str, category=TypeCategory.CUSTOM)


class SQLTransformer(Transformer):
    """Transforms SQL parse trees into SQL AST nodes."""

    def __init__(self, visit_tokens: bool = True) -> None:
        """Initialize SQL transformer."""
        super().__init__(visit_tokens)

    def sql_statements(self, items: list[Any]) -> list[Any]:
        """Transform multiple SQL statements."""
        return [item for item in items if item is not None]

    def sql_statement(self, items: list[Any]) -> Any:
        """Transform a single SQL statement."""
        return items[0] if items else None

    def select_statement(self, items: list[Any]) -> SQLSelectStatement:
        """Transform SELECT statement."""
        stmt = SQLSelectStatement()

        for item in items:
            if isinstance(item, Tree):
                if item.data == "result_columns":
                    stmt.result_columns = self._process_result_columns(item)
                elif item.data == "from_clause":
                    stmt.from_clause = self.transform(item)
                elif item.data == "where_clause":
                    stmt.where_clause = self.transform(item)

        return stmt

    def _process_result_columns(self, tree: Tree) -> list[Any]:
        """Process result columns from tree."""
        columns = []
        for child in tree.children:
            if isinstance(child, Tree):
                col = self.transform(child)
                columns.append(col)
        return columns

    def column_reference(self, items: list[Any]) -> SQLColumn:
        """Transform column reference."""
        if len(items) == 1:
            return SQLColumn(column_name=str(items[0]))
        elif len(items) >= 3:
            return SQLColumn(table_name=str(items[0]), column_name=str(items[2]))
        return SQLColumn(column_name="unknown")

    def table_reference(self, items: list[Any]) -> SQLTable:
        """Transform table reference."""
        if len(items) == 1:
            return SQLTable(table_name=str(items[0]))
        elif len(items) == 2:
            return SQLTable(table_name=str(items[0]), alias=str(items[1]))
        return SQLTable(table_name="unknown")

    def identifier(self, items: list[Any]) -> str:
        """Transform identifier to string."""
        return str(items[0]) if items else ""

    def number(self, items: list[Any]) -> NumberLiteral:
        """Transform number literal."""
        if items:
            return NumberLiteral(value=int(items[0]))
        return NumberLiteral(value=0)

    def string_literal(self, items: list[Any]) -> ASTStringLiteral:
        """Transform string literal."""
        if items:
            value = str(items[0])
            if value.startswith(("'", '"')) and value.endswith(("'", '"')):
                value = value[1:-1]
            return ASTStringLiteral(value=value)
        return ASTStringLiteral(value="")


# ============================================================================
# LIBRARY AND RESOLUTION SECTION
# ============================================================================


@dataclass
class LibraryInfo:
    """Information about a loaded library."""

    path: Path
    load_time: float
    objects: dict[str, Any] = field(default_factory=dict)
    dependencies: set[str] = field(default_factory=set)
    is_compiled: bool = False


@dataclass
class SymbolInfo:
    """Information about a symbol."""

    name: str
    library_path: Path
    object_type: str
    ast: Any
    dependencies: set[str] = field(default_factory=set)
    dependents: set[str] = field(default_factory=set)


class SymbolCache:
    """Thread-safe cache for parsed symbols."""

    def __init__(self, max_size: int = 1000) -> None:
        self._cache: dict[str, SymbolInfo] = {}
        self._access_order: list[str] = []
        self._lock = Lock()
        self.max_size = max_size

    def get(self, key: str) -> SymbolInfo | None:
        """Get a symbol from cache."""
        with self._lock:
            if key in self._cache:
                self._access_order.remove(key)
                self._access_order.append(key)
                return self._cache[key]
        return None

    def put(self, key: str, value: SymbolInfo) -> None:
        """Add a symbol to cache."""
        with self._lock:
            if key in self._cache:
                self._access_order.remove(key)
                self._access_order.append(key)
                self._cache[key] = value
            else:
                if len(self._cache) >= self.max_size:
                    lru_key = self._access_order.pop(0)
                    del self._cache[lru_key]
                self._cache[key] = value
                self._access_order.append(key)

    def clear(self) -> None:
        """Clear the cache."""
        with self._lock:
            self._cache.clear()
            self._access_order.clear()


class LibraryManager:
    """Manages PowerBuilder library files."""

    OBJECT_PREFIXES = {
        "n_": "userobject",
        "u_": "userobject",
        "w_": "window",
        "d_": "datawindow",
        "m_": "menu",
        "f_": "function",
    }

    def __init__(
        self, library_paths: list[Path] | None = None, cache_size: int = 1000
    ) -> None:
        """Initialize library manager."""
        self.library_paths = library_paths or []
        self.libraries: dict[Path, LibraryInfo] = {}
        self.symbol_cache = SymbolCache(cache_size)
        self.symbol_index: dict[str, Path] = {}
        self.dependency_graph: dict[str, set[str]] = defaultdict(set)
        self.parser = None
        self._lock = Lock()

    def _get_parser(self):
        """Get parser instance."""
        if self.parser is None:
            self.parser = UnifiedPowerBuilderParser()
        return self.parser

    def load_library(self, library_path: Path) -> LibraryInfo:
        """Load a PowerBuilder library file."""
        library_path = Path(library_path).resolve()

        if library_path in self.libraries:
            return self.libraries[library_path]

        start_time = time.time()
        temp_dir = Path(f"/tmp/pb_lib_extract_{library_path.stem}_{os.getpid()}")
        temp_dir.mkdir(parents=True, exist_ok=True)

        try:
            # Extract library contents
            extract_pbl(str(library_path), str(temp_dir))

            lib_info = LibraryInfo(
                path=library_path,
                load_time=time.time() - start_time,
                is_compiled=library_path.suffix.lower() == ".pbd",
            )

            # Parse extracted objects
            self._parse_library_objects(lib_info, temp_dir)

            with self._lock:
                self.libraries[library_path] = lib_info

            return lib_info

        except Exception as e:
            logger.error("Failed to load library %s: %s", library_path, e)
            raise
        finally:
            # Clean up
            import shutil

            if temp_dir.exists():
                shutil.rmtree(temp_dir, ignore_errors=True)

    def _parse_library_objects(self, lib_info: LibraryInfo, extract_dir: Path) -> None:
        """Parse all objects extracted from a library."""
        parser = self._get_parser()

        for obj_file in extract_dir.iterdir():
            if obj_file.is_file() and obj_file.suffix.lower() in [
                ".sru",
                ".srw",
                ".srf",
                ".srm",
            ]:
                try:
                    ast = parser.parse(obj_file)
                    obj_name = obj_file.stem.lower()
                    lib_info.objects[obj_name] = ast

                    symbol_info = SymbolInfo(
                        name=obj_name,
                        library_path=lib_info.path,
                        object_type=self._detect_object_type(obj_name, obj_file.suffix),
                        ast=ast,
                    )

                    with self._lock:
                        self.symbol_index[obj_name] = lib_info.path
                        self.symbol_cache.put(obj_name, symbol_info)

                except Exception as e:
                    logger.error("Failed to parse %s: %s", obj_file, e)

    def _detect_object_type(self, obj_name: str, file_ext: str) -> str:
        """Detect object type from name and extension."""
        obj_name_lower = obj_name.lower()

        for prefix, obj_type in self.OBJECT_PREFIXES.items():
            if obj_name_lower.startswith(prefix):
                return obj_type

        ext_map = {
            ".srw": "window",
            ".sru": "userobject",
            ".srf": "function",
            ".srm": "menu",
            ".srs": "structure",
            ".sra": "application",
        }

        return ext_map.get(file_ext.lower(), "unknown")

    def get_symbol(
        self, symbol_name: str, search_order: list[Path] | None = None
    ) -> SymbolInfo | None:
        """Get a symbol from the libraries."""
        symbol_name_lower = symbol_name.lower()

        # Check cache first
        cached = self.symbol_cache.get(symbol_name_lower)
        if cached:
            return cached

        # Search libraries
        search_paths = search_order or list(self.libraries.keys())

        for lib_path in search_paths:
            if lib_path in self.libraries:
                lib_info = self.libraries[lib_path]
                if symbol_name_lower in lib_info.objects:
                    symbol_info = SymbolInfo(
                        name=symbol_name_lower,
                        library_path=lib_path,
                        object_type=self._detect_object_type(symbol_name_lower, ""),
                        ast=lib_info.objects[symbol_name_lower],
                    )
                    self.symbol_cache.put(symbol_name_lower, symbol_info)
                    return symbol_info

        return None


@dataclass
class ResolutionContext:
    """Context for type resolution."""

    file_path: Path
    resolved_types: dict[str, PBType] = field(default_factory=dict)
    unresolved_symbols: set[str] = field(default_factory=set)
    imported_types: dict[str, str] = field(default_factory=dict)
    imported_modules: set[str] = field(default_factory=set)
    namespace: str | None = None

    def add_resolved_type(self, name: str, type_info: PBType) -> None:
        """Add a resolved type."""
        self.resolved_types[name] = type_info
        self.unresolved_symbols.discard(name)

    def is_resolved(self, name: str) -> bool:
        """Check if a type is resolved."""
        return name in self.resolved_types


class TypeResolver:
    """Resolves types in PowerBuilder code."""

    def __init__(self, library_manager: LibraryManager | None = None) -> None:
        """Initialize type resolver."""
        self.contexts: dict[Path, ResolutionContext] = {}
        self.type_registry = PBTypeRegistry()
        self.library_manager = library_manager
        self._type_cache: dict[str, PBType] = {}
        self._initialize_system_types()

    def _initialize_system_types(self) -> None:
        """Initialize system types."""
        object_types = [
            ("window", "window"),
            ("datawindow", "datawindow"),
            ("menu", "menu"),
            ("application", "application"),
            ("userobject", "userobject"),
        ]

        for type_name, base_class in object_types:
            custom_type = PBCustomType(name=type_name, base_class=base_class)
            custom_type.category = "object"
            self.type_registry.register(custom_type)

    def create_context(
        self, file_path: Path, namespace: str | None = None
    ) -> ResolutionContext:
        """Create a resolution context for a file."""
        context = ResolutionContext(file_path, namespace=namespace)
        self.contexts[file_path] = context
        return context

    def resolve_type(self, type_name: str, context: ResolutionContext) -> PBType | None:
        """Resolve a type name in the given context."""
        cache_key = f"{context.file_path}:{type_name}"
        if cache_key in self._type_cache:
            return self._type_cache[cache_key]

        resolved_type = self._resolve_type_internal(type_name, context)

        if resolved_type:
            self._type_cache[cache_key] = resolved_type
            context.add_resolved_type(type_name, resolved_type)
        else:
            context.unresolved_symbols.add(type_name)

        return resolved_type

    def _resolve_type_internal(
        self, type_name: str, context: ResolutionContext
    ) -> PBType | None:
        """Internal type resolution logic."""
        clean_name = type_name.strip().lower()

        # Check if already resolved
        if context.is_resolved(type_name):
            return context.resolved_types[type_name]

        # Check type registry
        type_info = self.type_registry.get(clean_name)
        if type_info:
            return type_info

        # Check for custom types through library manager
        if self.library_manager:
            symbol_info = self.library_manager.get_symbol(type_name)
            if symbol_info:
                return self._create_custom_type_from_symbol(symbol_info.ast)

        return None

    def _create_custom_type_from_symbol(self, symbol: Any) -> PBCustomType:
        """Create custom type from symbol."""
        if isinstance(symbol, dict):
            type_name = symbol.get("name", "unknown")
            base_class = symbol.get("base_class", "object")
            return PBCustomType(name=type_name, base_class=base_class)
        return PBCustomType(name="unknown", base_class="object")


# ============================================================================
# RECOVERY AND FACTORY SECTION
# ============================================================================


class EnhancedErrorRecovery:
    """Enhanced error recovery strategy."""

    def __init__(self, parser=None, error_collector=None) -> None:
        """Initialize error recovery handler."""
        self.parser = parser
        self.error_collector = error_collector or ParseErrorCollector()
        self.errors: list[str] = []

    def recover(self, error: Exception, parser=None) -> None:
        """Attempt to recover from a parse error."""
        self.errors.append(str(error))

    def parse_with_recovery(self, text: str) -> Tree:
        """Parse text with error recovery."""
        if not self.parser:
            raise ValueError("No parser instance provided")

        try:
            return self.parser.parse(text)
        except Exception as e:
            self.recover(e, self.parser)
            return Tree("error", [Token("ERROR", str(e))])


class ErrorRecoveryTransformer(Transformer):
    """Transformer that handles error nodes."""

    def __init__(self, error_collector: ParseErrorCollector | None = None) -> None:
        """Initialize transformer."""
        super().__init__()
        self.error_collector = error_collector or ParseErrorCollector()

    def error_node(self, children) -> Tree:
        """Handle error nodes."""
        return Tree("error", children)


class ParseCoordinatorFactory:
    """Factory for creating parse coordinators."""

    @staticmethod
    def create_simple(
        input_dir: str | Path | None = None,
        output_dir: str | Path | None = None,
        library_path: str | Path | None = None,
        enable_preprocessing: bool = True,
        resolve_imports: bool = True,
        **kwargs,
    ) -> Any:
        """Create a simple parse coordinator."""
        # Create components
        grammar_manager = GrammarManager()
        library_manager = LibraryManager(
            library_paths=[Path(library_path)] if library_path else None
        )
        type_resolver = TypeResolver(library_manager)
        imports_resolver = ImplicitImportResolver() if resolve_imports else None
        preprocessor = PowerBuilderPreprocessor() if enable_preprocessing else None
        parser = UnifiedPowerBuilderParser()
        transformer = PowerBuilderTransformer()

        # Return a mock coordinator for now
        return {
            "grammar_manager": grammar_manager,
            "library_manager": library_manager,
            "type_resolver": type_resolver,
            "parser": parser,
            "transformer": transformer,
        }


# Convenience function
def create_parse_coordinator(
    input_dir: str | Path | None = None,
    output_dir: str | Path | None = None,
    **kwargs,
) -> Any:
    """Create a parse coordinator with default configuration."""
    return ParseCoordinatorFactory.create_simple(
        input_dir=input_dir, output_dir=output_dir, **kwargs
    )


# ============================================================================
# VISITOR PATTERN SECTION
# ============================================================================

# Stub classes for nodes that don't exist yet but are referenced in the visitor
# These should be implemented as needed or the visitor methods should be removed


@dataclass
class PBAccessModifierDefinerNode(PBNode):
    """Stub for access modifier definer node."""

    access_modifier: Any = None


class PBAccessModifierNode(PBNode):
    """Stub for access modifier node."""

    access_modifier: str = ""


class PBBehavioralAliasNode(PBNode):
    """Stub for behavioral alias node."""

    alias: Any = None


class PBBehavioralLibraryNode(PBNode):
    """Stub for behavioral library node."""

    library_file: Any = None


class PBBehavioralOptionNode(PBNode):
    """Stub for behavioral option node."""

    option: Any = None
    behavioral_option: Any = None


class PBCommonFileNode(PBNode):
    """Stub for common file node."""

    file_content: Any = None
    file_statements: Any = None


class PBAccessOrTypeNode(PBNode):
    """Stub for access or type node."""

    access_or_type: Any = None


class PBArrayDesignationNode(PBNode):
    """Stub for array designation node."""

    array_designation: str = ""


class PBAssignationNode(PBNode):
    """Stub for assignation node."""

    expression: Any = None


class PBAssignationStatementNode(PBNode):
    """Stub for assignation statement node."""

    access_or_type: Any = None
    expression_action: Any = None
    assignation: Any = None


class PBBooleanValueNode(PBNode):
    """Stub for boolean value node."""

    boolean_value: str = ""


class PBCallStatementNode(PBNode):
    """Stub for call statement node."""

    variable: Any = None
    identifier: Any = None
    event_type: Any = None


class PBCaseElseNode(PBNode):
    """Stub for case else node."""

    statements: Any = None
    statement: Any = None


class PBCaseNode(PBNode):
    """Stub for case node."""

    case: Any = None


class PBChooseCaseNode(PBNode):
    """Stub for choose case node."""

    expression: Any = None
    cases: list[Any] = field(default_factory=list)
    case_else: Any = None


class PBConditionNode(PBNode):
    """Stub for condition node."""

    expression: Any = None


class PBConstantNode(PBNode):
    """Stub for constant node."""

    constant: str = ""


class PBContinueStatementNode(PBNode):
    """Stub for continue statement node."""

    continue_statement: str = ""


class PBCreateInstructionNode(PBNode):
    """Stub for create instruction node."""

    variable: Any = None


class PBCreateUsingInstructionNode(PBNode):
    """Stub for create using instruction node."""

    expression: Any = None


class PBCustomCallStatementNode(PBNode):
    """Stub for custom call statement node."""

    identifier: Any = None


class PBDescriptorNode(PBNode):
    """Stub for descriptor node."""

    expression: Any = None


class PBDestroyStatementNode(PBNode):
    """Stub for destroy statement node."""

    expression: Any = None


class PBDoLoopUntilNode(PBNode):
    """Stub for do loop until node."""

    statements: Any = None
    expression: Any = None


class PBDoLoopWhileNode(PBNode):
    """Stub for do loop while node."""

    statements: Any = None
    expression: Any = None


class PBDoUntilLoopNode(PBNode):
    """Stub for do until loop node."""

    expression: Any = None
    statements: Any = None


class PBDoWhileLoopNode(PBNode):
    """Stub for do while loop node."""

    expression: Any = None
    statements: Any = None


class PBDynamicMethodInvocationNode(PBNode):
    """Stub for dynamic method invocation node."""

    unchecked_identifier: Any = None
    function_arguments: Any = None


class PBElseIfNode(PBNode):
    """Stub for else if node."""

    expression: Any = None
    statements: Any = None


class PBElseNode(PBNode):
    """Stub for else node."""

    statements: Any = None


class PBElseOnLineNode(PBNode):
    """Stub for else on line node."""

    statement: Any = None


class PBEndForwardNode(PBNode):
    """Stub for end forward node."""

    end_forward: str = ""


class PBExitStatementNode(PBNode):
    """Stub for exit statement node."""

    exit_statement: str = ""


class PBExportNode(PBNode):
    """Stub for export node."""

    format_type: Any = None
    parameters: Any = None


class PBExpressionActionNode(PBNode):
    """Stub for expression action node."""

    action: Any = None
    expression_action: Any = None


class PBExpressionListNode(PBNode):
    """Stub for expression list node."""

    expressions: list[Any] = field(default_factory=list)


class PBExpressionNode(PBNode):
    """Stub for expression node."""

    expression: Any = None
    expression_action: Any = None


class PBExpressionOperatorNode(PBNode):
    """Stub for expression operator node."""

    expression_operator: str = ""


# Additional stub classes for missing array nodes
@dataclass
class PBArrayNode(PBNode):
    """Stub for array node."""

    expressions: list[Any] = field(default_factory=list)


class PBArrayPositionNode(PBNode):
    """Stub for array position node."""

    expressions: list[Any] = field(default_factory=list)


class PBArrayWithSizeNode(PBNode):
    """Stub for array with size node."""

    expressions: list[Any] = field(default_factory=list)


# Stub classes for missing SQL nodes
@dataclass
class PBCloseSqlCursorNode(PBNode):
    """Stub for close SQL cursor node."""

    cursor_name: Any = None
    identifier: Any = None


class PBDeclareCursorNode(PBNode):
    """Stub for declare cursor node."""

    cursor_name: Any = None
    sql_query: Any = None
    identifier: Any = None
    target: Any = None


class PBDeclareProcedureNode(PBNode):
    """Stub for declare procedure node."""

    procedure_name: Any = None
    parameters: Any = None


class PBExecuteProcedureNode(PBNode):
    """Stub for execute procedure node."""

    procedure_name: Any = None
    arguments: Any = None
    using_clause: Any = None


# Stub classes for missing function argument nodes
@dataclass
class PBArgumentNode(PBNode):
    """Stub for argument node."""

    argument_option: Any = None
    type: Any = None
    identifier: Any = None
    array_with_size: Any = None


class PBArgumentOptionNode(PBNode):
    """Stub for argument option node."""

    argument_option: str = ""


class PBArgumentsNode(PBNode):
    """Stub for arguments node."""

    arguments: list[Any] = field(default_factory=list)


class PBDefaultVariableNode(PBNode):
    """Stub for default variable node."""

    default_value: Any = None
    default_variable: Any = None


# Stub classes for missing event nodes
@dataclass
class PBEventAttributeNode(PBNode):
    """Stub for event attribute node."""

    attribute: Any = None
    return_type: Any = None
    event_name: Any = None


class PBEventDeclarationNode(PBNode):
    """Stub for event declaration node."""

    event_name: Any = None
    event_type: Any = None
    return_type: Any = None
    event_reference_name: Any = None
    custom_call_statement: Any = None
    statements: Any = None


class PBEventInvocationNode(PBNode):
    """Stub for event invocation node."""

    event_name: Any = None
    arguments: Any = None
    identifier: Any = None
    function_arguments: Any = None


class PBEventLongNode(PBNode):
    """Stub for event long node."""

    event_long: str = ""
    function_argument: Any = None


class PBEventNameNode(PBNode):
    """Stub for event name node."""

    event_name: str = ""


class PBEventReferenceNameNode(PBNode):
    """Stub for event reference name node."""

    reference_name: str = ""
    object_class: Any = None
    event_name: Any = None
    arguments: Any = None


class PBEventTriggeringOrPostingNode(PBNode):
    """Stub for event triggering or posting node."""

    event_action: Any = None
    identifiers: Any = None
    array_positions: Any = None
    event_name: Any = None
    event_word: Any = None
    event_long: Any = None


class PBEventTypeNode(PBNode):
    """Stub for event type node."""

    event_type: str = ""


class PBEventWordNode(PBNode):
    """Stub for event word node."""

    event_word: str = ""
    function_argument: Any = None


# Stub classes for missing datawindow nodes
@dataclass
class PBColumnDefinitionNode(PBNode):
    """Stub for column definition node."""

    column_name: Any = None
    column_type: Any = None
    options: Any = None


class PBColumnNameOptionNode(PBNode):
    """Stub for column name option node."""

    column_name_option: str = ""
    expression: Any = None


class PBColumnNode(PBNode):
    """Stub for column node."""

    column_data: Any = None
    column_definition: Any = None


class PBColumnTypeOptionNode(PBNode):
    """Stub for column type option node."""

    column_type_option: str = ""
    expression: Any = None


class PBDataWindowFileNode(PBNode):
    """Stub for data window file node."""

    file_content: Any = None
    file_statements: Any = None


class PBDataWindowNode(PBNode):
    """Stub for data window node."""

    datawindow_content: Any = None
    parameters: Any = None


class PowerBuilderASTVisitor(ABC):
    """Abstract base class for PowerBuilder AST visitors.

    Features:
    - Generic visit method for any node type
    - Visit collection of nodes
    - Type-specific visit methods for each AST node type
    """

    def visit(self, node: Any | None) -> Any:
        """Visit a node.

        Args:
            node: Node to visit

        Returns:
            Result of visiting the node
        """
        if node is None:
            return None
        return node.accept_visitor(self)

    def visit_all(self, nodes: list[Any] | None) -> None:
        """Visit a collection of nodes.

        Args:
            nodes: List of nodes to visit
        """
        if nodes is not None:
            for node in nodes:
                self.visit(node)

    @abstractmethod
    def visit_access(self, node: PBAccessNode) -> None:
        """Visit an access node."""
        self.visit(node.accessed)
        self.visit(node.array_position)

    @abstractmethod
    def visit_access_modifier(self, node: PBAccessModifierNode) -> str:
        """Visit an access modifier node."""
        return node.access_modifier

    @abstractmethod
    def visit_access_modifier_definer(self, node: PBAccessModifierDefinerNode) -> None:
        """Visit an access modifier definer node."""
        self.visit(node.access_modifier)

    @abstractmethod
    def visit_access_or_type(self, node: PBAccessOrTypeNode) -> None:
        """Visit an access or type node."""
        self.visit(node.access_or_type)

    @abstractmethod
    def visit_argument(self, node: PBArgumentNode) -> None:
        """Visit an argument node."""
        self.visit(node.argument_option)
        self.visit(node.type)
        self.visit(node.identifier)
        self.visit(node.array_with_size)

    @abstractmethod
    def visit_argument_option(self, node: PBArgumentOptionNode) -> str:
        """Visit an argument option node."""
        return node.argument_option

    @abstractmethod
    def visit_arguments(self, node: PBArgumentsNode) -> None:
        """Visit an arguments node."""
        self.visit_all(node.arguments)

    @abstractmethod
    def visit_array(self, node: PBArrayNode) -> None:
        """Visit an array node."""
        self.visit_all(node.expressions)

    @abstractmethod
    def visit_array_designation(self, node: PBArrayDesignationNode) -> str:
        """Visit an array designation node."""
        return node.array_designation

    @abstractmethod
    def visit_array_position(self, node: PBArrayPositionNode) -> None:
        """Visit an array position node."""
        self.visit_all(node.expressions)

    @abstractmethod
    def visit_array_with_size(self, node: PBArrayWithSizeNode) -> None:
        """Visit an array with size node."""
        self.visit_all(node.expressions)

    @abstractmethod
    def visit_assignation(self, node: PBAssignationNode) -> None:
        """Visit an assignation node."""
        self.visit(node.expression)

    @abstractmethod
    def visit_assignation_statement(self, node: PBAssignationStatementNode) -> None:
        """Visit an assignation statement node."""
        self.visit(node.access_or_type)
        self.visit(node.expression_action)
        self.visit(node.assignation)

    @abstractmethod
    def visit_basic_type(self, node: BasicType) -> str:
        """Visit a basic type node."""
        return node.name

    @abstractmethod
    def visit_behavioral_alias(self, node: PBBehavioralAliasNode) -> None:
        """Visit a behavioral alias node."""
        self.visit(node.alias)

    @abstractmethod
    def visit_behavioral_library(self, node: PBBehavioralLibraryNode) -> None:
        """Visit a behavioral library node."""
        self.visit(node.library_file)

    @abstractmethod
    def visit_behavioral_option(self, node: PBBehavioralOptionNode) -> None:
        """Visit a behavioral option node."""
        self.visit(node.behavioral_option)

    @abstractmethod
    def visit_boolean_value(self, node: PBBooleanValueNode) -> str:
        """Visit a boolean value node."""
        return node.boolean_value

    @abstractmethod
    def visit_call_statement(self, node: PBCallStatementNode) -> None:
        """Visit a call statement node."""
        self.visit(node.variable)
        self.visit(node.identifier)
        self.visit(node.event_type)

    @abstractmethod
    def visit_case(self, node: PBCaseNode) -> None:
        """Visit a case node."""
        self.visit(node.case)

    @abstractmethod
    def visit_case_else(self, node: PBCaseElseNode) -> None:
        """Visit a case else node."""
        self.visit(node.statements)
        self.visit(node.statement)

    @abstractmethod
    def visit_choose_case(self, node: PBChooseCaseNode) -> None:
        """Visit a choose case node."""
        self.visit(node.expression)
        self.visit_all(node.cases)
        self.visit(node.case_else)

    @abstractmethod
    def visit_close_sql_cursor(self, node: PBCloseSqlCursorNode) -> None:
        """Visit a close SQL cursor node."""
        self.visit(node.identifier)

    @abstractmethod
    def visit_column(self, node: PBColumnNode) -> None:
        """Visit a column node."""
        self.visit(node.column_definition)

    @abstractmethod
    def visit_column_definition(self, node: PBColumnDefinitionNode) -> None:
        """Visit a column definition node."""
        self.visit(node.options)

    @abstractmethod
    def visit_column_name_option(self, node: PBColumnNameOptionNode) -> None:
        """Visit a column name option node."""
        self.visit(node.expression)

    @abstractmethod
    def visit_column_type_option(self, node: PBColumnTypeOptionNode) -> None:
        """Visit a column type option node."""
        self.visit(node.expression)

    @abstractmethod
    def visit_common_file(self, node: PBCommonFileNode) -> None:
        """Visit a common file node."""
        self.visit_all(node.file_statements)

    @abstractmethod
    def visit_condition(self, node: PBConditionNode) -> None:
        """Visit a condition node."""
        self.visit(node.expression)

    @abstractmethod
    def visit_constant(self, node: PBConstantNode) -> str:
        """Visit a constant node."""
        return node.constant

    @abstractmethod
    def visit_continue_statement(self, node: PBContinueStatementNode) -> str:
        """Visit a continue statement node."""
        return node.continue_statement

    @abstractmethod
    def visit_create_instruction(self, node: PBCreateInstructionNode) -> None:
        """Visit a create instruction node."""
        self.visit(node.variable)

    @abstractmethod
    def visit_create_using_instruction(
        self,
        node: PBCreateUsingInstructionNode,
    ) -> None:
        """Visit a create using instruction node."""
        self.visit(node.expression)

    @abstractmethod
    def visit_custom_call_statement(self, node: PBCustomCallStatementNode) -> None:
        """Visit a custom call statement node."""
        self.visit(node.identifier)

    @abstractmethod
    def visit_custom_type(self, node: CustomType) -> None:
        """Visit a custom type node."""
        self.visit(node.identifier)

    @abstractmethod
    def visit_data_window(self, node: PBDataWindowNode) -> None:
        """Visit a data window node."""
        self.visit(node.parameters)

    @abstractmethod
    def visit_data_window_file(self, node: PBDataWindowFileNode) -> None:
        """Visit a data window file node."""
        self.visit_all(node.file_statements)

    @abstractmethod
    def visit_declare_cursor(self, node: PBDeclareCursorNode) -> None:
        """Visit a declare cursor node."""
        self.visit(node.identifier)
        self.visit(node.target)

    @abstractmethod
    def visit_declare_procedure(self, node: PBDeclareProcedureNode) -> None:
        """Visit a declare procedure node."""
        self.visit(node.procedure_name)

    @abstractmethod
    def visit_default_variable(self, node: PBDefaultVariableNode) -> str:
        """Visit a default variable node."""
        return node.default_variable

    @abstractmethod
    def visit_descriptor(self, node: PBDescriptorNode) -> None:
        """Visit a descriptor node."""
        self.visit(node.expression)

    @abstractmethod
    def visit_destroy_statement(self, node: PBDestroyStatementNode) -> None:
        """Visit a destroy statement node."""
        self.visit(node.expression)

    @abstractmethod
    def visit_do_loop_until(self, node: PBDoLoopUntilNode) -> None:
        """Visit a do loop until node."""
        self.visit(node.statements)
        self.visit(node.expression)

    @abstractmethod
    def visit_do_loop_while(self, node: PBDoLoopWhileNode) -> None:
        """Visit a do loop while node."""
        self.visit(node.statements)
        self.visit(node.expression)

    @abstractmethod
    def visit_do_until_loop(self, node: PBDoUntilLoopNode) -> None:
        """Visit a do until loop node."""
        self.visit(node.expression)
        self.visit(node.statements)

    @abstractmethod
    def visit_do_while_loop(self, node: PBDoWhileLoopNode) -> None:
        """Visit a do while loop node."""
        self.visit(node.expression)
        self.visit(node.statements)

    @abstractmethod
    def visit_dynamic_method_invocation(
        self,
        node: PBDynamicMethodInvocationNode,
    ) -> None:
        """Visit a dynamic method invocation node."""
        self.visit(node.unchecked_identifier)
        self.visit(node.function_arguments)

    @abstractmethod
    def visit_else(self, node: PBElseNode) -> None:
        """Visit an else node."""
        self.visit(node.statements)

    @abstractmethod
    def visit_else_if(self, node: PBElseIfNode) -> None:
        """Visit an else if node."""
        self.visit(node.expression)
        self.visit(node.statements)

    @abstractmethod
    def visit_else_on_line(self, node: PBElseOnLineNode) -> None:
        """Visit an else on line node."""
        self.visit(node.statement)

    @abstractmethod
    def visit_end_forward(self, node: PBEndForwardNode) -> str:
        """Visit an end forward node."""
        return node.end_forward

    @abstractmethod
    def visit_event_attribute(self, node: PBEventAttributeNode) -> None:
        """Visit an event attribute node."""
        self.visit(node.return_type)
        self.visit(node.event_name)
        self.visit(node.attribute)

    @abstractmethod
    def visit_event_declaration(self, node: PBEventDeclarationNode) -> None:
        """Visit an event declaration node."""
        self.visit(node.return_type)
        self.visit(node.event_reference_name)
        self.visit(node.custom_call_statement)
        self.visit(node.statements)

    @abstractmethod
    def visit_event_invocation(self, node: PBEventInvocationNode) -> None:
        """Visit an event invocation node."""
        self.visit(node.identifier)
        self.visit(node.function_arguments)

    @abstractmethod
    def visit_event_long(self, node: PBEventLongNode) -> None:
        """Visit an event long node."""
        self.visit(node.function_argument)

    @abstractmethod
    def visit_event_name(self, node: PBEventNameNode) -> None:
        """Visit an event name node."""
        self.visit(node.event_name)

    @abstractmethod
    def visit_event_reference_name(self, node: PBEventReferenceNameNode) -> None:
        """Visit an event reference name node."""
        self.visit(node.object_class)
        self.visit(node.event_name)
        self.visit(node.arguments)

    @abstractmethod
    def visit_event_triggering_or_posting(
        self,
        node: PBEventTriggeringOrPostingNode,
    ) -> None:
        """Visit an event triggering or posting node."""
        self.visit_all(node.identifiers)
        self.visit_all(node.array_positions)
        self.visit(node.event_name)
        self.visit(node.event_word)
        self.visit(node.event_long)

    @abstractmethod
    def visit_event_type(self, node: PBEventTypeNode) -> None:
        """Visit an event type node."""
        self.visit(node.event_type)

    @abstractmethod
    def visit_event_word(self, node: PBEventWordNode) -> None:
        """Visit an event word node."""
        self.visit(node.function_argument)

    @abstractmethod
    def visit_execute_procedure(self, node: PBExecuteProcedureNode) -> None:
        """Visit an execute procedure node."""
        self.visit(node.procedure_name)
        self.visit(node.using_clause)

    @abstractmethod
    def visit_exit_statement(self, node: PBExitStatementNode) -> str:
        """Visit an exit statement node."""
        return node.exit_statement

    @abstractmethod
    def visit_export(self, node: PBExportNode) -> None:
        """Visit an export node."""
        self.visit(node.format_type)
        self.visit(node.parameters)

    @abstractmethod
    def visit_expression(self, node: PBExpressionNode) -> None:
        """Visit an expression node."""
        self.visit(node.expression)
        self.visit(node.expression_action)

    @abstractmethod
    def visit_expression_action(self, node: PBExpressionActionNode) -> None:
        """Visit an expression action node."""
        self.visit(node.action)
        self.visit(node.expression_action)

    @abstractmethod
    def visit_expression_list(self, node: PBExpressionListNode) -> None:
        """Visit an expression list node."""
        self.visit_all(node.expressions)

    @abstractmethod
    def visit_expression_operator(self, node: PBExpressionOperatorNode) -> str:
        """Visit an expression operator node."""
        return node.expression_operator


class PositionTrackingVisitor(PowerBuilderASTVisitor, PositionTrackerMixin):
    """Visitor that tracks and propagates position information through the AST.

    This visitor traverses the AST and ensures all nodes have proper position
    information attached. It can also validate that position information is
    consistent throughout the tree.
    """

    def __init__(self, validate: bool = False) -> None:
        """Initialize the position tracking visitor.

        Args:
            validate: Whether to validate position consistency
        """
        super().__init__()
        self.validate = validate
        self._errors: list[dict[str, Any]] = []
        self._nodes_without_position: list[PBNode] = []

    def visit(self, node: Any | None) -> Any:
        """Visit a node and track its position.

        Args:
            node: Node to visit

        Returns:
            Result of visiting the node
        """
        if node is None:
            return None

        # Track nodes without position information
        if isinstance(node, PBNode):
            if node.start_position is None or node.stop_position is None:
                self._nodes_without_position.append(node)
                logger.debug(
                    "Node %s at %s has no position information",
                    type(node).__name__,
                    id(node),
                )

        # Visit the node
        result = super().visit(node)

        # Validate position consistency if enabled
        if self.validate and isinstance(node, PBNode):
            self._validate_node_position(node)

        return result

    def _validate_node_position(self, node: PBNode) -> None:
        """Validate that a node's position information is consistent.

        Args:
            node: Node to validate
        """
        if node.start_position is not None and node.stop_position is not None:
            if node.start_position > node.stop_position:
                self._errors.append(
                    {
                        "type": "position_validation_error",
                        "message": f"Node {type(node).__name__} has invalid position range: "
                        f"start={node.start_position}, stop={node.stop_position}",
                        "node": node,
                    }
                )

    def get_report(self) -> dict[str, Any]:
        """Get a report of position tracking results.

        Returns:
            Dictionary with tracking statistics and errors
        """
        return {
            "nodes_without_position": len(self._nodes_without_position),
            "validation_errors": len(self._errors),
            "errors": self._errors,
            "unpositioned_node_types": self._get_unpositioned_node_types(),
        }

    def _get_unpositioned_node_types(self) -> dict[str, int]:
        """Get count of unpositioned nodes by type.

        Returns:
            Dictionary mapping node type names to counts
        """
        type_counts: dict[str, int] = {}
        for node in self._nodes_without_position:
            type_name = type(node).__name__
            type_counts[type_name] = type_counts.get(type_name, 0) + 1
        return type_counts

    def _track_node_position(self, node: Any) -> None:
        """Track position information for a node.

        Args:
            node: Node to track position for
        """
        if isinstance(node, PBNode):
            if node.start_position is None or node.stop_position is None:
                self._nodes_without_position.append(node)
                logger.debug(
                    "Node %s at %s has no position information",
                    type(node).__name__,
                    id(node),
                )
            elif self.validate:
                self._validate_node_position(node)

    # Implement visitor methods - use default implementations for most
    # Since these are abstract methods, we need to provide implementations
    def visit_access(self, node: Any) -> None:
        """Visit an access node."""
        self._track_node_position(node)
        # Default implementation - visit children
        if hasattr(node, "accessed"):
            self.visit(node.accessed)
        if hasattr(node, "array_position"):
            self.visit(node.array_position)

    def visit_access_modifier(self, node: Any) -> str:
        """Visit an access modifier node."""
        self._track_node_position(node)
        return getattr(node, "access_modifier", "")

    def visit_access_modifier_definer(self, node: Any) -> None:
        """Visit an access modifier definer node."""
        self._track_node_position(node)
        if hasattr(node, "access_modifier"):
            self.visit(node.access_modifier)

    def visit_access_or_type(self, node: Any) -> None:
        """Visit an access or type node."""
        self._track_node_position(node)
        if hasattr(node, "access_or_type"):
            self.visit(node.access_or_type)

    def visit_argument(self, node: Any) -> None:
        """Visit an argument node."""
        self._track_node_position(node)
        for attr in ["argument_option", "type", "identifier", "array_with_size"]:
            if hasattr(node, attr):
                self.visit(getattr(node, attr))

    def visit_argument_option(self, node: Any) -> str:
        """Visit an argument option node."""
        self._track_node_position(node)
        return getattr(node, "argument_option", "")

    def visit_arguments(self, node: Any) -> None:
        """Visit an arguments node."""
        self._track_node_position(node)
        if hasattr(node, "arguments"):
            self.visit_all(node.arguments)

    def visit_array(self, node: Any) -> None:
        """Visit an array node."""
        self._track_node_position(node)
        if hasattr(node, "expressions"):
            self.visit_all(node.expressions)

    def visit_array_designation(self, node: Any) -> str:
        """Visit an array designation node."""
        self._track_node_position(node)
        return getattr(node, "array_designation", "")

    def visit_array_position(self, node: Any) -> None:
        """Visit an array position node."""
        self._track_node_position(node)
        if hasattr(node, "expressions"):
            self.visit_all(node.expressions)

    def visit_array_with_size(self, node: Any) -> None:
        """Visit an array with size node."""
        self._track_node_position(node)
        if hasattr(node, "expressions"):
            self.visit_all(node.expressions)

    def visit_assignation(self, node: Any) -> None:
        """Visit an assignation node."""
        self._track_node_position(node)
        if hasattr(node, "expression"):
            self.visit(node.expression)

    def visit_assignation_statement(self, node: Any) -> None:
        """Visit an assignation statement node."""
        self._track_node_position(node)
        for attr in ["access_or_type", "expression_action", "assignation"]:
            if hasattr(node, attr):
                self.visit(getattr(node, attr))

    def visit_basic_type(self, node: Any) -> str:
        """Visit a basic type node."""
        self._track_node_position(node)
        return getattr(node, "name", "")

    def visit_behavioral_alias(self, node: Any) -> None:
        """Visit a behavioral alias node."""
        self._track_node_position(node)
        if hasattr(node, "alias"):
            self.visit(node.alias)

    def visit_behavioral_library(self, node: Any) -> None:
        """Visit a behavioral library node."""
        self._track_node_position(node)
        if hasattr(node, "library_file"):
            self.visit(node.library_file)

    def visit_behavioral_option(self, node: Any) -> None:
        """Visit a behavioral option node."""
        self._track_node_position(node)
        if hasattr(node, "behavioral_option"):
            self.visit(node.behavioral_option)

    def visit_boolean_value(self, node: Any) -> str:
        """Visit a boolean value node."""
        self._track_node_position(node)
        return getattr(node, "boolean_value", "")

    def visit_call_statement(self, node: Any) -> None:
        """Visit a call statement node."""
        self._track_node_position(node)
        for attr in ["variable", "identifier", "event_type"]:
            if hasattr(node, attr):
                self.visit(getattr(node, attr))

    def visit_case(self, node: Any) -> None:
        """Visit a case node."""
        self._track_node_position(node)
        if hasattr(node, "case"):
            self.visit(node.case)

    def visit_case_else(self, node: Any) -> None:
        """Visit a case else node."""
        self._track_node_position(node)
        for attr in ["statements", "statement"]:
            if hasattr(node, attr):
                self.visit(getattr(node, attr))

    def visit_choose_case(self, node: Any) -> None:
        """Visit a choose case node."""
        self._track_node_position(node)
        if hasattr(node, "expression"):
            self.visit(node.expression)
        if hasattr(node, "cases"):
            self.visit_all(node.cases)
        if hasattr(node, "case_else"):
            self.visit(node.case_else)

    def visit_close_sql_cursor(self, node: Any) -> None:
        """Visit a close SQL cursor node."""
        self._track_node_position(node)
        if hasattr(node, "identifier"):
            self.visit(node.identifier)

    def visit_column(self, node: Any) -> None:
        """Visit a column node."""
        self._track_node_position(node)
        if hasattr(node, "column_definition"):
            self.visit(node.column_definition)

    def visit_column_definition(self, node: Any) -> None:
        """Visit a column definition node."""
        self._track_node_position(node)
        if hasattr(node, "options"):
            self.visit(node.options)

    def visit_column_name_option(self, node: Any) -> None:
        """Visit a column name option node."""
        self._track_node_position(node)
        if hasattr(node, "expression"):
            self.visit(node.expression)

    def visit_column_type_option(self, node: Any) -> None:
        """Visit a column type option node."""
        self._track_node_position(node)
        if hasattr(node, "expression"):
            self.visit(node.expression)

    def visit_common_file(self, node: Any) -> None:
        """Visit a common file node."""
        self._track_node_position(node)
        if hasattr(node, "file_statements"):
            self.visit_all(node.file_statements)

    def visit_condition(self, node: Any) -> None:
        """Visit a condition node."""
        self._track_node_position(node)
        if hasattr(node, "expression"):
            self.visit(node.expression)

    def visit_constant(self, node: Any) -> str:
        """Visit a constant node."""
        self._track_node_position(node)
        return getattr(node, "constant", "")

    def visit_continue_statement(self, node: Any) -> str:
        """Visit a continue statement node."""
        self._track_node_position(node)
        return getattr(node, "continue_statement", "")

    def visit_create_instruction(self, node: Any) -> None:
        """Visit a create instruction node."""
        self._track_node_position(node)
        if hasattr(node, "variable"):
            self.visit(node.variable)

    def visit_create_using_instruction(self, node: Any) -> None:
        """Visit a create using instruction node."""
        self._track_node_position(node)
        if hasattr(node, "expression"):
            self.visit(node.expression)

    def visit_custom_call_statement(self, node: Any) -> None:
        """Visit a custom call statement node."""
        self._track_node_position(node)
        if hasattr(node, "identifier"):
            self.visit(node.identifier)

    def visit_custom_type(self, node: Any) -> None:
        """Visit a custom type node."""
        self._track_node_position(node)
        if hasattr(node, "identifier"):
            self.visit(node.identifier)

    def visit_data_window(self, node: Any) -> None:
        """Visit a data window node."""
        self._track_node_position(node)
        if hasattr(node, "parameters"):
            self.visit(node.parameters)

    def visit_data_window_file(self, node: Any) -> None:
        """Visit a data window file node."""
        self._track_node_position(node)
        if hasattr(node, "file_statements"):
            self.visit_all(node.file_statements)

    def visit_declare_cursor(self, node: Any) -> None:
        """Visit a declare cursor node."""
        self._track_node_position(node)
        for attr in ["identifier", "target"]:
            if hasattr(node, attr):
                self.visit(getattr(node, attr))

    def visit_declare_procedure(self, node: Any) -> None:
        """Visit a declare procedure node."""
        self._track_node_position(node)
        if hasattr(node, "procedure_name"):
            self.visit(node.procedure_name)

    def visit_default_variable(self, node: Any) -> str:
        """Visit a default variable node."""
        self._track_node_position(node)
        return getattr(node, "default_variable", "")

    def visit_descriptor(self, node: Any) -> None:
        """Visit a descriptor node."""
        self._track_node_position(node)
        if hasattr(node, "expression"):
            self.visit(node.expression)

    def visit_destroy_statement(self, node: Any) -> None:
        """Visit a destroy statement node."""
        self._track_node_position(node)
        if hasattr(node, "expression"):
            self.visit(node.expression)

    def visit_do_loop_until(self, node: Any) -> None:
        """Visit a do loop until node."""
        self._track_node_position(node)
        for attr in ["statements", "expression"]:
            if hasattr(node, attr):
                self.visit(getattr(node, attr))

    def visit_do_loop_while(self, node: Any) -> None:
        """Visit a do loop while node."""
        self._track_node_position(node)
        for attr in ["statements", "expression"]:
            if hasattr(node, attr):
                self.visit(getattr(node, attr))

    def visit_do_until_loop(self, node: Any) -> None:
        """Visit a do until loop node."""
        self._track_node_position(node)
        for attr in ["expression", "statements"]:
            if hasattr(node, attr):
                self.visit(getattr(node, attr))

    def visit_do_while_loop(self, node: Any) -> None:
        """Visit a do while loop node."""
        self._track_node_position(node)
        for attr in ["expression", "statements"]:
            if hasattr(node, attr):
                self.visit(getattr(node, attr))

    def visit_dynamic_method_invocation(self, node: Any) -> None:
        """Visit a dynamic method invocation node."""
        self._track_node_position(node)
        for attr in ["unchecked_identifier", "function_arguments"]:
            if hasattr(node, attr):
                self.visit(getattr(node, attr))

    def visit_else(self, node: Any) -> None:
        """Visit an else node."""
        self._track_node_position(node)
        if hasattr(node, "statements"):
            self.visit(node.statements)

    def visit_else_if(self, node: Any) -> None:
        """Visit an else if node."""
        self._track_node_position(node)
        for attr in ["expression", "statements"]:
            if hasattr(node, attr):
                self.visit(getattr(node, attr))

    def visit_else_on_line(self, node: Any) -> None:
        """Visit an else on line node."""
        self._track_node_position(node)
        if hasattr(node, "statement"):
            self.visit(node.statement)

    def visit_end_forward(self, node: Any) -> str:
        """Visit an end forward node."""
        self._track_node_position(node)
        return getattr(node, "end_forward", "")

    def visit_event_attribute(self, node: Any) -> None:
        """Visit an event attribute node."""
        self._track_node_position(node)
        for attr in ["return_type", "event_name", "attribute"]:
            if hasattr(node, attr):
                self.visit(getattr(node, attr))

    def visit_event_declaration(self, node: Any) -> None:
        """Visit an event declaration node."""
        self._track_node_position(node)
        for attr in [
            "return_type",
            "event_reference_name",
            "custom_call_statement",
            "statements",
        ]:
            if hasattr(node, attr):
                self.visit(getattr(node, attr))

    def visit_event_invocation(self, node: Any) -> None:
        """Visit an event invocation node."""
        self._track_node_position(node)
        for attr in ["identifier", "function_arguments"]:
            if hasattr(node, attr):
                self.visit(getattr(node, attr))

    def visit_event_long(self, node: Any) -> None:
        """Visit an event long node."""
        self._track_node_position(node)
        if hasattr(node, "function_argument"):
            self.visit(node.function_argument)

    def visit_event_name(self, node: Any) -> None:
        """Visit an event name node."""
        self._track_node_position(node)
        if hasattr(node, "event_name"):
            self.visit(node.event_name)

    def visit_event_reference_name(self, node: Any) -> None:
        """Visit an event reference name node."""
        self._track_node_position(node)
        for attr in ["object_class", "event_name", "arguments"]:
            if hasattr(node, attr):
                self.visit(getattr(node, attr))

    def visit_event_triggering_or_posting(self, node: Any) -> None:
        """Visit an event triggering or posting node."""
        self._track_node_position(node)
        if hasattr(node, "identifiers"):
            self.visit_all(node.identifiers)
        if hasattr(node, "array_positions"):
            self.visit_all(node.array_positions)
        for attr in ["event_name", "event_word", "event_long"]:
            if hasattr(node, attr):
                self.visit(getattr(node, attr))

    def visit_event_type(self, node: Any) -> None:
        """Visit an event type node."""
        self._track_node_position(node)
        if hasattr(node, "event_type"):
            self.visit(node.event_type)

    def visit_event_word(self, node: Any) -> None:
        """Visit an event word node."""
        self._track_node_position(node)
        if hasattr(node, "function_argument"):
            self.visit(node.function_argument)

    def visit_execute_procedure(self, node: Any) -> None:
        """Visit an execute procedure node."""
        self._track_node_position(node)
        for attr in ["procedure_name", "using_clause"]:
            if hasattr(node, attr):
                self.visit(getattr(node, attr))

    def visit_exit_statement(self, node: Any) -> str:
        """Visit an exit statement node."""
        self._track_node_position(node)
        return getattr(node, "exit_statement", "")

    def visit_export(self, node: Any) -> None:
        """Visit an export node."""
        self._track_node_position(node)
        for attr in ["format_type", "parameters"]:
            if hasattr(node, attr):
                self.visit(getattr(node, attr))

    def visit_expression(self, node: Any) -> None:
        """Visit an expression node."""
        self._track_node_position(node)
        for attr in ["expression", "expression_action"]:
            if hasattr(node, attr):
                self.visit(getattr(node, attr))

    def visit_expression_action(self, node: Any) -> None:
        """Visit an expression action node."""
        self._track_node_position(node)
        for attr in ["action", "expression_action"]:
            if hasattr(node, attr):
                self.visit(getattr(node, attr))

    def visit_expression_list(self, node: Any) -> None:
        """Visit an expression list node."""
        self._track_node_position(node)
        if hasattr(node, "expressions"):
            self.visit_all(node.expressions)

    def visit_expression_operator(self, node: Any) -> str:
        """Visit an expression operator node."""
        self._track_node_position(node)
        return getattr(node, "expression_operator", "")


def track_positions_in_transformer[T](transformer_class: type[T]) -> type[T]:
    """Decorator to add position tracking to a transformer class.

    Args:
        transformer_class: Transformer class to enhance

    Returns:
        Enhanced transformer class with position tracking
    """

    class PositionTrackingTransformer(PositionTrackerMixin, transformer_class):
        """Transformer with automatic position tracking."""

        def transform(self, tree: Tree) -> PBNode | Any:
            """Transform tree with position tracking.

            Args:
                tree: Parse tree to transform

            Returns:
                Transformed result with position information
            """
            # Extract position from the tree
            position = self.extract_position_from_tree(tree)

            # Transform with position context
            with self.with_position_context(position):
                result = super().transform(tree)

                # Annotate result with position if it's an AST node
                if isinstance(result, PBNode):
                    self.annotate_node_with_position(result, position)

                return result

        def __default__(self, data: str, children: list[Any], meta: Any) -> Any:
            """Default transformer method with position tracking.

            Args:
                data: Rule name
                children: Child nodes
                meta: Metadata including position info

            Returns:
                Transformed result
            """
            # Create position from meta
            position = None
            if meta:
                position = PositionRange(
                    start_line=meta.line,
                    start_column=meta.column,
                    end_line=getattr(meta, "end_line", meta.line),
                    end_column=getattr(meta, "end_column", meta.column),
                    start_offset=getattr(meta, "start_pos", None),
                    end_offset=getattr(meta, "end_pos", None),
                    filename=self._current_filename,
                )

            with self.with_position_context(position):
                result = super().__default__(data, children, meta)

                # Annotate result if it's an AST node
                if isinstance(result, PBNode):
                    self.annotate_node_with_position(result, position)

                return result

    # Preserve class metadata
    PositionTrackingTransformer.__name__ = transformer_class.__name__
    PositionTrackingTransformer.__qualname__ = transformer_class.__qualname__
    PositionTrackingTransformer.__module__ = transformer_class.__module__

    return PositionTrackingTransformer


# ============================================================================
# PUBLIC API
# ============================================================================

__all__ = [
    # Types and Position Handling
    "EnumeratedType",
    "StructureType",
    "PositionRange",
    "PositionTrackable",
    "PositionTrackerMixin",
    "PositionTrackingVisitor",
    "track_positions_in_transformer",
    # Grammar
    "GrammarManager",
    # Preprocessor
    "PowerBuilderPreprocessor",
    "ImplicitImportResolver",
    "PreprocessorState",
    "ImplicitDependency",
    "DependencyContext",
    # Parsers
    "PowerBuilderBaseParser",
    "SQLParser",
    "UnifiedPowerBuilderParser",
    "BasicPowerBuilderParser",
    "PowerBuilderPseudocodeParser",
    "PowerBuilderTransactionParser",
    "TypeParser",
    # Transformers
    "PowerBuilderTransformer",
    "SQLTransformer",
    # Visitor Pattern
    "PowerBuilderASTVisitor",
    # Library Management
    "LibraryManager",
    "LibraryInfo",
    "SymbolInfo",
    "SymbolCache",
    # Type Resolution
    "TypeResolver",
    "ResolutionContext",
    # Error Recovery
    "EnhancedErrorRecovery",
    "ErrorRecoveryTransformer",
    # Factory
    "ParseCoordinatorFactory",
    "create_parse_coordinator",
    # Node stub classes (for backward compatibility)
    "PBAccessModifierDefinerNode",
    "PBAccessModifierNode",
    "PBBehavioralAliasNode",
    "PBBehavioralLibraryNode",
    "PBBehavioralOptionNode",
    "PBCommonFileNode",
    "PBAccessOrTypeNode",
    "PBArrayDesignationNode",
    "PBAssignationNode",
    "PBAssignationStatementNode",
    "PBBooleanValueNode",
    "PBCallStatementNode",
    "PBCaseElseNode",
    "PBCaseNode",
    "PBChooseCaseNode",
    "PBConditionNode",
    "PBConstantNode",
    "PBContinueStatementNode",
    "PBCreateInstructionNode",
    "PBCreateUsingInstructionNode",
    "PBCustomCallStatementNode",
    "PBDescriptorNode",
    "PBDestroyStatementNode",
    "PBDoLoopUntilNode",
    "PBDoLoopWhileNode",
    "PBDoUntilLoopNode",
    "PBDoWhileLoopNode",
    "PBDynamicMethodInvocationNode",
    "PBElseIfNode",
    "PBElseNode",
    "PBElseOnLineNode",
    "PBEndForwardNode",
    "PBExitStatementNode",
    "PBExportNode",
    "PBExpressionActionNode",
    "PBExpressionListNode",
    "PBExpressionNode",
    "PBExpressionOperatorNode",
    "PBArrayNode",
    "PBArrayPositionNode",
    "PBArrayWithSizeNode",
    "PBCloseSqlCursorNode",
    "PBDeclareCursorNode",
    "PBDeclareProcedureNode",
    "PBExecuteProcedureNode",
    "PBArgumentNode",
    "PBArgumentOptionNode",
    "PBArgumentsNode",
    "PBDefaultVariableNode",
    "PBEventAttributeNode",
    "PBEventDeclarationNode",
    "PBEventInvocationNode",
    "PBEventLongNode",
    "PBEventNameNode",
    "PBEventReferenceNameNode",
    "PBEventTriggeringOrPostingNode",
    "PBEventTypeNode",
    "PBEventWordNode",
    "PBColumnDefinitionNode",
    "PBColumnNameOptionNode",
    "PBColumnNode",
    "PBColumnTypeOptionNode",
    "PBDataWindowFileNode",
    "PBDataWindowNode",
]
