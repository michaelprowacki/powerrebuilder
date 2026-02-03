"""AST Representation Adapter.

Abstract Syntax Tree is HOW we represent code structure, not WHAT code is.
This adapter handles AST as one possible representation of programs.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum

from src_new.shared.result import Result, Success, Error


# ============================================================================
# AST REPRESENTATION (Not domain - just one way to represent code)
# ============================================================================


@dataclass(frozen=True)
class ASTNode:
    """Abstract syntax tree node.

    A representation of program structure, not the program itself.
    """

    node_type: "NodeType"
    children: List["ASTNode"] = field(default_factory=list)
    attributes: Dict[str, Any] = field(default_factory=dict)
    metadata: "NodeMetadata" = field(default_factory=lambda: NodeMetadata())


class NodeType(str, Enum):
    """Types of AST nodes."""

    # Program structure
    PROGRAM = "program"
    MODULE = "module"
    IMPORT = "import"

    # Declarations
    FUNCTION = "function"
    CLASS = "class"
    VARIABLE = "variable"
    CONSTANT = "constant"

    # Statements
    BLOCK = "block"
    IF = "if"
    WHILE = "while"
    FOR = "for"
    RETURN = "return"
    ASSIGNMENT = "assignment"

    # Expressions
    BINARY_OP = "binary_op"
    UNARY_OP = "unary_op"
    CALL = "call"
    MEMBER_ACCESS = "member"
    INDEX = "index"

    # Literals
    IDENTIFIER = "identifier"
    NUMBER = "number"
    STRING = "string"
    BOOLEAN = "boolean"
    NULL = "null"


@dataclass(frozen=True)
class NodeMetadata:
    """Metadata about AST node."""

    line: Optional[int] = None
    column: Optional[int] = None
    end_line: Optional[int] = None
    end_column: Optional[int] = None
    source_file: Optional[str] = None


# ============================================================================
# AST BUILDER
# ============================================================================


class ASTBuilder:
    """Builder for constructing ASTs."""

    @staticmethod
    def program(modules: List[ASTNode]) -> ASTNode:
        """Create program node."""
        return ASTNode(node_type=NodeType.PROGRAM, children=modules)

    @staticmethod
    def function(
        name: str,
        params: List[ASTNode],
        body: ASTNode,
        return_type: Optional[str] = None,
    ) -> ASTNode:
        """Create function node."""
        return ASTNode(
            node_type=NodeType.FUNCTION,
            children=[*params, body],
            attributes={"name": name, "return_type": return_type},
        )

    @staticmethod
    def variable(
        name: str, var_type: Optional[str] = None, init_value: Optional[ASTNode] = None
    ) -> ASTNode:
        """Create variable declaration node."""
        children = [init_value] if init_value else []
        return ASTNode(
            node_type=NodeType.VARIABLE,
            children=children,
            attributes={"name": name, "type": var_type},
        )

    @staticmethod
    def binary_op(left: ASTNode, operator: str, right: ASTNode) -> ASTNode:
        """Create binary operation node."""
        return ASTNode(
            node_type=NodeType.BINARY_OP,
            children=[left, right],
            attributes={"operator": operator},
        )

    @staticmethod
    def identifier(name: str) -> ASTNode:
        """Create identifier node."""
        return ASTNode(node_type=NodeType.IDENTIFIER, attributes={"name": name})

    @staticmethod
    def literal(value: Any, literal_type: str) -> ASTNode:
        """Create literal node."""
        node_type_map = {
            "number": NodeType.NUMBER,
            "string": NodeType.STRING,
            "boolean": NodeType.BOOLEAN,
            "null": NodeType.NULL,
        }
        return ASTNode(
            node_type=node_type_map.get(literal_type, NodeType.STRING),
            attributes={"value": value},
        )


# ============================================================================
# AST VISITOR
# ============================================================================


class ASTVisitor:
    """Visitor pattern for traversing AST."""

    def visit(self, node: ASTNode) -> Any:
        """Visit a node."""
        method_name = f"visit_{node.node_type.value}"
        visitor = getattr(self, method_name, self.visit_default)
        return visitor(node)

    def visit_default(self, node: ASTNode) -> Any:
        """Default visitor for unhandled nodes."""
        # Visit all children
        for child in node.children:
            self.visit(child)

    def visit_children(self, node: ASTNode) -> List[Any]:
        """Visit all children of a node."""
        return [self.visit(child) for child in node.children]


# ============================================================================
# AST TRANSFORMER
# ============================================================================


class ASTTransformer:
    """Transform one AST to another."""

    def transform(self, node: ASTNode) -> ASTNode:
        """Transform a node."""
        method_name = f"transform_{node.node_type.value}"
        transformer = getattr(self, method_name, self.transform_default)
        return transformer(node)

    def transform_default(self, node: ASTNode) -> ASTNode:
        """Default transformer - recursively transform children."""
        new_children = [self.transform(child) for child in node.children]
        return ASTNode(
            node_type=node.node_type,
            children=new_children,
            attributes=node.attributes,
            metadata=node.metadata,
        )


# ============================================================================
# AST TO DOMAIN CONVERTER
# ============================================================================


class ASTToDomainConverter:
    """Convert AST representation to domain objects.

    This bridges the gap between representation and domain.
    """

    def convert_to_computation(self, ast_node: ASTNode) -> Result[Any, str]:
        """Convert AST function to domain Computation."""
        if ast_node.node_type != NodeType.FUNCTION:
            return Error(f"Expected function node, got {ast_node.node_type}")

        # Extract function information from AST representation
        name = ast_node.attributes.get("name", "unnamed")
        return_type = ast_node.attributes.get("return_type")

        # This would convert to domain types from core/computation.py
        # For now, return simplified representation
        return Success(
            {
                "name": name,
                "return_type": return_type,
                "is_pure": self._check_purity(ast_node),
            }
        )

    def convert_to_type(self, ast_node: ASTNode) -> Result[Any, str]:
        """Convert AST type to domain Type."""
        # Convert AST representation to domain type from core/types.py
        if ast_node.node_type == NodeType.VARIABLE:
            var_type = ast_node.attributes.get("type", "any")
            return Success({"type_kind": "variable", "type_name": var_type})
        return Error(f"Cannot convert {ast_node.node_type} to type")

    def _check_purity(self, node: ASTNode) -> bool:
        """Check if function is pure (no side effects)."""
        # Simplified purity check
        impure_operations = ["assignment", "call", "print", "io"]

        def has_impure_ops(n: ASTNode) -> bool:
            if n.node_type.value in impure_operations:
                return True
            return any(has_impure_ops(child) for child in n.children)

        return not has_impure_ops(node)


# ============================================================================
# AST SERIALIZATION
# ============================================================================


def ast_to_dict(node: ASTNode) -> Dict[str, Any]:
    """Serialize AST to dictionary."""
    return {
        "type": node.node_type.value,
        "attributes": node.attributes,
        "children": [ast_to_dict(child) for child in node.children],
        "metadata": {
            "line": node.metadata.line,
            "column": node.metadata.column,
            "end_line": node.metadata.end_line,
            "end_column": node.metadata.end_column,
            "source_file": node.metadata.source_file,
        }
        if node.metadata
        else None,
    }


def dict_to_ast(data: Dict[str, Any]) -> ASTNode:
    """Deserialize AST from dictionary."""
    metadata = NodeMetadata()
    if data.get("metadata"):
        meta = data["metadata"]
        metadata = NodeMetadata(
            line=meta.get("line"),
            column=meta.get("column"),
            end_line=meta.get("end_line"),
            end_column=meta.get("end_column"),
            source_file=meta.get("source_file"),
        )

    children = [dict_to_ast(child) for child in data.get("children", [])]

    return ASTNode(
        node_type=NodeType(data["type"]),
        attributes=data.get("attributes", {}),
        children=children,
        metadata=metadata,
    )


# ============================================================================
# AST PRINTER
# ============================================================================


class ASTPrinter:
    """Pretty print AST for debugging."""

    def print(self, node: ASTNode, indent: int = 0) -> str:
        """Print AST as indented text."""
        lines = []
        indent_str = "  " * indent

        # Print node type and attributes
        attrs = ", ".join(f"{k}={v}" for k, v in node.attributes.items())
        if attrs:
            lines.append(f"{indent_str}{node.node_type.value}({attrs})")
        else:
            lines.append(f"{indent_str}{node.node_type.value}")

        # Print children
        for child in node.children:
            lines.append(self.print(child, indent + 1))

        return "\n".join(lines)


# ============================================================================
# PARSE TREE TO AST
# ============================================================================


class ParseTreeToAST:
    """Convert parse tree to AST.

    Parse trees are concrete, ASTs are abstract.
    """

    def convert(self, parse_tree: Dict[str, Any]) -> Result[ASTNode, str]:
        """Convert parse tree to AST."""
        try:
            ast = self._convert_node(parse_tree)
            return Success(ast)
        except Exception as e:
            return Error(f"Conversion failed: {e}")

    def _convert_node(self, node: Dict[str, Any]) -> ASTNode:
        """Convert parse tree node to AST node."""
        node_type = node.get("type", "unknown")

        # Map parse tree types to AST types
        type_map = {
            "window": NodeType.CLASS,
            "function": NodeType.FUNCTION,
            "statement": NodeType.BLOCK,
            "expression": NodeType.BINARY_OP,
            "identifier": NodeType.IDENTIFIER,
            "string": NodeType.STRING,
            "number": NodeType.NUMBER,
            "boolean": NodeType.BOOLEAN,
        }

        ast_type = type_map.get(node_type, NodeType.PROGRAM)

        # Convert children
        children = []
        for child in node.get("children", []):
            if isinstance(child, dict):
                children.append(self._convert_node(child))

        # Extract attributes
        attributes = {
            k: v for k, v in node.items() if k not in ["type", "children", "meta"]
        }

        return ASTNode(node_type=ast_type, children=children, attributes=attributes)
