"""PowerScript Language Domain Types.

Pure data types representing PowerScript language constructs.
These are the WHAT - no operations, just data models.
Following Scott Wlaschin's FDM principles.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Any
from enum import Enum


# ============================================================================
# DATA TYPES
# ============================================================================


class DataType(str, Enum):
    """PowerScript data types."""

    INTEGER = "integer"
    LONG = "long"
    DECIMAL = "decimal"
    REAL = "real"
    DOUBLE = "double"
    STRING = "string"
    CHAR = "char"
    BOOLEAN = "boolean"
    DATE = "date"
    TIME = "time"
    DATETIME = "datetime"
    BLOB = "blob"
    ANY = "any"
    POWEROBJECT = "powerobject"
    STRUCTURE = "structure"
    ARRAY = "array"


@dataclass(frozen=True)
class Variable:
    """A PowerScript variable."""

    name: str
    datatype: DataType
    array_dimensions: Optional[List[int]] = None
    initial_value: Optional[Any] = None
    scope: str = "local"  # local, instance, global, shared


# ============================================================================
# EXPRESSIONS
# ============================================================================


@dataclass(frozen=True)
class Expression:
    """Base expression type."""

    pass


@dataclass(frozen=True)
class Literal(Expression):
    """A literal value."""

    value: Any
    datatype: DataType


@dataclass(frozen=True)
class Identifier(Expression):
    """A variable or object reference."""

    name: str


@dataclass(frozen=True)
class BinaryOp(Expression):
    """A binary operation."""

    operator: str  # +, -, *, /, =, <>, <, >, <=, >=, AND, OR
    left: Expression
    right: Expression


@dataclass(frozen=True)
class UnaryOp(Expression):
    """A unary operation."""

    operator: str  # NOT, -, +
    operand: Expression


@dataclass(frozen=True)
class MemberAccess(Expression):
    """Object member access (dot notation)."""

    object: Expression
    member: str


@dataclass(frozen=True)
class ArrayAccess(Expression):
    """Array element access."""

    array: Expression
    indices: List[Expression]


@dataclass(frozen=True)
class FunctionCall(Expression):
    """A function or method call."""

    name: str
    arguments: List[Expression] = field(default_factory=list)
    object: Optional[Expression] = None  # For method calls


# ============================================================================
# STATEMENTS
# ============================================================================


@dataclass(frozen=True)
class Statement:
    """Base statement type."""

    line: Optional[int] = None


@dataclass(frozen=True)
class Assignment(Statement):
    """An assignment statement."""

    target: Expression
    value: Expression


@dataclass(frozen=True)
class IfStatement(Statement):
    """An IF-THEN-ELSE statement."""

    condition: Expression
    then_branch: List[Statement]
    elseif_branches: List[tuple[Expression, List[Statement]]] = field(
        default_factory=list
    )
    else_branch: Optional[List[Statement]] = None


@dataclass(frozen=True)
class ChooseCase(Statement):
    """A CHOOSE CASE statement."""

    expression: Expression
    cases: List[tuple[List[Expression], List[Statement]]]
    else_case: Optional[List[Statement]] = None


@dataclass(frozen=True)
class ForLoop(Statement):
    """A FOR loop."""

    variable: str
    start: Expression
    end: Expression
    step: Optional[Expression] = None
    body: List[Statement] = field(default_factory=list)


@dataclass(frozen=True)
class WhileLoop(Statement):
    """A WHILE loop."""

    condition: Expression
    body: List[Statement] = field(default_factory=list)


@dataclass(frozen=True)
class DoLoop(Statement):
    """A DO WHILE/UNTIL loop."""

    condition: Expression
    until: bool = False  # False = WHILE, True = UNTIL
    body: List[Statement] = field(default_factory=list)


@dataclass(frozen=True)
class ReturnStatement(Statement):
    """A RETURN statement."""

    value: Optional[Expression] = None


@dataclass(frozen=True)
class ExitStatement(Statement):
    """An EXIT statement."""

    pass


@dataclass(frozen=True)
class ContinueStatement(Statement):
    """A CONTINUE statement."""

    pass


@dataclass(frozen=True)
class ThrowStatement(Statement):
    """A THROW statement."""

    exception: Expression


@dataclass(frozen=True)
class TryBlock(Statement):
    """A TRY-CATCH-FINALLY block."""

    try_body: List[Statement]
    catch_blocks: List[
        tuple[str, str, List[Statement]]
    ]  # (exception_type, var_name, body)
    finally_body: Optional[List[Statement]] = None


# ============================================================================
# SQL STATEMENTS
# ============================================================================


@dataclass(frozen=True)
class SQLStatement(Statement):
    """Base SQL statement."""

    pass


@dataclass(frozen=True)
class SelectStatement(SQLStatement):
    """A SELECT statement."""

    columns: List[str]
    into_variables: List[str]
    from_clause: str
    where_clause: Optional[str] = None
    using_transaction: Optional[str] = None


@dataclass(frozen=True)
class InsertStatement(SQLStatement):
    """An INSERT statement."""

    table: str
    columns: List[str]
    values: List[Expression]
    using_transaction: Optional[str] = None


@dataclass(frozen=True)
class UpdateStatement(SQLStatement):
    """An UPDATE statement."""

    table: str
    set_clauses: List[tuple[str, Expression]]
    where_clause: Optional[str] = None
    using_transaction: Optional[str] = None


@dataclass(frozen=True)
class DeleteStatement(SQLStatement):
    """A DELETE statement."""

    table: str
    where_clause: Optional[str] = None
    using_transaction: Optional[str] = None


@dataclass(frozen=True)
class CommitStatement(SQLStatement):
    """A COMMIT statement."""

    using_transaction: Optional[str] = None


@dataclass(frozen=True)
class RollbackStatement(SQLStatement):
    """A ROLLBACK statement."""

    using_transaction: Optional[str] = None


# ============================================================================
# DECLARATIONS
# ============================================================================


@dataclass(frozen=True)
class VariableDeclaration(Statement):
    """A variable declaration."""

    variable: Variable


@dataclass(frozen=True)
class ConstantDeclaration(Statement):
    """A constant declaration."""

    name: str
    datatype: DataType
    value: Expression


@dataclass(frozen=True)
class TypeDeclaration(Statement):
    """A type declaration (for structures)."""

    name: str
    members: List[Variable]


# ============================================================================
# SCRIPT STRUCTURE
# ============================================================================


@dataclass(frozen=True)
class Script:
    """A PowerScript script (function body, event handler, etc)."""

    statements: List[Statement] = field(default_factory=list)
    local_variables: List[Variable] = field(default_factory=list)


@dataclass(frozen=True)
class FunctionDefinition:
    """A function definition."""

    name: str
    return_type: Optional[DataType]
    parameters: List[Variable]
    script: Script
    access: str = "public"
    throws: List[str] = field(default_factory=list)
