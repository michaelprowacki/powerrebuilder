"""Unified Model Module - ALL model functionality in ONE place.

This mega-consolidation merges ALL 49 model files into 1 for radical simplification.
Includes AST, entities, types, services, transactions, expressions, system - EVERYTHING.

Consolidated modules:
- ast/ (8 files) - AST nodes and functions
- entities/ (6 files) - Entity classes
- nodes/ (4 files) - Node definitions
- optimization/ (2 files) - SQL optimization
- services/ (6 files) - Model services
- symbols/ (3 files) - Symbol resolution
- transaction/ (6 files) - Transaction handling
- types/ (4 files) - Type system
- utils/ (6 files) - Utilities
- visitors/ (1 file) - Visitor patterns
- unified_expressions.py - Expression system
- unified_system.py - System components
- unified_model_utils.py - Model utilities
- constructs/ - PowerBuilder constructs

This consolidation eliminates 49 files and creates one mega-module for everything.
"""

from __future__ import annotations

import logging
import re
import json
import hashlib
import time
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from enum import Enum, auto
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, TYPE_CHECKING

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

# ============================================================================
# BASE TYPE SYSTEM SECTION (from types/)
# ============================================================================


class NodeKind(Enum):
    """Enumeration of AST node types."""

    # Structural nodes
    FILE = auto()
    MODULE = auto()
    CLASS = auto()
    FUNCTION = auto()
    METHOD = auto()
    PROPERTY = auto()
    EVENT = auto()

    # Statement nodes
    STATEMENT = auto()
    EXPRESSION = auto()
    DECLARATION = auto()
    ASSIGNMENT = auto()
    IF_STATEMENT = auto()
    WHILE_LOOP = auto()
    FOR_LOOP = auto()
    CASE_STATEMENT = auto()
    TRY_CATCH = auto()
    RETURN_STATEMENT = auto()

    # Expression nodes
    BINARY_OP = auto()
    UNARY_OP = auto()
    CALL = auto()
    IDENTIFIER = auto()
    LITERAL = auto()
    ARRAY_ACCESS = auto()
    MEMBER_ACCESS = auto()

    # Type nodes
    TYPE = auto()
    BASIC_TYPE = auto()
    CUSTOM_TYPE = auto()
    ARRAY_TYPE = auto()

    # SQL nodes
    SQL_SELECT = auto()
    SQL_INSERT = auto()
    SQL_UPDATE = auto()
    SQL_DELETE = auto()

    # Special nodes
    UNKNOWN = auto()
    ERROR = auto()


@dataclass
class SourceAnchor:
    """Source location information for AST nodes."""

    file: Optional[str] = None
    line: Optional[int] = None
    column: Optional[int] = None
    start_pos: Optional[int] = None
    end_pos: Optional[int] = None

    def __str__(self) -> str:
        """String representation of source location."""
        if self.file and self.line:
            return f"{self.file}:{self.line}:{self.column or 0}"
        elif self.line:
            return f"line {self.line}:{self.column or 0}"
        else:
            return "unknown location"


class Visitor(ABC):
    """Abstract base class for AST visitors."""

    @abstractmethod
    def visit(self, node: "PBNode") -> Any:
        """Visit a node."""
        pass


