"""PowerBuilder AST Domain Types.

Pure data types representing Abstract Syntax Tree nodes.
These are the WHAT - no operations, just data models.
Following Scott Wlaschin's FDM principles.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Any, Dict
from enum import Enum


# ============================================================================
# AST NODE TYPES
# ============================================================================


class NodeType(str, Enum):
    """Types of AST nodes."""

    # Root
    MODULE = "module"
    COMPILATION_UNIT = "compilation_unit"

    # Declarations
    CLASS = "class"
    FUNCTION = "function"
    EVENT = "event"
    VARIABLE = "variable"
    CONSTANT = "constant"
    TYPE = "type"

    # Statements
    BLOCK = "block"
    IF = "if"
    FOR = "for"
    WHILE = "while"
    DO = "do"
    CHOOSE = "choose"
    CASE = "case"
    TRY = "try"
    CATCH = "catch"
    FINALLY = "finally"

    # Simple statements
    ASSIGNMENT = "assignment"
    RETURN = "return"
    BREAK = "break"
    CONTINUE = "continue"
    EXIT = "exit"
    THROW = "throw"
    EXPRESSION_STMT = "expression_stmt"

    # Expressions
    BINARY_OP = "binary_op"
    UNARY_OP = "unary_op"
    CALL = "call"
    MEMBER = "member"
    INDEX = "index"
    LITERAL = "literal"
    IDENTIFIER = "identifier"
    ARRAY = "array"

    # SQL
    SQL_SELECT = "sql_select"
    SQL_INSERT = "sql_insert"
    SQL_UPDATE = "sql_update"
    SQL_DELETE = "sql_delete"
    SQL_COMMIT = "sql_commit"
    SQL_ROLLBACK = "sql_rollback"

    # PowerBuilder specific
    DATAWINDOW = "datawindow"
    WINDOW = "window"
    MENU = "menu"
    USEROBJECT = "userobject"
    STRUCTURE = "structure"
    GLOBAL = "global"
    FORWARD = "forward"
    CREATE = "create"
    DESTROY = "destroy"
    POST = "post"
    TRIGGER = "trigger"


# ============================================================================
# AST NODE STRUCTURE
# ============================================================================


@dataclass(frozen=True)
class ASTNode:
    """Abstract Syntax Tree node."""

    type: NodeType
    value: Optional[Any] = None
    children: List["ASTNode"] = field(default_factory=list)
    attributes: Dict[str, Any] = field(default_factory=dict)
    location: Optional["SourceLocation"] = None


@dataclass(frozen=True)
class SourceLocation:
    """Source code location information."""

    file: str
    line: int
    column: int
    end_line: Optional[int] = None
    end_column: Optional[int] = None


# ============================================================================
# SPECIALIZED AST NODES
# ============================================================================


@dataclass(frozen=True)
class ModuleNode:
    """Root node for a PowerBuilder module."""

    name: str
    type: str  # window, datawindow, function, etc.
    declarations: List[ASTNode]
    statements: List[ASTNode]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ClassNode:
    """Class/Object declaration node."""

    name: str
    ancestor: Optional[str]
    variables: List[ASTNode]
    functions: List[ASTNode]
    events: List[ASTNode]
    properties: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class FunctionNode:
    """Function declaration node."""

    name: str
    return_type: Optional[str]
    parameters: List[ASTNode]
    body: List[ASTNode]
    access: str = "public"
    throws: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class VariableNode:
    """Variable declaration node."""

    name: str
    datatype: str
    initial_value: Optional[ASTNode] = None
    array_bounds: Optional[List[int]] = None
    scope: str = "local"


@dataclass(frozen=True)
class BinaryOpNode:
    """Binary operation node."""

    operator: str
    left: ASTNode
    right: ASTNode
    datatype: Optional[str] = None  # Result type


@dataclass(frozen=True)
class CallNode:
    """Function/method call node."""

    name: str
    arguments: List[ASTNode]
    object: Optional[ASTNode] = None  # For method calls
    datatype: Optional[str] = None  # Return type


@dataclass(frozen=True)
class LiteralNode:
    """Literal value node."""

    value: Any
    datatype: str


@dataclass(frozen=True)
class IdentifierNode:
    """Identifier (variable/function name) node."""

    name: str
    qualified: bool = False  # True if includes namespace/object
    parts: List[str] = field(default_factory=list)  # For qualified names


# ============================================================================
# CONTROL FLOW NODES
# ============================================================================


@dataclass(frozen=True)
class IfNode:
    """IF statement node."""

    condition: ASTNode
    then_branch: List[ASTNode]
    elseif_branches: List[tuple[ASTNode, List[ASTNode]]] = field(default_factory=list)
    else_branch: Optional[List[ASTNode]] = None


@dataclass(frozen=True)
class ForNode:
    """FOR loop node."""

    variable: str
    start: ASTNode
    end: ASTNode
    step: Optional[ASTNode]
    body: List[ASTNode]


@dataclass(frozen=True)
class WhileNode:
    """WHILE loop node."""

    condition: ASTNode
    body: List[ASTNode]


@dataclass(frozen=True)
class ChooseNode:
    """CHOOSE CASE statement node."""

    expression: ASTNode
    cases: List[tuple[List[ASTNode], List[ASTNode]]]  # (values, statements)
    default_case: Optional[List[ASTNode]] = None


# ============================================================================
# SQL NODES
# ============================================================================


@dataclass(frozen=True)
class SQLNode:
    """SQL statement node."""

    type: str  # SELECT, INSERT, UPDATE, DELETE
    sql: str
    into_variables: Optional[List[str]] = None
    using_transaction: Optional[str] = None
    parameters: List[ASTNode] = field(default_factory=list)


# ============================================================================
# AST METADATA
# ============================================================================


@dataclass(frozen=True)
class ASTMetadata:
    """Metadata about the AST."""

    source_file: str
    parse_time: float
    node_count: int
    max_depth: int
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class ParsedModule:
    """A fully parsed PowerBuilder module."""

    ast: ASTNode
    metadata: ASTMetadata
    source: Optional[str] = None  # Original source code
    symbols: List[str] = field(default_factory=list)  # Symbol table
