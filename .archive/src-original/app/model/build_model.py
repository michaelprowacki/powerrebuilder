"""Model Domain - Build Semantic Model.

Pure functions for building semantic models from AST.
Self-contained with all types defined here.
All functions return Result types for total error handling.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any, Union

from src_new._core.result import Result, Success, Failure


# ============================================================================
# MODEL DOMAIN TYPES (Self-contained - no shared.py!)
# ============================================================================

# ============================================================================
# MODEL DOMAIN ERRORS
# ============================================================================


@dataclass(frozen=True)
class ModelBuildError:
    """Error building semantic model."""

    error_type: str
    message: str
    node_type: Optional[str] = None
    location: Optional[str] = None

    def __str__(self) -> str:
        parts = [f"{self.error_type}: {self.message}"]
        if self.node_type:
            parts.append(f" at node type {self.node_type}")
        if self.location:
            parts.append(f" in {self.location}")
        return "".join(parts)


@dataclass(frozen=True)
class SymbolResolutionError:
    """Error resolving symbols."""

    symbol_name: str
    reason: str
    scope: Optional[str] = None

    def __str__(self) -> str:
        scope_str = f" in scope {self.scope}" if self.scope else ""
        return f"Cannot resolve symbol '{self.symbol_name}'{scope_str}: {self.reason}"


# ============================================================================
# MODEL DOMAIN VALUE TYPES
# ============================================================================


class NodeType(str, Enum):
    """AST node types needed for model building."""

    MODULE = "MODULE"
    CLASS = "CLASS"
    FUNCTION = "FUNCTION"
    METHOD = "METHOD"
    PROPERTY = "PROPERTY"
    EVENT = "EVENT"
    BLOCK = "BLOCK"
    IF_STATEMENT = "IF"
    WHILE_LOOP = "WHILE"
    FOR_LOOP = "FOR"
    RETURN_STATEMENT = "RETURN"
    ASSIGNMENT = "ASSIGNMENT"
    BINARY_OP = "BINARY_OP"
    UNARY_OP = "UNARY_OP"
    CALL = "CALL"
    IDENTIFIER = "IDENTIFIER"
    LITERAL = "LITERAL"
    TYPE = "TYPE"
    ARRAY_TYPE = "ARRAY_TYPE"
    DATAWINDOW = "DATAWINDOW"
    SQL_STATEMENT = "SQL_STATEMENT"
    COLUMN_DEF = "COLUMN_DEF"
    CONTROL_DEF = "CONTROL_DEF"


@dataclass(frozen=True)
class ASTNode:
    """Abstract syntax tree node (immutable)."""

    type: NodeType
    value: Any = None
    children: tuple = field(default_factory=tuple)
    metadata: dict = field(default_factory=dict)

    def get_child(self, index: int) -> Optional["ASTNode"]:
        """Get child node by index."""
        return self.children[index] if index < len(self.children) else None

    def find_children(self, node_type: NodeType) -> List["ASTNode"]:
        """Find all children of a specific type."""
        return [c for c in self.children if c.type == node_type]


class SymbolType(str, Enum):
    """Symbol types in semantic model."""

    CLASS = "CLASS"
    FUNCTION = "FUNCTION"
    VARIABLE = "VARIABLE"
    PARAMETER = "PARAMETER"
    PROPERTY = "PROPERTY"
    METHOD = "METHOD"
    CONSTANT = "CONSTANT"


@dataclass(frozen=True)
class Symbol:
    """Symbol in semantic model (immutable)."""

    name: str
    type: SymbolType
    data_type: Optional[str] = None
    scope: Optional[str] = None
    metadata: dict = field(default_factory=dict)


@dataclass(frozen=True)
class SemanticModel:
    """Semantic model of PowerBuilder code."""

    symbols: Dict[str, Symbol]
    dependencies: List[str]
    entry_points: List[str]
    metadata: dict


@dataclass(frozen=True)
class ModelSuccess:
    """Successful model building result."""

    model: SemanticModel
    warnings: List[str]


@dataclass(frozen=True)
class ModelFailed:
    """Failed model building result."""

    error: str
    partial_model: Optional[SemanticModel] = None


# ADT for model results (keeping for backwards compatibility)
ModelResult = Union[ModelSuccess, ModelFailed]


def build_model(ast: ASTNode) -> Result[SemanticModel, ModelBuildError]:
    """Build semantic model from AST.

    Pure function: AST -> Result[Model, Error]
    No exceptions - total function handling all cases.
    """
    if not ast:
        return Failure(
            ModelBuildError(error_type="InvalidInput", message="Empty AST provided")
        )

    # Extract symbols
    symbols_result = extract_symbols(ast)
    if symbols_result.is_failure():
        return Failure(symbols_result.error())

    # Find dependencies
    dependencies_result = find_dependencies(ast)
    if dependencies_result.is_failure():
        return Failure(dependencies_result.error())

    # Find entry points
    entry_points_result = find_entry_points(symbols_result.value())
    if entry_points_result.is_failure():
        return Failure(entry_points_result.error())

    # Create model
    model = SemanticModel(
        symbols=symbols_result.value(),
        dependencies=dependencies_result.value(),
        entry_points=entry_points_result.value(),
        metadata={"ast_type": ast.type.value},
    )

    # Validate model
    validation_result = validate_model(model)
    if validation_result.is_failure():
        return Failure(validation_result.error())

    return Success(model)


def extract_symbols(ast: ASTNode) -> Result[Dict[str, Symbol], ModelBuildError]:
    """Extract symbols from AST.

    Pure function to build symbol table.
    Returns Success with symbol table or Failure with error.
    """
    symbols = {}

    for node in walk_ast(ast):
        if node.type == NodeType.FUNCTION:
            if not node.value:
                return Failure(
                    ModelBuildError(
                        error_type="InvalidNode",
                        message="Function node missing name",
                        node_type=node.type.value,
                    )
                )

            symbol = Symbol(
                name=node.value,
                type=SymbolType.FUNCTION,
                metadata={"line": node.metadata.get("line")},
            )
            symbols[node.value] = symbol

        elif node.type == NodeType.ASSIGNMENT:
            if not node.value:
                return Failure(
                    ModelBuildError(
                        error_type="InvalidNode",
                        message="Assignment node missing variable name",
                        node_type=node.type.value,
                    )
                )

            symbol = Symbol(name=node.value, type=SymbolType.VARIABLE)
            symbols[node.value] = symbol

        elif node.type == NodeType.CLASS:
            if not node.value:
                return Failure(
                    ModelBuildError(
                        error_type="InvalidNode",
                        message="Class node missing name",
                        node_type=node.type.value,
                    )
                )

            symbol = Symbol(name=node.value, type=SymbolType.CLASS)
            symbols[node.value] = symbol

    return Success(symbols)


def find_dependencies(ast: ASTNode) -> Result[List[str], ModelBuildError]:
    """Find external dependencies in AST.

    Pure function to extract import/require statements.
    Returns Success with dependency list or Failure with error.
    """
    dependencies = []

    for node in walk_ast(ast):
        if node.type == NodeType.CALL:
            # Check if it's a system call that implies dependency
            if node.value and node.value.startswith("import_"):
                dep = node.value.replace("import_", "")
                if dep not in dependencies:
                    dependencies.append(dep)

    return Success(dependencies)


def find_entry_points(symbols: Dict[str, Symbol]) -> Result[List[str], ModelBuildError]:
    """Find entry points in symbol table.

    Pure function to identify main functions.
    Returns Success with entry points or Failure with error.
    """
    entry_points = []

    for name, symbol in symbols.items():
        if symbol.type == SymbolType.FUNCTION:
            # Check for main/entry function patterns
            if name.lower() in ["main", "start", "init", "constructor"]:
                entry_points.append(name)

    return Success(entry_points)


def validate_model(model: SemanticModel) -> Result[List[str], ModelBuildError]:
    """Validate semantic model.

    Pure function to check for issues.
    Returns Success with warnings list (may be empty) or Failure with critical error.
    """
    warnings = []

    # Critical validations that would cause failure
    if not model.symbols:
        return Failure(
            ModelBuildError(
                error_type="InvalidModel",
                message="Model has no symbols - cannot proceed",
            )
        )

    # Non-critical warnings
    if len(model.symbols) > 100:
        warnings.append("Large number of symbols may indicate overly complex code")

    if not model.entry_points:
        warnings.append("No obvious entry points found - may need manual configuration")

    if len(model.dependencies) > 50:
        warnings.append("High dependency count - consider refactoring")

    return Success(warnings)


def walk_ast(node: ASTNode):
    """Walk AST nodes recursively.

    Generator that yields all nodes.
    """
    yield node
    for child in node.children:
        yield from walk_ast(child)