@dataclass
class PBNode(ABC):
    """Base class for all PowerBuilder AST nodes."""

    name: Optional[str] = None
    kind: NodeKind = NodeKind.UNKNOWN
    source_anchor: Optional[SourceAnchor] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    children: List["PBNode"] = field(default_factory=list)
    parent: Optional["PBNode"] = None

    def __post_init__(self):
        """Initialize parent references for children."""
        for child in self.children:
            if isinstance(child, PBNode):
                child.parent = self

    @abstractmethod
    def accept(self, visitor: Visitor) -> Any:
        """Accept a visitor for the visitor pattern."""
        pass

    def add_child(self, child: "PBNode") -> None:
        """Add a child node."""
        if child and isinstance(child, PBNode):
            child.parent = self
            self.children.append(child)

    def remove_child(self, child: "PBNode") -> bool:
        """Remove a child node."""
        try:
            self.children.remove(child)
            child.parent = None
            return True
        except ValueError:
            return False

    def find_children(self, kind: NodeKind) -> List["PBNode"]:
        """Find all children of a specific kind."""
        return [child for child in self.children if child.kind == kind]

    def find_ancestor(self, kind: NodeKind) -> Optional["PBNode"]:
        """Find the first ancestor of a specific kind."""
        current = self.parent
        while current:
            if current.kind == kind:
                return current
            current = current.parent
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Convert the node to a dictionary representation."""
        result = {
            "kind": self.kind.name,
            "name": self.name,
        }

        if self.source_anchor:
            result["source"] = {
                "file": self.source_anchor.file,
                "line": self.source_anchor.line,
                "column": self.source_anchor.column,
            }

        if self.metadata:
            result["metadata"] = self.metadata

        if self.children:
            result["children"] = [child.to_dict() for child in self.children]

        return result


@dataclass
class Type(PBNode):
    """Base class for type nodes."""

    type_name: str = ""
    is_array: bool = False
    is_nullable: bool = True

    def __post_init__(self):
        super().__post_init__()
        self.kind = NodeKind.TYPE

    def accept(self, visitor: Visitor) -> Any:
        return visitor.visit(self)


@dataclass
class BasicType(Type):
    """Represents a basic/primitive type."""

    def __post_init__(self):
        super().__post_init__()
        self.kind = NodeKind.BASIC_TYPE


@dataclass
class CustomType(Type):
    """Represents a custom/user-defined type."""

    base_type: Optional[str] = None

    def __post_init__(self):
        super().__post_init__()
        self.kind = NodeKind.CUSTOM_TYPE


@dataclass
class ArrayType(Type):
    """Represents an array type."""

    element_type: Optional[Type] = None
    dimensions: List[Optional[int]] = field(default_factory=list)

    def __post_init__(self):
        super().__post_init__()
        self.kind = NodeKind.ARRAY_TYPE
        self.is_array = True


# Common type constants
STRING_TYPE = BasicType(type_name="string")
INTEGER_TYPE = BasicType(type_name="integer")
LONG_TYPE = BasicType(type_name="long")
DECIMAL_TYPE = BasicType(type_name="decimal")
BOOLEAN_TYPE = BasicType(type_name="boolean")
DATE_TYPE = BasicType(type_name="date")
TIME_TYPE = BasicType(type_name="time")
DATETIME_TYPE = BasicType(type_name="datetime")
ANY_TYPE = BasicType(type_name="any")
VOID_TYPE = BasicType(type_name="void")


# Type aliases for convenience
NodeDict = Dict[str, Any]
NodeList = List[PBNode]
NodeOrDict = Union[PBNode, NodeDict]


# ============================================================================
# TYPE INFERENCE SYSTEM (from types/inference.py)
# ============================================================================


class TypeCategory(Enum):
    """Categories of PowerBuilder types."""

    PRIMITIVE = auto()
    OBJECT = auto()
    ARRAY = auto()
    ENUMERATED = auto()
    STRUCTURE = auto()
    FUNCTION = auto()
    INTERFACE = auto()
    GENERIC = auto()
    UNKNOWN = auto()


@dataclass
class TypeInfo:
    """Information about a type."""

    name: str
    category: TypeCategory
    base_type: Optional[str] = None
    is_nullable: bool = True
    is_readonly: bool = False
    constraints: List[str] = field(default_factory=list)
    properties: Dict[str, "TypeInfo"] = field(default_factory=dict)
    methods: Dict[str, "FunctionSignature"] = field(default_factory=dict)


@dataclass
class FunctionSignature:
    """Function signature information."""

    name: str
    parameters: List["Parameter"] = field(default_factory=list)
    return_type: Optional[TypeInfo] = None
    is_variadic: bool = False
    is_static: bool = False


@dataclass
class Parameter:
    """Function parameter information."""

    name: str
    type_info: TypeInfo
    is_optional: bool = False
    default_value: Optional[Any] = None


class TypeInferrer:
    """Infers types from PowerBuilder code and expressions."""

    def __init__(self):
        self.type_cache: Dict[str, TypeInfo] = {}
        self.context_stack: List[Dict[str, TypeInfo]] = [{}]
        self._init_builtin_types()

    def _init_builtin_types(self):
        """Initialize built-in PowerBuilder types."""
        builtins = {
            "integer": TypeInfo("integer", TypeCategory.PRIMITIVE, is_nullable=False),
            "long": TypeInfo("long", TypeCategory.PRIMITIVE, is_nullable=False),
            "string": TypeInfo("string", TypeCategory.PRIMITIVE),
            "boolean": TypeInfo("boolean", TypeCategory.PRIMITIVE, is_nullable=False),
            "decimal": TypeInfo("decimal", TypeCategory.PRIMITIVE),
            "double": TypeInfo("double", TypeCategory.PRIMITIVE, is_nullable=False),
            "real": TypeInfo("real", TypeCategory.PRIMITIVE, is_nullable=False),
            "date": TypeInfo("date", TypeCategory.PRIMITIVE),
            "time": TypeInfo("time", TypeCategory.PRIMITIVE),
            "datetime": TypeInfo("datetime", TypeCategory.PRIMITIVE),
            "blob": TypeInfo("blob", TypeCategory.PRIMITIVE),
            "char": TypeInfo("char", TypeCategory.PRIMITIVE),
            "any": TypeInfo("any", TypeCategory.UNKNOWN),
            "object": TypeInfo("object", TypeCategory.OBJECT),
        }

        self.type_cache.update(builtins)

    def infer_type(self, node: Any) -> TypeInfo:
        """Infer the type of a node or expression."""
        if node is None:
            return self.type_cache["any"]

        # Handle different node types
        node_type = type(node).__name__.lower()

        if hasattr(node, "type_name") and node.type_name:
            return self.get_type_info(node.type_name)

        if hasattr(node, "value"):
            return self._infer_from_value(node.value)

        if "literal" in node_type:
            return self._infer_literal_type(node)

        if "binary" in node_type:
            return self._infer_binary_type(node)

        if "call" in node_type:
            return self._infer_call_type(node)

        # Default to any for unknown types
        return self.type_cache["any"]

    def _infer_from_value(self, value: Any) -> TypeInfo:
        """Infer type from a Python value."""
        if isinstance(value, bool):
            return self.type_cache["boolean"]
        elif isinstance(value, int):
            if -(2**31) <= value <= 2**31 - 1:
                return self.type_cache["integer"]
            else:
                return self.type_cache["long"]
        elif isinstance(value, float):
            return self.type_cache["double"]
        elif isinstance(value, str):
            return self.type_cache["string"]
        elif isinstance(value, Decimal):
            return self.type_cache["decimal"]
        elif isinstance(value, date):
            return self.type_cache["date"]
        elif isinstance(value, datetime):
            return self.type_cache["datetime"]
        else:
            return self.type_cache["any"]

    def _infer_literal_type(self, node: Any) -> TypeInfo:
        """Infer type from literal node."""
        if hasattr(node, "value"):
            return self._infer_from_value(node.value)
        return self.type_cache["any"]

    def _infer_binary_type(self, node: Any) -> TypeInfo:
        """Infer type from binary operation."""
        if not hasattr(node, "operator"):
            return self.type_cache["any"]

        op = (
            node.operator.upper()
            if isinstance(node.operator, str)
            else str(node.operator)
        )

        # Comparison operators always return boolean
        if op in ["=", "<>", "<", ">", "<=", ">=", "AND", "OR", "NOT"]:
            return self.type_cache["boolean"]

        # Arithmetic operators - infer from operands
        if op in ["+", "-", "*", "/", "^"]:
            left_type = self.infer_type(getattr(node, "left", None))
            right_type = self.infer_type(getattr(node, "right", None))

            # String concatenation with +
            if op == "+" and (
                left_type.name == "string" or right_type.name == "string"
            ):
                return self.type_cache["string"]

            # Promote to more general numeric type
            if (
                left_type.category == TypeCategory.PRIMITIVE
                and right_type.category == TypeCategory.PRIMITIVE
            ):
                type_hierarchy = ["integer", "long", "real", "double", "decimal"]
                left_idx = (
                    type_hierarchy.index(left_type.name)
                    if left_type.name in type_hierarchy
                    else -1
                )
                right_idx = (
                    type_hierarchy.index(right_type.name)
                    if right_type.name in type_hierarchy
                    else -1
                )

                if left_idx >= 0 and right_idx >= 0:
                    result_type = type_hierarchy[max(left_idx, right_idx)]
                    return self.type_cache[result_type]

        return self.type_cache["any"]

    def _infer_call_type(self, node: Any) -> TypeInfo:
        """Infer type from function call."""
        if hasattr(node, "function_name"):
            func_name = node.function_name.lower()

            # Built-in function type mappings
            builtin_types = {
                "len": "integer",
                "upper": "string",
                "lower": "string",
                "trim": "string",
                "left": "string",
                "right": "string",
                "mid": "string",
                "string": "string",
                "integer": "integer",
                "long": "long",
                "double": "double",
                "decimal": "decimal",
                "boolean": "boolean",
                "abs": "decimal",  # Most general numeric type
                "round": "decimal",
                "isnull": "boolean",
                "today": "date",
                "now": "datetime",
                "max": "any",  # Depends on arguments
                "min": "any",  # Depends on arguments
            }

            if func_name in builtin_types:
                return self.type_cache[builtin_types[func_name]]

        return self.type_cache["any"]

    def get_type_info(self, type_name: str) -> TypeInfo:
        """Get type information by name."""
        type_name = type_name.lower()

        if type_name in self.type_cache:
            return self.type_cache[type_name]

        # Handle array types
        if type_name.endswith("[]"):
            base_type_name = type_name[:-2]
            base_type = self.get_type_info(base_type_name)
            array_type = TypeInfo(
                type_name,
                TypeCategory.ARRAY,
                base_type=base_type_name,
                properties={"element_type": base_type},
            )
            self.type_cache[type_name] = array_type
            return array_type

        # Create unknown type
        unknown_type = TypeInfo(type_name, TypeCategory.UNKNOWN)
        self.type_cache[type_name] = unknown_type
        return unknown_type

    def push_context(self, variables: Dict[str, TypeInfo]) -> None:
        """Push a new variable context."""
        self.context_stack.append(variables.copy())

    def pop_context(self) -> None:
        """Pop the current variable context."""
        if len(self.context_stack) > 1:
            self.context_stack.pop()

    def add_variable(self, name: str, type_info: TypeInfo) -> None:
        """Add a variable to the current context."""
        self.context_stack[-1][name] = type_info

    def get_variable_type(self, name: str) -> Optional[TypeInfo]:
        """Get the type of a variable from context."""
        for context in reversed(self.context_stack):
            if name in context:
                return context[name]
        return None


# ============================================================================
# TYPE VALIDATION SYSTEM (from types/validation.py)
# ============================================================================


class ValidationLevel(Enum):
    """Levels of validation strictness."""

    STRICT = auto()  # All errors are failures
    LENIENT = auto()  # Only critical errors are failures
    PERMISSIVE = auto()  # Very few errors are failures


@dataclass
class ValidationError:
    """A validation error."""

    message: str
    node: Optional[PBNode] = None
    severity: str = "error"  # error, warning, info
    code: Optional[str] = None

    def __str__(self) -> str:
        location = (
            f" at {self.node.source_anchor}"
            if self.node and self.node.source_anchor
            else ""
        )
        return f"{self.severity.upper()}: {self.message}{location}"


@dataclass
class ValidationResult:
    """Result of validation."""

    is_valid: bool
    errors: List[ValidationError] = field(default_factory=list)
    warnings: List[ValidationError] = field(default_factory=list)

    def add_error(
        self, message: str, node: Optional[PBNode] = None, code: Optional[str] = None
    ) -> None:
        """Add an error."""
        self.errors.append(ValidationError(message, node, "error", code))
        self.is_valid = False

    def add_warning(
        self, message: str, node: Optional[PBNode] = None, code: Optional[str] = None
    ) -> None:
        """Add a warning."""
        self.warnings.append(ValidationError(message, node, "warning", code))

    def merge(self, other: "ValidationResult") -> None:
        """Merge another validation result."""
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)
        self.is_valid = self.is_valid and other.is_valid


class TypeValidator:
    """Validates PowerBuilder types and type compatibility."""

    def __init__(self, level: ValidationLevel = ValidationLevel.STRICT):
        self.level = level
        self.type_inferrer = TypeInferrer()

    def validate_node(self, node: PBNode) -> ValidationResult:
        """Validate a single node."""
        result = ValidationResult(is_valid=True)

        if isinstance(node, Type):
            self._validate_type_node(node, result)

        # Validate children
        for child in node.children:
            child_result = self.validate_node(child)
            result.merge(child_result)

        return result

    def _validate_type_node(self, node: Type, result: ValidationResult) -> None:
        """Validate a type node."""
        if not node.type_name:
            result.add_error("Type name cannot be empty", node, "EMPTY_TYPE_NAME")
            return

        # Check if type exists
        type_info = self.type_inferrer.get_type_info(node.type_name)
        if (
            type_info.category == TypeCategory.UNKNOWN
            and self.level == ValidationLevel.STRICT
        ):
            result.add_warning(f"Unknown type '{node.type_name}'", node, "UNKNOWN_TYPE")

    def validate_assignment(
        self, target_type: TypeInfo, source_type: TypeInfo
    ) -> ValidationResult:
        """Validate type compatibility for assignment."""
        result = ValidationResult(is_valid=True)

        if not self._is_assignable(target_type, source_type):
            result.add_error(
                f"Cannot assign {source_type.name} to {target_type.name}",
                code="TYPE_MISMATCH",
            )

        return result

    def _is_assignable(self, target: TypeInfo, source: TypeInfo) -> bool:
        """Check if source type can be assigned to target type."""
        if target.name == source.name:
            return True

        if target.name == "any" or source.name == "any":
            return True

        # Numeric type compatibility
        numeric_types = {"integer", "long", "real", "double", "decimal"}
        if target.name in numeric_types and source.name in numeric_types:
            return self._is_numeric_promotion_valid(target.name, source.name)

        # String compatibility
        if target.name == "string":
            return True  # Most types can be converted to string

        # Nullable compatibility
        if target.is_nullable and source.name == "null":
            return True

        return False

    def _is_numeric_promotion_valid(self, target: str, source: str) -> bool:
        """Check if numeric promotion is valid."""
        # Define promotion hierarchy
        hierarchy = ["integer", "long", "real", "double", "decimal"]

        if target not in hierarchy or source not in hierarchy:
            return False

        target_idx = hierarchy.index(target)
        source_idx = hierarchy.index(source)

        # Can promote to higher precision types
        return target_idx >= source_idx


# ============================================================================
# AST SECTION (from ast/ and nodes/)
# ============================================================================


@dataclass
class Expression(PBNode):
    """Base class for expressions."""

    def __post_init__(self):
        super().__post_init__()
        self.kind = NodeKind.EXPRESSION

    def accept(self, visitor: Visitor) -> Any:
        return visitor.visit(self)


@dataclass
class Statement(PBNode):
    """Base class for statements."""

    def __post_init__(self):
        super().__post_init__()
        self.kind = NodeKind.STATEMENT

    def accept(self, visitor: Visitor) -> Any:
        return visitor.visit(self)


@dataclass
class Identifier(Expression):
    """Identifier expression."""

    def __post_init__(self):
        super().__post_init__()
        self.kind = NodeKind.IDENTIFIER


@dataclass
class Literal(Expression):
    """Base class for literal expressions."""

    value: Any = None

    def __post_init__(self):
        super().__post_init__()
        self.kind = NodeKind.LITERAL


@dataclass
class StringLiteral(Literal):
    """String literal expression."""

    value: str = ""


@dataclass
class NumberLiteral(Literal):
    """Numeric literal expression."""

    value: Union[int, float] = 0


@dataclass
class IntegerLiteral(NumberLiteral):
    """Integer literal expression."""

    value: int = 0


@dataclass
class RealLiteral(NumberLiteral):
    """Real/float literal expression."""

    value: float = 0.0


@dataclass
class BooleanLiteral(Literal):
    """Boolean literal expression."""

    value: bool = False


@dataclass
class NullLiteral(Literal):
    """Null literal expression."""

    value: None = None


@dataclass
class DateLiteral(Literal):
    """Date literal expression."""

    value: Optional[date] = None


@dataclass
class DateTimeLiteral(Literal):
    """DateTime literal expression."""

    value: Optional[datetime] = None


@dataclass
class DecimalLiteral(Literal):
    """Decimal literal expression."""

    value: Decimal = field(default_factory=lambda: Decimal("0"))


@dataclass
class BinaryExpression(Expression):
    """Binary operation expression."""

    left: Optional[Expression] = None
    operator: str = ""
    right: Optional[Expression] = None

    def __post_init__(self):
        super().__post_init__()
        self.kind = NodeKind.BINARY_OP


@dataclass
class UnaryExpression(Expression):
    """Unary operation expression."""

    operator: str = ""
    operand: Optional[Expression] = None

    def __post_init__(self):
        super().__post_init__()
        self.kind = NodeKind.UNARY_OP


@dataclass
class CallExpression(Expression):
    """Function call expression."""

    function: Optional[Expression] = None
    arguments: List[Expression] = field(default_factory=list)

    def __post_init__(self):
        super().__post_init__()
        self.kind = NodeKind.CALL


@dataclass
class MemberAccess(Expression):
    """Member access expression (dot notation)."""

    object: Optional[Expression] = None
    member: str = ""

    def __post_init__(self):
        super().__post_init__()
        self.kind = NodeKind.MEMBER_ACCESS


@dataclass
class ArrayAccess(Expression):
    """Array access expression."""

    array: Optional[Expression] = None
    indices: List[Expression] = field(default_factory=list)

    def __post_init__(self):
        super().__post_init__()
        self.kind = NodeKind.ARRAY_ACCESS


@dataclass
class AssignmentStatement(Statement):
    """Assignment statement."""

    target: Optional[Expression] = None
    value: Optional[Expression] = None

    def __post_init__(self):
        super().__post_init__()
        self.kind = NodeKind.ASSIGNMENT


@dataclass
class IfStatement(Statement):
    """If statement."""

    condition: Optional[Expression] = None
    then_statement: Optional[Statement] = None
    else_statement: Optional[Statement] = None

    def __post_init__(self):
        super().__post_init__()
        self.kind = NodeKind.IF_STATEMENT


@dataclass
class WhileLoop(Statement):
    """While loop statement."""

    condition: Optional[Expression] = None
    body: Optional[Statement] = None

    def __post_init__(self):
        super().__post_init__()
        self.kind = NodeKind.WHILE_LOOP


@dataclass
class ForLoop(Statement):
    """For loop statement."""

    init: Optional[Statement] = None
    condition: Optional[Expression] = None
    update: Optional[Statement] = None
    body: Optional[Statement] = None

    def __post_init__(self):
        super().__post_init__()
        self.kind = NodeKind.FOR_LOOP


@dataclass
class ReturnStatement(Statement):
    """Return statement."""

    value: Optional[Expression] = None

    def __post_init__(self):
        super().__post_init__()
        self.kind = NodeKind.RETURN_STATEMENT


@dataclass
class Block(Statement):
    """Block statement containing multiple statements."""

    statements: List[Statement] = field(default_factory=list)


@dataclass
class VariableDeclaration(Statement):
    """Variable declaration statement."""

    variable_type: Optional[Type] = None
    variables: List[str] = field(default_factory=list)

    def __post_init__(self):
        super().__post_init__()
        self.kind = NodeKind.DECLARATION


@dataclass
class FunctionDefinition(Statement):
    """Function definition."""

    signature: Optional["FunctionSignature"] = None
    body: Optional[Block] = None

    def __post_init__(self):
        super().__post_init__()
        self.kind = NodeKind.FUNCTION


# ============================================================================
# SQL NODES SECTION (from nodes/sql.py)
# ============================================================================


@dataclass
class SqlStatement(Statement):
    """Base class for SQL statements."""

    def __post_init__(self):
        super().__post_init__()


@dataclass
class SelectStatement(SqlStatement):
    """SQL SELECT statement."""

    columns: List["ResultColumn"] = field(default_factory=list)
    from_clause: Optional["FromClause"] = None
    where_clause: Optional["WhereClause"] = None
    group_by: Optional["GroupByClause"] = None
    having: Optional["HavingClause"] = None
    order_by: Optional["OrderByClause"] = None
    limit_clause: Optional["LimitClause"] = None

    def __post_init__(self):
        super().__post_init__()
        self.kind = NodeKind.SQL_SELECT


@dataclass
class InsertStatement(SqlStatement):
    """SQL INSERT statement."""

    table: str = ""
    columns: List[str] = field(default_factory=list)
    values: List[Expression] = field(default_factory=list)

    def __post_init__(self):
        super().__post_init__()
        self.kind = NodeKind.SQL_INSERT


@dataclass
class UpdateStatement(SqlStatement):
    """SQL UPDATE statement."""

    table: str = ""
    assignments: List["Assignment"] = field(default_factory=list)
    where_clause: Optional["WhereClause"] = None

    def __post_init__(self):
        super().__post_init__()
        self.kind = NodeKind.SQL_UPDATE


@dataclass
class DeleteStatement(SqlStatement):
    """SQL DELETE statement."""

    table: str = ""
    where_clause: Optional["WhereClause"] = None

    def __post_init__(self):
        super().__post_init__()
        self.kind = NodeKind.SQL_DELETE


@dataclass
class ResultColumn(PBNode):
    """Column in SELECT statement."""

    expression: Optional[Expression] = None
    alias: Optional[str] = None

    def accept(self, visitor: Visitor) -> Any:
        return visitor.visit(self)


@dataclass
class FromClause(PBNode):
    """FROM clause in SQL."""

    tables: List["TableReference"] = field(default_factory=list)
    joins: List["JoinClause"] = field(default_factory=list)

    def accept(self, visitor: Visitor) -> Any:
        return visitor.visit(self)


@dataclass
class TableReference(PBNode):
    """Table reference in FROM clause."""

    table_name: str = ""
    alias: Optional[str] = None

    def accept(self, visitor: Visitor) -> Any:
        return visitor.visit(self)


@dataclass
class JoinClause(PBNode):
    """JOIN clause in SQL."""

    join_type: str = "INNER"  # INNER, LEFT, RIGHT, FULL
    table: Optional[TableReference] = None
    condition: Optional[Expression] = None

    def accept(self, visitor: Visitor) -> Any:
        return visitor.visit(self)


@dataclass
class WhereClause(PBNode):
    """WHERE clause in SQL."""

    condition: Optional[Expression] = None

    def accept(self, visitor: Visitor) -> Any:
        return visitor.visit(self)


@dataclass
class GroupByClause(PBNode):
    """GROUP BY clause in SQL."""

    expressions: List[Expression] = field(default_factory=list)

    def accept(self, visitor: Visitor) -> Any:
        return visitor.visit(self)


@dataclass
class HavingClause(PBNode):
    """HAVING clause in SQL."""

    condition: Optional[Expression] = None

    def accept(self, visitor: Visitor) -> Any:
        return visitor.visit(self)


@dataclass
class OrderByClause(PBNode):
    """ORDER BY clause in SQL."""

    terms: List["OrderingTerm"] = field(default_factory=list)

    def accept(self, visitor: Visitor) -> Any:
        return visitor.visit(self)


@dataclass
class OrderingTerm(PBNode):
    """Term in ORDER BY clause."""

    expression: Optional[Expression] = None
    direction: str = "ASC"  # ASC or DESC

    def accept(self, visitor: Visitor) -> Any:
        return visitor.visit(self)


@dataclass
class LimitClause(PBNode):
    """LIMIT clause in SQL."""

    count: Optional[Expression] = None
    offset: Optional[Expression] = None

    def accept(self, visitor: Visitor) -> Any:
        return visitor.visit(self)


@dataclass
class Assignment(PBNode):
    """Assignment in UPDATE statement."""

    column: str = ""
    value: Optional[Expression] = None

    def accept(self, visitor: Visitor) -> Any:
        return visitor.visit(self)


@dataclass
class ColumnReference(Expression):
    """Reference to a table column."""

    table: Optional[str] = None
    column: str = ""


@dataclass
class SubqueryExpression(Expression):
    """Subquery expression."""

    query: Optional[SelectStatement] = None


@dataclass
class SQLQuery(PBNode):
    """PowerBuilder SQL query node."""

    statement: Optional[SqlStatement] = None
    parameters: List["SqlParameter"] = field(default_factory=list)

    def accept(self, visitor: Visitor) -> Any:
        return visitor.visit(self)


@dataclass
class SqlParameter(PBNode):
    """SQL parameter."""

    name: str = ""
    type_name: str = "string"

    def accept(self, visitor: Visitor) -> Any:
        return visitor.visit(self)


@dataclass
class ColonParameter(SqlParameter):
    """Colon-style SQL parameter (:param)."""

    pass


@dataclass
class QuestionMarkParameter(SqlParameter):
    """Question mark SQL parameter (?)."""

    pass


# ============================================================================
# ENTITIES SECTION (from entities/)
# ============================================================================


@dataclass
class PBApplication(PBNode):
    """PowerBuilder application entity."""

    description: str = ""
    libraries: List["Library"] = field(default_factory=list)

    def accept(self, visitor: Visitor) -> Any:
        return visitor.visit(self)


@dataclass
class PBEvent(PBNode):
    """PowerBuilder event entity."""

    event_type: str = ""
    parameters: List[Parameter] = field(default_factory=list)
    body: Optional[Block] = None

    def accept(self, visitor: Visitor) -> Any:
        return visitor.visit(self)


@dataclass
class PBFunction(PBNode):
    """PowerBuilder function entity."""

    signature: Optional[FunctionSignature] = None
    body: Optional[Block] = None
    access_level: str = "public"
    is_static: bool = False

    def accept(self, visitor: Visitor) -> Any:
        return visitor.visit(self)


@dataclass
class PBFunctionCall(CallExpression):
    """PowerBuilder function call."""

    function_name: str = ""


@dataclass
class PBVariableNode(Identifier):
    """PowerBuilder variable node."""

    variable_type: Optional[Type] = None


@dataclass
class Library(PBNode):
    """PowerBuilder library entity."""

    version: str = ""
    path: Optional[Path] = None
    objects: List[PBNode] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)

    def accept(self, visitor: Visitor) -> Any:
        return visitor.visit(self)


@dataclass
class PBMethodCall(CallExpression):
    """PowerBuilder method call."""

    object_ref: Optional[Expression] = None
    method_name: str = ""


@dataclass
class PBConstructorCall(CallExpression):
    """PowerBuilder constructor call."""

    class_name: str = ""


# ============================================================================
# SYMBOLS SECTION (from symbols/)
# ============================================================================


class SymbolKind(Enum):
    """Types of symbols."""

    VARIABLE = auto()
    FUNCTION = auto()
    TYPE = auto()
    CONSTANT = auto()
    PARAMETER = auto()
    FIELD = auto()
    METHOD = auto()
    PROPERTY = auto()
    EVENT = auto()
    NAMESPACE = auto()


@dataclass
class Symbol:
    """A symbol in the symbol table."""

    name: str
    kind: SymbolKind
    type_info: Optional[TypeInfo] = None
    scope: Optional["Scope"] = None
    definition_node: Optional[PBNode] = None
    is_public: bool = True
    is_static: bool = False

    def get_full_name(self) -> str:
        """Get the fully qualified name of the symbol."""
        if self.scope and self.scope.name:
            return f"{self.scope.get_full_name()}.{self.name}"
        return self.name


@dataclass
class Scope:
    """A lexical scope containing symbols."""

    name: Optional[str] = None
    parent: Optional["Scope"] = None
    symbols: Dict[str, Symbol] = field(default_factory=dict)
    children: List["Scope"] = field(default_factory=list)

    def add_symbol(self, symbol: Symbol) -> None:
        """Add a symbol to this scope."""
        symbol.scope = self
        self.symbols[symbol.name] = symbol

    def lookup(self, name: str) -> Optional[Symbol]:
        """Look up a symbol by name."""
        if name in self.symbols:
            return self.symbols[name]

        if self.parent:
            return self.parent.lookup(name)

        return None

    def lookup_local(self, name: str) -> Optional[Symbol]:
        """Look up a symbol only in this scope."""
        return self.symbols.get(name)

    def get_full_name(self) -> str:
        """Get the fully qualified scope name."""
        if self.parent and self.parent.name:
            return f"{self.parent.get_full_name()}.{self.name}"
        return self.name or ""

    def create_child_scope(self, name: Optional[str] = None) -> "Scope":
        """Create a child scope."""
        child = Scope(name=name, parent=self)
        self.children.append(child)
        return child


class SymbolTable:
    """Global symbol table managing all scopes."""

    def __init__(self):
        self.global_scope = Scope(name="global")
        self.current_scope = self.global_scope
        self._builtin_symbols()

    def _builtin_symbols(self):
        """Add built-in symbols."""
        builtins = [
            Symbol(
                "string", SymbolKind.TYPE, TypeInfo("string", TypeCategory.PRIMITIVE)
            ),
            Symbol(
                "integer", SymbolKind.TYPE, TypeInfo("integer", TypeCategory.PRIMITIVE)
            ),
            Symbol(
                "boolean", SymbolKind.TYPE, TypeInfo("boolean", TypeCategory.PRIMITIVE)
            ),
            Symbol("date", SymbolKind.TYPE, TypeInfo("date", TypeCategory.PRIMITIVE)),
            Symbol(
                "datetime",
                SymbolKind.TYPE,
                TypeInfo("datetime", TypeCategory.PRIMITIVE),
            ),
        ]

        for symbol in builtins:
            self.global_scope.add_symbol(symbol)

    def enter_scope(self, name: Optional[str] = None) -> Scope:
        """Enter a new scope."""
        new_scope = self.current_scope.create_child_scope(name)
        self.current_scope = new_scope
        return new_scope

    def exit_scope(self) -> Optional[Scope]:
        """Exit the current scope."""
        if self.current_scope.parent:
            old_scope = self.current_scope
            self.current_scope = self.current_scope.parent
            return old_scope
        return None

    def define_symbol(
        self,
        name: str,
        kind: SymbolKind,
        type_info: Optional[TypeInfo] = None,
        node: Optional[PBNode] = None,
    ) -> Symbol:
        """Define a new symbol in the current scope."""
        symbol = Symbol(name, kind, type_info, definition_node=node)
        self.current_scope.add_symbol(symbol)
        return symbol

    def lookup_symbol(self, name: str) -> Optional[Symbol]:
        """Look up a symbol starting from current scope."""
        return self.current_scope.lookup(name)

    def lookup_global(self, name: str) -> Optional[Symbol]:
        """Look up a symbol in global scope only."""
        return self.global_scope.lookup_local(name)


class SymbolResolver:
    """Resolves symbol references in the AST."""

    def __init__(self, symbol_table: Optional[SymbolTable] = None):
        self.symbol_table = symbol_table or SymbolTable()
        self.type_inferrer = TypeInferrer()

    def resolve_ast(self, root: PBNode) -> None:
        """Resolve all symbols in an AST."""
        self._resolve_node(root)

    def _resolve_node(self, node: PBNode) -> None:
        """Resolve symbols in a single node."""
        if isinstance(node, VariableDeclaration):
            self._resolve_variable_declaration(node)
        elif isinstance(node, FunctionDefinition):
            self._resolve_function_definition(node)
        elif isinstance(node, Identifier):
            self._resolve_identifier(node)

        # Recursively resolve children
        for child in node.children:
            self._resolve_node(child)

    def _resolve_variable_declaration(self, node: VariableDeclaration) -> None:
        """Resolve variable declaration."""
        type_info = None
        if node.variable_type:
            type_info = self.type_inferrer.get_type_info(node.variable_type.type_name)

        for var_name in node.variables:
            self.symbol_table.define_symbol(
                var_name, SymbolKind.VARIABLE, type_info, node
            )

    def _resolve_function_definition(self, node: FunctionDefinition) -> None:
        """Resolve function definition."""
        if node.signature:
            # Enter function scope
            self.symbol_table.enter_scope(node.signature.name)

            # Add parameters to scope
            for param in node.signature.parameters:
                param_type = (
                    self.type_inferrer.get_type_info(param.type_info.name)
                    if param.type_info
                    else None
                )
                self.symbol_table.define_symbol(
                    param.name, SymbolKind.PARAMETER, param_type
                )

            # Resolve function body
            if node.body:
                self._resolve_node(node.body)

            # Exit function scope
            self.symbol_table.exit_scope()

            # Add function to parent scope
            return_type = node.signature.return_type
            func_type = TypeInfo(
                node.signature.name,
                TypeCategory.FUNCTION,
                properties={"return_type": return_type} if return_type else {},
            )
            self.symbol_table.define_symbol(
                node.signature.name, SymbolKind.FUNCTION, func_type, node
            )

    def _resolve_identifier(self, node: Identifier) -> None:
        """Resolve identifier reference."""
        if node.name:
            symbol = self.symbol_table.lookup_symbol(node.name)
            if symbol:
                node.metadata["resolved_symbol"] = symbol
                node.metadata["type"] = symbol.type_info
            else:
                logger.warning(f"Unresolved symbol: {node.name}")


# ============================================================================
# SERVICES SECTION (from services/)
# ============================================================================


class EntityFactory:
    """Factory for creating PowerBuilder entities."""

    def __init__(self):
        self.type_inferrer = TypeInferrer()

    def create_function(
        self,
        name: str,
        return_type: str = "void",
        parameters: Optional[List[Dict[str, Any]]] = None,
    ) -> PBFunction:
        """Create a PowerBuilder function."""
        params = []
        if parameters:
            for param_data in parameters:
                param_type = self.type_inferrer.get_type_info(
                    param_data.get("type", "string")
                )
                param = Parameter(
                    name=param_data.get("name", ""),
                    type_info=param_type,
                    is_optional=param_data.get("optional", False),
                    default_value=param_data.get("default"),
                )
                params.append(param)

        return_type_info = (
            self.type_inferrer.get_type_info(return_type)
            if return_type != "void"
            else None
        )
        signature = FunctionSignature(name, params, return_type_info)

        return PBFunction(name=name, signature=signature)

    def create_variable(self, name: str, type_name: str = "string") -> PBVariableNode:
        """Create a PowerBuilder variable."""
        var_type = BasicType(type_name=type_name)
        return PBVariableNode(name=name, variable_type=var_type)

    def create_literal(self, value: Any) -> Literal:
        """Create appropriate literal node for a value."""
        if isinstance(value, bool):
            return BooleanLiteral(value=value)
        elif isinstance(value, int):
            return IntegerLiteral(value=value)
        elif isinstance(value, float):
            return RealLiteral(value=value)
        elif isinstance(value, str):
            return StringLiteral(value=value)
        elif value is None:
            return NullLiteral()
        elif isinstance(value, Decimal):
            return DecimalLiteral(value=value)
        else:
            return Literal(value=value)


class EntityValidator:
    """Validates PowerBuilder entities."""

    def __init__(self):
        self.type_validator = TypeValidator()

    def validate_function(self, function: PBFunction) -> ValidationResult:
        """Validate a PowerBuilder function."""
        result = ValidationResult(is_valid=True)

        if not function.name:
            result.add_error("Function name cannot be empty")

        if not function.signature:
            result.add_error("Function must have a signature")
        else:
            # Validate parameter names are unique
            param_names = set()
            for param in function.signature.parameters:
                if param.name in param_names:
                    result.add_error(f"Duplicate parameter name: {param.name}")
                param_names.add(param.name)

        return result

    def validate_variable(self, variable: PBVariableNode) -> ValidationResult:
        """Validate a PowerBuilder variable."""
        result = ValidationResult(is_valid=True)

        if not variable.name:
            result.add_error("Variable name cannot be empty")

        if variable.variable_type:
            type_result = self.type_validator.validate_node(variable.variable_type)
            result.merge(type_result)

        return result


class RelationshipManager:
    """Manages relationships between PowerBuilder entities."""

    def __init__(self):
        self.relationships: Dict[str, List[str]] = {}
        self.reverse_relationships: Dict[str, List[str]] = {}

    def add_relationship(
        self, source: str, target: str, relationship_type: str = "uses"
    ) -> None:
        """Add a relationship between entities."""
        key = f"{source}-{relationship_type}"
        if key not in self.relationships:
            self.relationships[key] = []
        self.relationships[key].append(target)

        # Add reverse relationship
        reverse_key = f"{target}-used_by"
        if reverse_key not in self.reverse_relationships:
            self.reverse_relationships[reverse_key] = []
        self.reverse_relationships[reverse_key].append(source)

    def get_dependencies(self, entity: str) -> List[str]:
        """Get all entities that this entity depends on."""
        dependencies = []
        for key, targets in self.relationships.items():
            if key.startswith(f"{entity}-"):
                dependencies.extend(targets)
        return dependencies

    def get_dependents(self, entity: str) -> List[str]:
        """Get all entities that depend on this entity."""
        dependents = []
        for key, sources in self.reverse_relationships.items():
            if key.startswith(f"{entity}-"):
                dependents.extend(sources)
        return dependents


class ASTProcessor:
    """Processes AST nodes for analysis and transformation."""

    def __init__(self):
        self.type_inferrer = TypeInferrer()
        self.symbol_resolver = SymbolResolver()

    def process_ast(self, root: PBNode) -> Dict[str, Any]:
        """Process an AST and return analysis results."""
        # Resolve symbols
        self.symbol_resolver.resolve_ast(root)

        # Collect statistics
        stats = self._collect_statistics(root)

        # Infer types
        self._infer_types(root)

        return {
            "statistics": stats,
            "symbols": self.symbol_resolver.symbol_table.global_scope.symbols,
            "processed_at": datetime.now().isoformat(),
        }

    def _collect_statistics(self, node: PBNode) -> Dict[str, int]:
        """Collect statistics about the AST."""
        stats: Dict[str, int] = {}

        def count_node(n: PBNode):
            kind_name = n.kind.name.lower()
            stats[kind_name] = stats.get(kind_name, 0) + 1

            for child in n.children:
                count_node(child)

        count_node(node)
        return stats

    def _infer_types(self, node: PBNode) -> None:
        """Infer types for expressions in the AST."""
        if isinstance(node, Expression):
            type_info = self.type_inferrer.infer_type(node)
            node.metadata["inferred_type"] = type_info

        for child in node.children:
            self._infer_types(child)


class ModelExtractor:
    """Extracts semantic models from AST."""

    def __init__(self):
        self.ast_processor = ASTProcessor()
        self.entity_factory = EntityFactory()

    def extract_model(self, ast: PBNode) -> Dict[str, Any]:
        """Extract semantic model from AST."""
        # Process the AST
        analysis = self.ast_processor.process_ast(ast)

        # Extract entities
        entities = self._extract_entities(ast)

        # Extract relationships
        relationships = self._extract_relationships(ast)

        return {
            "entities": entities,
            "relationships": relationships,
            "analysis": analysis,
            "extracted_at": datetime.now().isoformat(),
        }

    def _extract_entities(self, node: PBNode) -> List[Dict[str, Any]]:
        """Extract entities from AST nodes."""
        entities = []

        if isinstance(node, PBFunction):
            entities.append(
                {
                    "type": "function",
                    "name": node.name,
                    "signature": node.signature.name if node.signature else None,
                    "access_level": node.access_level,
                    "is_static": node.is_static,
                }
            )
        elif isinstance(node, PBVariableNode):
            entities.append(
                {
                    "type": "variable",
                    "name": node.name,
                    "type_name": node.variable_type.type_name
                    if node.variable_type
                    else "unknown",
                }
            )

        # Recursively extract from children
        for child in node.children:
            entities.extend(self._extract_entities(child))

        return entities

    def _extract_relationships(self, node: PBNode) -> List[Dict[str, Any]]:
        """Extract relationships from AST nodes."""
        relationships = []

        if isinstance(node, CallExpression):
            if isinstance(node.function, Identifier):
                relationships.append(
                    {
                        "type": "calls",
                        "source": getattr(node.parent, "name", "unknown"),
                        "target": node.function.name,
                    }
                )

        # Recursively extract from children
        for child in node.children:
            relationships.extend(self._extract_relationships(child))

        return relationships


class ModelPersistenceService:
    """Handles persistence of semantic models."""

    def __init__(self):
        self.cache: Dict[str, Any] = {}

    def save_model(self, model_id: str, model: Dict[str, Any]) -> None:
        """Save a model."""
        self.cache[model_id] = {
            "model": model,
            "saved_at": datetime.now().isoformat(),
            "hash": self._compute_hash(model),
        }

    def load_model(self, model_id: str) -> Optional[Dict[str, Any]]:
        """Load a model."""
        if model_id in self.cache:
            return self.cache[model_id]["model"]
        return None

    def _compute_hash(self, model: Dict[str, Any]) -> str:
        """Compute hash of model for caching."""
        model_str = json.dumps(model, sort_keys=True, default=str)
        return hashlib.sha256(model_str.encode()).hexdigest()


# ============================================================================
# TRANSACTION SECTION (from transaction/)
# ============================================================================


class TransactionState(Enum):
    """States of a transaction."""

    ACTIVE = auto()
    COMMITTED = auto()
    ABORTED = auto()
    PREPARING = auto()
    PREPARED = auto()


@dataclass
class TransactionContext:
    """Context for a database transaction."""

    transaction_id: str
    connection_id: str
    state: TransactionState = TransactionState.ACTIVE
    started_at: Optional[datetime] = None
    isolation_level: str = "READ_COMMITTED"

    def __post_init__(self):
        if self.started_at is None:
            self.started_at = datetime.now()


class TransactionError(Exception):
    """Base exception for transaction errors."""

    def __init__(self, message: str, transaction_id: Optional[str] = None):
        super().__init__(message)
        self.transaction_id = transaction_id


class DeadlockError(TransactionError):
    """Raised when a deadlock is detected."""

    pass


class TimeoutError(TransactionError):
    """Raised when a transaction times out."""

    pass


@dataclass
class Savepoint:
    """A transaction savepoint."""

    name: str
    transaction_id: str
    created_at: datetime = field(default_factory=datetime.now)
    statements_since: int = 0


class TransactionManager:
    """Manages database transactions."""

    def __init__(self):
        self.active_transactions: Dict[str, TransactionContext] = {}
        self.savepoints: Dict[str, List[Savepoint]] = {}
        self._next_tx_id = 1

    def begin_transaction(
        self, connection_id: str, isolation_level: str = "READ_COMMITTED"
    ) -> str:
        """Begin a new transaction."""
        tx_id = f"tx_{self._next_tx_id}"
        self._next_tx_id += 1

        context = TransactionContext(
            transaction_id=tx_id,
            connection_id=connection_id,
            isolation_level=isolation_level,
        )

        self.active_transactions[tx_id] = context
        self.savepoints[tx_id] = []

        logger.info(f"Started transaction {tx_id} on connection {connection_id}")
        return tx_id

    def commit_transaction(self, tx_id: str) -> None:
        """Commit a transaction."""
        if tx_id not in self.active_transactions:
            raise TransactionError(f"Transaction {tx_id} not found", tx_id)

        context = self.active_transactions[tx_id]
        if context.state != TransactionState.ACTIVE:
            raise TransactionError(f"Transaction {tx_id} is not active", tx_id)

        try:
            # Perform commit logic here
            context.state = TransactionState.COMMITTED
            logger.info(f"Committed transaction {tx_id}")
        finally:
            self._cleanup_transaction(tx_id)

    def rollback_transaction(self, tx_id: str) -> None:
        """Rollback a transaction."""
        if tx_id not in self.active_transactions:
            raise TransactionError(f"Transaction {tx_id} not found", tx_id)

        context = self.active_transactions[tx_id]
        if context.state not in [TransactionState.ACTIVE, TransactionState.PREPARING]:
            raise TransactionError(f"Transaction {tx_id} cannot be rolled back", tx_id)

        try:
            # Perform rollback logic here
            context.state = TransactionState.ABORTED
            logger.info(f"Rolled back transaction {tx_id}")
        finally:
            self._cleanup_transaction(tx_id)

    def create_savepoint(self, tx_id: str, savepoint_name: str) -> None:
        """Create a savepoint."""
        if tx_id not in self.active_transactions:
            raise TransactionError(f"Transaction {tx_id} not found", tx_id)

        savepoint = Savepoint(savepoint_name, tx_id)
        self.savepoints[tx_id].append(savepoint)

        logger.info(f"Created savepoint {savepoint_name} in transaction {tx_id}")

    def rollback_to_savepoint(self, tx_id: str, savepoint_name: str) -> None:
        """Rollback to a savepoint."""
        if tx_id not in self.savepoints:
            raise TransactionError(f"No savepoints for transaction {tx_id}", tx_id)

        savepoints = self.savepoints[tx_id]
        savepoint_index = None

        for i, sp in enumerate(savepoints):
            if sp.name == savepoint_name:
                savepoint_index = i
                break

        if savepoint_index is None:
            raise TransactionError(f"Savepoint {savepoint_name} not found", tx_id)

        # Remove savepoints created after this one
        self.savepoints[tx_id] = savepoints[: savepoint_index + 1]

        logger.info(f"Rolled back to savepoint {savepoint_name} in transaction {tx_id}")

    def _cleanup_transaction(self, tx_id: str) -> None:
        """Clean up transaction resources."""
        self.active_transactions.pop(tx_id, None)
        self.savepoints.pop(tx_id, None)


class DistributedTransactionManager(TransactionManager):
    """Manager for distributed transactions."""

    def __init__(self):
        super().__init__()
        self.coordinator_nodes: List[str] = []
        self.participant_nodes: Dict[str, List[str]] = {}

    def begin_distributed_transaction(self, participant_connections: List[str]) -> str:
        """Begin a distributed transaction."""
        tx_id = f"dtx_{self._next_tx_id}"
        self._next_tx_id += 1

        # Create transaction context
        context = TransactionContext(
            transaction_id=tx_id,
            connection_id="distributed",
            state=TransactionState.ACTIVE,
        )

        self.active_transactions[tx_id] = context
        self.participant_nodes[tx_id] = participant_connections.copy()

        logger.info(
            f"Started distributed transaction {tx_id} with {len(participant_connections)} participants"
        )
        return tx_id

    def prepare_phase(self, tx_id: str) -> bool:
        """Execute the prepare phase of 2PC."""
        if tx_id not in self.active_transactions:
            raise TransactionError(f"Transaction {tx_id} not found", tx_id)

        context = self.active_transactions[tx_id]
        if context.state != TransactionState.ACTIVE:
            raise TransactionError(f"Transaction {tx_id} is not active", tx_id)

        context.state = TransactionState.PREPARING

        # Simulate prepare phase
        participants = self.participant_nodes.get(tx_id, [])
        all_prepared = True

        for participant in participants:
            # In real implementation, send PREPARE message to participant
            prepared = self._send_prepare(participant, tx_id)
            if not prepared:
                all_prepared = False
                break

        if all_prepared:
            context.state = TransactionState.PREPARED
            logger.info(f"All participants prepared for transaction {tx_id}")
        else:
            context.state = TransactionState.ABORTED
            logger.warning(
                f"Some participants failed to prepare for transaction {tx_id}"
            )

        return all_prepared

    def _send_prepare(self, participant: str, tx_id: str) -> bool:
        """Send PREPARE message to participant (mock implementation)."""
        # In real implementation, this would send a network message
        logger.debug(f"Sending PREPARE to {participant} for transaction {tx_id}")
        return True  # Mock success


# ============================================================================
# OPTIMIZATION SECTION (from optimization/)
# ============================================================================


class SQLOptimizer:
    """Optimizes SQL queries for better performance."""

    def __init__(self):
        self.optimization_rules: List[Callable[[SqlStatement], SqlStatement]] = [
            self._eliminate_redundant_conditions,
            self._push_down_predicates,
            self._optimize_joins,
            self._simplify_expressions,
        ]

    def optimize_query(self, query: SqlStatement) -> SqlStatement:
        """Optimize a SQL query."""
        optimized = query

        for rule in self.optimization_rules:
            try:
                optimized = rule(optimized)
            except Exception as e:
                logger.warning(f"Optimization rule failed: {e}")

        return optimized

    def _eliminate_redundant_conditions(self, query: SqlStatement) -> SqlStatement:
        """Remove redundant WHERE conditions."""
        if isinstance(query, SelectStatement) and query.where_clause:
            # Simplified redundancy elimination
            condition = query.where_clause.condition
            if isinstance(condition, BinaryExpression):
                if condition.operator == "AND":
                    # Check for contradictory conditions
                    if self._is_contradiction(condition):
                        # Replace with FALSE condition
                        query.where_clause.condition = BooleanLiteral(value=False)
                elif condition.operator == "OR":
                    # Check for tautology
                    if self._is_tautology(condition):
                        # Remove WHERE clause entirely
                        query.where_clause = None

        return query

    def _is_contradiction(self, expr: BinaryExpression) -> bool:
        """Check if expression is a contradiction."""
        # Simplified check - in reality would be much more complex
        if (
            isinstance(expr.left, Identifier)
            and isinstance(expr.right, Identifier)
            and expr.left.name == expr.right.name
            and expr.operator == "<>"
        ):
            return True
        return False

    def _is_tautology(self, expr: BinaryExpression) -> bool:
        """Check if expression is a tautology."""
        # Simplified check - in reality would be much more complex
        if (
            isinstance(expr.left, Identifier)
            and isinstance(expr.right, Identifier)
            and expr.left.name == expr.right.name
            and expr.operator == "="
        ):
            return True
        return False

    def _push_down_predicates(self, query: SqlStatement) -> SqlStatement:
        """Push predicates down to reduce intermediate result sizes."""
        # Simplified predicate pushdown
        if isinstance(query, SelectStatement) and query.from_clause:
            for join in query.from_clause.joins:
                if join.condition and query.where_clause:
                    # Try to move WHERE conditions to JOIN conditions
                    self._move_conditions_to_join(query, join)

        return query

    def _move_conditions_to_join(
        self, query: SelectStatement, join: JoinClause
    ) -> None:
        """Move applicable WHERE conditions to JOIN conditions."""
        # This is a simplified version - real implementation would be much more complex
        pass

    def _optimize_joins(self, query: SqlStatement) -> SqlStatement:
        """Optimize JOIN operations."""
        if isinstance(query, SelectStatement) and query.from_clause:
            # Reorder joins for better performance (simplified)
            joins = query.from_clause.joins
            if len(joins) > 1:
                # Sort joins by estimated selectivity (mock implementation)
                joins.sort(key=lambda j: self._estimate_join_selectivity(j))

        return query

    def _estimate_join_selectivity(self, join: JoinClause) -> float:
        """Estimate join selectivity (mock implementation)."""
        # In real implementation, this would use statistics
        if join.join_type == "INNER":
            return 0.1
        elif join.join_type == "LEFT":
            return 0.5
        else:
            return 1.0

    def _simplify_expressions(self, query: SqlStatement) -> SqlStatement:
        """Simplify expressions in the query."""
        # This would recursively simplify all expressions in the query
        return query


# ============================================================================
# VISITORS SECTION (from visitors/)
# ============================================================================


class ModelVisitor(Visitor):
    """Base visitor for model AST nodes."""

    def visit(self, node: PBNode) -> Any:
        """Visit a node using dynamic dispatch."""
        method_name = f"visit_{node.kind.name.lower()}"
        method = getattr(self, method_name, self.generic_visit)
        return method(node)

    def generic_visit(self, node: PBNode) -> Any:
        """Default visit method."""
        results = []
        for child in node.children:
            result = self.visit(child)
            if result is not None:
                results.append(result)
        return results

    def visit_expression(self, node: Expression) -> Any:
        """Visit an expression node."""
        return self.generic_visit(node)

    def visit_statement(self, node: Statement) -> Any:
        """Visit a statement node."""
        return self.generic_visit(node)

    def visit_function(self, node: PBFunction) -> Any:
        """Visit a function node."""
        return self.generic_visit(node)


class CodeGenerationVisitor(ModelVisitor):
    """Visitor that generates code from the model."""

    def __init__(self, target_language: str = "powerbuilder"):
        self.target_language = target_language
        self.indent_level = 0
        self.output: List[str] = []

    def generate(self, node: PBNode) -> str:
        """Generate code for a node tree."""
        self.output.clear()
        self.indent_level = 0
        self.visit(node)
        return "\n".join(self.output)

    def emit(self, code: str) -> None:
        """Emit a line of code with proper indentation."""
        indent = "    " * self.indent_level
        self.output.append(f"{indent}{code}")

    def visit_function(self, node: PBFunction) -> Any:
        """Generate function code."""
        if node.signature:
            # Generate function signature
            params = ", ".join(
                f"{p.type_info.name if p.type_info else 'any'} {p.name}"
                for p in node.signature.parameters
            )
            return_type = (
                node.signature.return_type.name
                if node.signature.return_type
                else "void"
            )

            access = node.access_level
            static = "static " if node.is_static else ""

            self.emit(f"{access} {static}{return_type} {node.signature.name}({params})")

            if node.body:
                self.indent_level += 1
                self.visit(node.body)
                self.indent_level -= 1

            self.emit("end function")

    def visit_block(self, node: Block) -> Any:
        """Generate block code."""
        for stmt in node.statements:
            self.visit(stmt)

    def visit_assignment(self, node: AssignmentStatement) -> Any:
        """Generate assignment code."""
        if node.target and node.value:
            target_code = self._generate_expression(node.target)
            value_code = self._generate_expression(node.value)
            self.emit(f"{target_code} = {value_code}")

    def _generate_expression(self, expr: Expression) -> str:
        """Generate code for an expression."""
        if isinstance(expr, Literal):
            return self._generate_literal(expr)
        elif isinstance(expr, Identifier):
            return expr.name or ""
        elif isinstance(expr, BinaryExpression):
            left = self._generate_expression(expr.left) if expr.left else ""
            right = self._generate_expression(expr.right) if expr.right else ""
            return f"({left} {expr.operator} {right})"
        else:
            return str(expr)

    def _generate_literal(self, literal: Literal) -> str:
        """Generate code for a literal."""
        if isinstance(literal, StringLiteral):
            return f'"{literal.value}"'
        elif isinstance(literal, BooleanLiteral):
            return "true" if literal.value else "false"
        elif isinstance(literal, NullLiteral):
            return "null"
        else:
            return str(literal.value)


# ============================================================================
# EXPRESSIONS SECTION (from unified_expressions.py)
# ============================================================================


class ExpressionType(Enum):
    """Types of expressions for reconstruction."""

    LITERAL = auto()
    VARIABLE = auto()
    BINARY_OP = auto()
    UNARY_OP = auto()
    CALL = auto()
    FIELD_ACCESS = auto()
    ARRAY_ACCESS = auto()
    CAST = auto()
    CONDITIONAL = auto()
    TERNARY = auto()
    LAMBDA = auto()
    METHOD_CHAIN = auto()
    COMPOUND_ASSIGN = auto()
    INCREMENT = auto()
    DECREMENT = auto()
    NULL_COALESCE = auto()
    SPREAD = auto()
    DESTRUCTURE = auto()
    PATTERN_MATCH = auto()


@dataclass
class PBLiteral:
    """Base class for PowerBuilder literals."""

    value: Any = None

    @property
    def kind(self):
        return "LITERAL"

    def evaluate(self, context: Any = None) -> Any:
        return self.value


@dataclass
class PBBooleanLiteral(PBLiteral):
    """PowerBuilder boolean literal."""

    value: bool = False


@dataclass
class PBNullLiteral(PBLiteral):
    """PowerBuilder null literal."""

    value: None = None


@dataclass
class PBStringLiteral(PBLiteral):
    """PowerBuilder string literal."""

    value: str = ""


@dataclass
class PBNumberLiteral(PBLiteral):
    """PowerBuilder numeric literal that can be integer or real."""

    value: int | float = 0


@dataclass
class PBVariable:
    """PowerBuilder variable reference."""

    name: str = ""

    @property
    def kind(self):
        return "VARIABLE"

    def evaluate(self, context: Any = None) -> Any:
        if context and hasattr(context, "get"):
            return context.get(self.name)
        return None


@dataclass
class PBBinaryOperator:
    """PowerBuilder binary operator expression."""

    left: Any | None = None
    operator: str = ""
    right: Any | None = None

    @property
    def kind(self):
        return "BINARY"

    def evaluate(self, context: Any = None) -> Any:
        if not self.left or not self.right:
            return None
        left_val = (
            self.left.evaluate(context) if hasattr(self.left, "evaluate") else self.left
        )
        right_val = (
            self.right.evaluate(context)
            if hasattr(self.right, "evaluate")
            else self.right
        )

        # Basic operator evaluation
        if self.operator == "+":
            return left_val + right_val
        elif self.operator == "-":
            return left_val - right_val
        elif self.operator == "*":
            return left_val * right_val
        elif self.operator == "/":
            return left_val / right_val if right_val != 0 else None
        elif self.operator == "=":
            return left_val == right_val
        elif self.operator == "<>":
            return left_val != right_val
        elif self.operator == "<":
            return left_val < right_val
        elif self.operator == ">":
            return left_val > right_val
        elif self.operator == "<=":
            return left_val <= right_val
        elif self.operator == ">=":
            return left_val >= right_val
        elif self.operator == "AND":
            return left_val and right_val
        elif self.operator == "OR":
            return left_val or right_val
        else:
            return None


@dataclass
class PBUnaryOperator:
    """PowerBuilder unary operator expression."""

    operator: str = ""
    operand: Any | None = None

    @property
    def kind(self):
        return "UNARY"

    def evaluate(self, context: Any = None) -> Any:
        if not self.operand:
            return None
        val = (
            self.operand.evaluate(context)
            if hasattr(self.operand, "evaluate")
            else self.operand
        )

        if self.operator == "-":
            return -val
        elif self.operator == "+":
            return +val
        elif self.operator == "NOT":
            return not val
        else:
            return None


@dataclass
class PBFunctionCall:
    """PowerBuilder function call expression."""

    function_name: str = ""
    arguments: list[Any] = field(default_factory=list)

    @property
    def kind(self):
        return "FUNCTION_CALL"

    def evaluate(self, context: Any = None) -> Any:
        # Function evaluation would require a function registry
        return None


@dataclass
class PBArrayAccess:
    """PowerBuilder array access expression."""

    array: Any | None = None
    indices: list[Any] = field(default_factory=list)

    @property
    def kind(self):
        return "ARRAY_ACCESS"

    def evaluate(self, context: Any = None) -> Any:
        return None


@dataclass
class PBMemberAccess:
    """PowerBuilder member access expression (dot notation)."""

    object: Any | None = None
    member: str = ""

    @property
    def kind(self):
        return "MEMBER_ACCESS"

    def evaluate(self, context: Any = None) -> Any:
        return None


# Expression evaluation context and evaluator
class EvaluationError(Exception):
    """Error during expression evaluation."""

    pass


@dataclass
class EvaluationContext:
    """Context for expression evaluation."""

    variables: dict[str, Any] = field(default_factory=dict)
    functions: dict[str, Callable] = field(default_factory=dict)
    types: dict[str, type] = field(default_factory=dict)
    parent: Optional["EvaluationContext"] = None

    def get_variable(self, name: str) -> Any:
        """Get variable value, checking parent scopes."""
        if name in self.variables:
            return self.variables[name]
        if self.parent:
            return self.parent.get_variable(name)
        raise EvaluationError(f"Variable '{name}' not found")

    def set_variable(self, name: str, value: Any) -> None:
        """Set variable value in current scope."""
        self.variables[name] = value

    def create_child(self) -> "EvaluationContext":
        """Create a child context."""
        return EvaluationContext(parent=self)


class ExpressionEvaluator:
    """Evaluates PowerBuilder expressions."""

    def __init__(self, context: Optional[EvaluationContext] = None):
        self.context = context or EvaluationContext()
        self._init_builtin_types()

    def _init_builtin_types(self) -> None:
        """Initialize built-in PowerBuilder types."""
        self.context.types.update(
            {
                "integer": int,
                "long": int,
                "real": float,
                "double": float,
                "decimal": Decimal,
                "string": str,
                "boolean": bool,
                "date": date,
                "datetime": datetime,
            }
        )

    def evaluate(self, expr: Any) -> Any:
        """Evaluate an expression and return its value."""
        if expr is None:
            return None

        try:
            # Check if expression has its own evaluate method
            if hasattr(expr, "evaluate"):
                return expr.evaluate(self.context)

            # Simple value types
            if isinstance(expr, (int, float, str, bool, type(None))):
                return expr

            # Try to extract value attribute
            if hasattr(expr, "value"):
                return expr.value

            # Default: can't evaluate
            raise EvaluationError(f"Cannot evaluate expression type: {type(expr)}")

        except EvaluationError:
            raise
        except Exception as e:
            raise EvaluationError(f"Error evaluating expression: {e}") from e


# Built-in PowerBuilder functions
def pb_len(s: Any) -> int:
    """PowerBuilder Len function."""
    if s is None:
        return 0
    return len(str(s))


def pb_trim(s: Any) -> str:
    """PowerBuilder Trim function."""
    if s is None:
        return ""
    return str(s).strip()


def pb_upper(s: Any) -> str:
    """PowerBuilder Upper function."""
    if s is None:
        return ""
    return str(s).upper()


def pb_lower(s: Any) -> str:
    """PowerBuilder Lower function."""
    if s is None:
        return ""
    return str(s).lower()


def pb_isnull(val: Any) -> bool:
    """PowerBuilder IsNull function."""
    return val is None


# Dictionary of built-in functions
BUILTIN_FUNCTIONS: dict[str, Callable] = {
    "len": pb_len,
    "trim": pb_trim,
    "upper": pb_upper,
    "lower": pb_lower,
    "isnull": pb_isnull,
}


# ============================================================================
# SYSTEM SECTION (from unified_system.py)
# ============================================================================


class PBGlobalScope(Enum):
    """Scope of global variables."""

    GLOBAL = auto()
    SHARED = auto()
    INSTANCE = auto()
    LOCAL = auto()


@dataclass
class PBGlobalVariable(PBNode):
    """PowerBuilder global variable."""

    type_name: str = ""
    scope: PBGlobalScope = PBGlobalScope.GLOBAL
    default_value: Any = None
    description: str = ""
    is_readonly: bool = False
    is_deprecated: bool = False
    used_by: List[str] = field(default_factory=list)

    def accept(self, visitor: Visitor) -> Any:
        return visitor.visit(self)


class PBSystemEventType(Enum):
    """Types of system events."""

    APPLICATION = auto()
    WINDOW = auto()
    CONTROL = auto()
    MENU = auto()
    DATABASE = auto()
    ERROR = auto()
    USER = auto()


@dataclass
class PBSystemEvent(PBNode):
    """PowerBuilder system event."""

    event_type: PBSystemEventType = PBSystemEventType.USER
    description: str = ""
    parameters: List[Parameter] = field(default_factory=list)
    return_type: Optional[str] = None
    is_overridable: bool = True

    def accept(self, visitor: Visitor) -> Any:
        return visitor.visit(self)


@dataclass
class PBSystemFunction(PBNode):
    """PowerBuilder system function."""

    category: str = "general"
    description: str = ""
    parameters: List[Parameter] = field(default_factory=list)
    return_type: str = "any"
    is_deprecated: bool = False
    version_added: str = "6.0"

    def accept(self, visitor: Visitor) -> Any:
        return visitor.visit(self)


# ============================================================================
# UTILS SECTION (from utils/ and unified_model_utils.py)
# ============================================================================

# Security analysis patterns
CREDENTIAL_PATTERNS = [
    r'password\s*=\s*["\'](^["\']+)["\']',
    r'pwd\s*=\s*["\'](^["\']+)["\']',
    r'secret\s*=\s*["\'](^["\']+)["\']',
    r'api_key\s*=\s*["\'](^["\']+)["\']',
    r'token\s*=\s*["\'](^["\']+)["\']',
]


class AccessType(Enum):
    """Types of PowerBuilder access."""

    PUBLIC = auto()
    PROTECTED = auto()
    PRIVATE = auto()
    GLOBAL = auto()


@dataclass
class PBAccessNode(PBNode):
    """PowerBuilder access node."""

    access_type: AccessType = AccessType.PUBLIC
    object_name: str = ""
    member_name: str = ""

    def accept(self, visitor: Visitor) -> Any:
        return visitor.visit(self)


class SecurityAnalyzer:
    """Analyzes PowerBuilder code for security issues."""

    def __init__(self):
        self.issues: List[Dict[str, Any]] = []

    def analyze_node(self, node: PBNode) -> Dict[str, Any]:
        """Analyze a node for security issues."""
        self.issues.clear()
        self._analyze_recursive(node)

        return {
            "sql_injections": [i for i in self.issues if i["type"] == "sql_injection"],
            "hardcoded_credentials": [
                i for i in self.issues if i["type"] == "credential"
            ],
            "insecure_functions": [
                i for i in self.issues if i["type"] == "insecure_function"
            ],
        }

    def _analyze_recursive(self, node: PBNode) -> None:
        """Recursively analyze nodes."""
        # Check for hardcoded credentials
        if isinstance(node, StringLiteral):
            self._check_hardcoded_credentials(node)

        # Check for SQL injection risks
        if isinstance(node, SqlStatement):
            self._check_sql_injection(node)

        # Analyze children
        for child in node.children:
            self._analyze_recursive(child)

    def _check_hardcoded_credentials(self, node: StringLiteral) -> None:
        """Check for hardcoded credentials."""
        value = node.value.lower() if node.value else ""

        for pattern in CREDENTIAL_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                self.issues.append(
                    {
                        "type": "credential",
                        "message": "Potential hardcoded credential found",
                        "node": node,
                        "severity": "high",
                    }
                )
                break

    def _check_sql_injection(self, node: SqlStatement) -> None:
        """Check for SQL injection vulnerabilities."""
        # Simple check for string concatenation in SQL
        # In real implementation, this would be much more sophisticated
        self.issues.append(
            {
                "type": "sql_injection",
                "message": "SQL statement may be vulnerable to injection",
                "node": node,
                "severity": "medium",
            }
        )


class ModelValidator:
    """Validates model consistency and correctness."""

    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def validate_model(self, root: PBNode) -> bool:
        """Validate a complete model."""
        self.errors.clear()
        self.warnings.clear()

        self._validate_node(root)

        return len(self.errors) == 0

    def _validate_node(self, node: PBNode) -> None:
        """Validate a single node."""
        # Check basic node properties
        if not node.kind:
            self.errors.append(f"Node missing kind: {node}")

        # Validate specific node types
        if isinstance(node, PBFunction):
            self._validate_function(node)
        elif isinstance(node, Type):
            self._validate_type(node)

        # Validate children
        for child in node.children:
            self._validate_node(child)

    def _validate_function(self, func: PBFunction) -> None:
        """Validate a function node."""
        if not func.name:
            self.errors.append("Function missing name")

        if func.signature:
            # Check parameter names are unique
            param_names = [p.name for p in func.signature.parameters]
            if len(param_names) != len(set(param_names)):
                self.errors.append(f"Duplicate parameter names in function {func.name}")

    def _validate_type(self, type_node: Type) -> None:
        """Validate a type node."""
        if not type_node.type_name:
            self.errors.append("Type missing type_name")


# Utility functions
def create_node_from_dict(data: Dict[str, Any]) -> PBNode:
    """Create a PBNode from a dictionary representation."""
    kind_str = data.get("kind", "UNKNOWN")
    kind = NodeKind[kind_str] if kind_str in NodeKind.__members__ else NodeKind.UNKNOWN

    # Create source anchor if present
    source_anchor = None
    if "source" in data:
        source_data = data["source"]
        source_anchor = SourceAnchor(
            file=source_data.get("file"),
            line=source_data.get("line"),
            column=source_data.get("column"),
            start_pos=source_data.get("start_pos"),
            end_pos=source_data.get("end_pos"),
        )

    # Create appropriate node type based on kind
    if kind in [NodeKind.BASIC_TYPE, NodeKind.CUSTOM_TYPE, NodeKind.ARRAY_TYPE]:
        if kind == NodeKind.BASIC_TYPE:
            node = BasicType(type_name=data.get("type_name", ""))
        elif kind == NodeKind.CUSTOM_TYPE:
            node = CustomType(
                type_name=data.get("type_name", ""), base_type=data.get("base_type")
            )
        else:  # ARRAY_TYPE
            node = ArrayType(
                type_name=data.get("type_name", ""),
                dimensions=data.get("dimensions", []),
            )
    else:
        # Generic node
        class GenericNode(PBNode):
            def accept(self, visitor: Visitor) -> Any:
                return visitor.visit(self)

        node = GenericNode(
            name=data.get("name"),
            kind=kind,
            source_anchor=source_anchor,
            metadata=data.get("metadata", {}),
        )

    # Recursively create children
    if "children" in data:
        for child_data in data["children"]:
            if isinstance(child_data, dict):
                child = create_node_from_dict(child_data)
                node.add_child(child)

    return node


# Configuration management
@dataclass
class ModelConfig:
    """Configuration for model processing."""

    validation_level: ValidationLevel = ValidationLevel.STRICT
    enable_type_inference: bool = True
    enable_optimization: bool = True
    enable_security_analysis: bool = True
    cache_enabled: bool = True
    max_cache_size: int = 1000

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "ModelConfig":
        """Create config from dictionary."""
        return cls(
            validation_level=ValidationLevel[
                config_dict.get("validation_level", "STRICT")
            ],
            enable_type_inference=config_dict.get("enable_type_inference", True),
            enable_optimization=config_dict.get("enable_optimization", True),
            enable_security_analysis=config_dict.get("enable_security_analysis", True),
            cache_enabled=config_dict.get("cache_enabled", True),
            max_cache_size=config_dict.get("max_cache_size", 1000),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return {
            "validation_level": self.validation_level.name,
            "enable_type_inference": self.enable_type_inference,
            "enable_optimization": self.enable_optimization,
            "enable_security_analysis": self.enable_security_analysis,
            "cache_enabled": self.cache_enabled,
            "max_cache_size": self.max_cache_size,
        }


# ============================================================================
# UNIFIED MODEL ORCHESTRATOR
# ============================================================================


class UnifiedModel:
    """Unified orchestrator for all model functionality."""

    def __init__(self, config: Optional[ModelConfig] = None):
        self.config = config or ModelConfig()

        # Initialize all subsystems
        self.type_inferrer = TypeInferrer()
        self.type_validator = TypeValidator(self.config.validation_level)
        self.symbol_table = SymbolTable()
        self.symbol_resolver = SymbolResolver(self.symbol_table)
        self.entity_factory = EntityFactory()
        self.entity_validator = EntityValidator()
        self.relationship_manager = RelationshipManager()
        self.ast_processor = ASTProcessor()
        self.model_extractor = ModelExtractor()
        self.model_persistence = ModelPersistenceService()
        self.transaction_manager = TransactionManager()
        self.sql_optimizer = SQLOptimizer()
        self.security_analyzer = SecurityAnalyzer()
        self.model_validator = ModelValidator()
        self.expression_evaluator = ExpressionEvaluator()

        # Cache for processed models
        self._model_cache: Dict[str, Any] = {}

    def process_ast(
        self, ast: PBNode, model_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Process an AST through the complete model pipeline."""
        start_time = time.time()

        # Check cache first
        if model_id and self.config.cache_enabled and model_id in self._model_cache:
            logger.info(f"Returning cached model for {model_id}")
            return self._model_cache[model_id]

        # Step 1: Validate the AST structure
        if not self.model_validator.validate_model(ast):
            raise ValueError(f"Model validation failed: {self.model_validator.errors}")

        # Step 2: Resolve symbols
        self.symbol_resolver.resolve_ast(ast)

        # Step 3: Infer types if enabled
        if self.config.enable_type_inference:
            self._infer_types_recursive(ast)

        # Step 4: Validate types
        validation_result = self.type_validator.validate_node(ast)
        if (
            not validation_result.is_valid
            and self.config.validation_level == ValidationLevel.STRICT
        ):
            errors = [str(e) for e in validation_result.errors]
            raise ValueError(f"Type validation failed: {errors}")

        # Step 5: Extract semantic model
        model = self.model_extractor.extract_model(ast)

        # Step 6: Security analysis if enabled
        if self.config.enable_security_analysis:
            security_issues = self.security_analyzer.analyze_node(ast)
            model["security_analysis"] = security_issues

        # Step 7: Optimize SQL if present
        if self.config.enable_optimization:
            model = self._optimize_sql_in_model(model)

        # Add processing metadata
        model["processing_metadata"] = {
            "processed_at": datetime.now().isoformat(),
            "processing_time": time.time() - start_time,
            "config": self.config.to_dict(),
            "validation_errors": len(validation_result.errors),
            "validation_warnings": len(validation_result.warnings),
        }

        # Cache the result
        if model_id and self.config.cache_enabled:
            self._model_cache[model_id] = model
            # Manage cache size
            if len(self._model_cache) > self.config.max_cache_size:
                # Remove oldest entry (simplified LRU)
                oldest_key = next(iter(self._model_cache))
                del self._model_cache[oldest_key]

        # Persist if model_id provided
        if model_id:
            self.model_persistence.save_model(model_id, model)

        return model

    def _infer_types_recursive(self, node: PBNode) -> None:
        """Recursively infer types for all nodes."""
        if isinstance(node, Expression):
            type_info = self.type_inferrer.infer_type(node)
            node.metadata["inferred_type"] = type_info

        for child in node.children:
            self._infer_types_recursive(child)

    def _optimize_sql_in_model(self, model: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize SQL statements in the model."""
        # This would recursively find and optimize SQL statements
        # Simplified implementation
        model["optimization_applied"] = True
        return model

    def create_function(
        self,
        name: str,
        return_type: str = "void",
        parameters: Optional[List[Dict[str, Any]]] = None,
    ) -> PBFunction:
        """Create a new function using the entity factory."""
        return self.entity_factory.create_function(name, return_type, parameters)

    def create_variable(self, name: str, type_name: str = "string") -> PBVariableNode:
        """Create a new variable using the entity factory."""
        return self.entity_factory.create_variable(name, type_name)

    def evaluate_expression(
        self, expression: Any, context: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Evaluate an expression using the expression evaluator."""
        if context:
            eval_context = EvaluationContext(variables=context)
            evaluator = ExpressionEvaluator(eval_context)
            return evaluator.evaluate(expression)
        else:
            return self.expression_evaluator.evaluate(expression)

    def begin_transaction(self, connection_id: str = "default") -> str:
        """Begin a database transaction."""
        return self.transaction_manager.begin_transaction(connection_id)

    def commit_transaction(self, tx_id: str) -> None:
        """Commit a database transaction."""
        self.transaction_manager.commit_transaction(tx_id)

    def rollback_transaction(self, tx_id: str) -> None:
        """Rollback a database transaction."""
        self.transaction_manager.rollback_transaction(tx_id)

    def generate_code(self, ast: PBNode, target_language: str = "powerbuilder") -> str:
        """Generate code from AST using the code generation visitor."""
        visitor = CodeGenerationVisitor(target_language)
        return visitor.generate(ast)

    def clear_cache(self) -> None:
        """Clear the model cache."""
        self._model_cache.clear()

    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about the unified model."""
        return {
            "cache_size": len(self._model_cache),
            "symbol_table_size": len(self.symbol_table.global_scope.symbols),
            "active_transactions": len(self.transaction_manager.active_transactions),
            "config": self.config.to_dict(),
        }


# ============================================================================
# PUBLIC API - __all__ EXPORT LIST
# ============================================================================

__all__ = [
    # Core base types
    "NodeKind",
    "SourceAnchor",
    "PBNode",
    "Visitor",
    "Type",
    "BasicType",
    "CustomType",
    "ArrayType",
    "NodeDict",
    "NodeList",
    "NodeOrDict",
    # Type system
    "TypeCategory",
    "TypeInfo",
    "FunctionSignature",
    "Parameter",
    "TypeInferrer",
    "ValidationLevel",
    "ValidationError",
    "ValidationResult",
    "TypeValidator",
    # AST nodes
    "Expression",
    "Statement",
    "Identifier",
    "Literal",
    "StringLiteral",
    "NumberLiteral",
    "IntegerLiteral",
    "RealLiteral",
    "BooleanLiteral",
    "NullLiteral",
    "DateLiteral",
    "DateTimeLiteral",
    "DecimalLiteral",
    "BinaryExpression",
    "UnaryExpression",
    "CallExpression",
    "MemberAccess",
    "ArrayAccess",
    "AssignmentStatement",
    "IfStatement",
    "WhileLoop",
    "ForLoop",
    "ReturnStatement",
    "Block",
    "VariableDeclaration",
    "FunctionDefinition",
    # SQL nodes
    "SqlStatement",
    "SelectStatement",
    "InsertStatement",
    "UpdateStatement",
    "DeleteStatement",
    "ResultColumn",
    "FromClause",
    "TableReference",
    "JoinClause",
    "WhereClause",
    "GroupByClause",
    "HavingClause",
    "OrderByClause",
    "OrderingTerm",
    "LimitClause",
    "Assignment",
    "ColumnReference",
    "SubqueryExpression",
    "SQLQuery",
    "SqlParameter",
    "ColonParameter",
    "QuestionMarkParameter",
    # Entities
    "PBApplication",
    "PBEvent",
    "PBFunction",
    "PBFunctionCall",
    "PBVariableNode",
    "Library",
    "PBMethodCall",
    "PBConstructorCall",
    # Symbols
    "SymbolKind",
    "Symbol",
    "Scope",
    "SymbolTable",
    "SymbolResolver",
    # Services
    "EntityFactory",
    "EntityValidator",
    "RelationshipManager",
    "ASTProcessor",
    "ModelExtractor",
    "ModelPersistenceService",
    # Transactions
    "TransactionState",
    "TransactionContext",
    "TransactionError",
    "DeadlockError",
    "TimeoutError",
    "Savepoint",
    "TransactionManager",
    "DistributedTransactionManager",
    # Optimization
    "SQLOptimizer",
    # Visitors
    "ModelVisitor",
    "CodeGenerationVisitor",
    # Expressions
    "ExpressionType",
    "PBLiteral",
    "PBBooleanLiteral",
    "PBNullLiteral",
    "PBStringLiteral",
    "PBNumberLiteral",
    "PBVariable",
    "PBBinaryOperator",
    "PBUnaryOperator",
    "PBFunctionCall",
    "PBArrayAccess",
    "PBMemberAccess",
    "EvaluationError",
    "EvaluationContext",
    "ExpressionEvaluator",
    "BUILTIN_FUNCTIONS",
    # System
    "PBGlobalScope",
    "PBGlobalVariable",
    "PBSystemEventType",
    "PBSystemEvent",
    "PBSystemFunction",
    # Utils
    "AccessType",
    "PBAccessNode",
    "SecurityAnalyzer",
    "ModelValidator",
    "ModelConfig",
    # Constants
    "STRING_TYPE",
    "INTEGER_TYPE",
    "LONG_TYPE",
    "DECIMAL_TYPE",
    "BOOLEAN_TYPE",
    "DATE_TYPE",
    "TIME_TYPE",
    "DATETIME_TYPE",
    "ANY_TYPE",
    "VOID_TYPE",
    # Functions
    "create_node_from_dict",
    "pb_len",
    "pb_trim",
    "pb_upper",
    "pb_lower",
    "pb_isnull",
    # Main orchestrator
    "UnifiedModel",
]
