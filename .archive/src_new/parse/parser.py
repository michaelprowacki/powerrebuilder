"""Parse Feature - PowerBuilder source to AST parsing.

This module handles parsing of PowerBuilder source code to Abstract Syntax Trees.
Uses Lark parser with EBNF grammars for accurate parsing.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from lark import Lark, Tree, Token
from lark.exceptions import ParseError as LarkParseError

from src_new._core import (
    ASTNode,
    ObjectType,
    ParsedObject,
)
from src_new._patterns import (
    BaseCoordinator,
    BaseParser,
    FileHandler,
)
from .grammar import get_grammar_for_type

logger = logging.getLogger(__name__)


# ============================================================================
# AST BUILDER
# ============================================================================


class ASTBuilder:
    """Builds AST from Lark parse tree."""

    def build(self, tree: Tree) -> ASTNode:
        """Build AST from Lark tree.

        Args:
            tree: Lark parse tree

        Returns:
            AST node
        """
        return self._convert_node(tree)

    def _convert_node(self, node: Any) -> ASTNode:
        """Convert Lark node to AST node.

        Args:
            node: Lark Tree or Token

        Returns:
            Converted AST node
        """
        if isinstance(node, Tree):
            # Tree node
            ast_node = ASTNode(
                node_type=node.data,
                value=None,
                children=[],
                attributes={},
            )

            # Get position if available
            if hasattr(node.meta, "line"):
                ast_node.line = node.meta.line
            if hasattr(node.meta, "column"):
                ast_node.column = node.meta.column

            # Convert children
            for child in node.children:
                child_ast = self._convert_node(child)
                if child_ast:
                    ast_node.children.append(child_ast)

            return ast_node

        elif isinstance(node, Token):
            # Token node
            return ASTNode(
                node_type=node.type,
                value=node.value,
                children=[],
                attributes={},
                line=getattr(node, "line", None),
                column=getattr(node, "column", None),
            )

        else:
            # Unknown node type
            return ASTNode(
                node_type="unknown",
                value=str(node),
                children=[],
                attributes={},
            )


# ============================================================================
# POWERBUILDER PARSER
# ============================================================================


class PowerBuilderParser(BaseParser[ParsedObject]):
    """Parser for PowerBuilder source code."""

    def __init__(self, object_type: Optional[ObjectType] = None):
        """Initialize parser.

        Args:
            object_type: Expected object type (for grammar selection)
        """
        super().__init__(strict=False)
        self.object_type = object_type
        self.lark_parser = None
        self.ast_builder = ASTBuilder()

    def parse_impl(self, source: str) -> ParsedObject:
        """Parse PowerBuilder source to AST.

        Args:
            source: Source code

        Returns:
            Parsed object with AST
        """
        # Detect object type if not provided
        if not self.object_type:
            self.object_type = self._detect_object_type(source)

        # Load appropriate grammar
        grammar = get_grammar_for_type(self.object_type)
        self.lark_parser = Lark(
            grammar,
            start="start",
            parser="lalr",
            propagate_positions=True,
        )

        # Parse to Lark tree
        try:
            tree = self.lark_parser.parse(source)
        except LarkParseError as e:
            self.add_error(f"Parse error: {e}")
            # Try to create partial AST
            tree = Tree("error", [])

        # Build AST
        ast = self.ast_builder.build(tree)

        # Extract metadata
        object_name = self._extract_object_name(ast, source)
        dependencies = self._extract_dependencies(ast)

        return ParsedObject(
            object_name=object_name,
            object_type=self.object_type,
            ast=ast,
            dependencies=dependencies,
            parse_errors=self.errors.copy(),
        )

    def _detect_object_type(self, source: str) -> ObjectType:
        """Detect object type from source code.

        Args:
            source: Source code

        Returns:
            Detected object type
        """
        source_lower = source.lower()

        # Check for type indicators
        if "window type" in source_lower or "from window" in source_lower:
            return ObjectType.WINDOW
        elif "menu type" in source_lower or "from menu" in source_lower:
            return ObjectType.MENU
        elif "datawindow" in source_lower or "dataobject" in source_lower:
            return ObjectType.DATAWINDOW
        elif "application object" in source_lower:
            return ObjectType.APPLICATION
        elif "global function" in source_lower or "function " in source_lower:
            return ObjectType.FUNCTION
        elif "global structure" in source_lower or "structure " in source_lower:
            return ObjectType.STRUCTURE
        elif "from userobject" in source_lower:
            return ObjectType.USER_OBJECT
        else:
            # Default to user object
            return ObjectType.USER_OBJECT

    def _extract_object_name(self, ast: ASTNode, source: str) -> str:
        """Extract object name from AST or source.

        Args:
            ast: AST root node
            source: Source code

        Returns:
            Object name
        """
        # Look for name in AST
        name_nodes = ast.find_all("object_name")
        if name_nodes:
            return str(name_nodes[0].value)

        # Try to extract from source
        import re

        # Look for type declaration
        match = re.search(r"type\s+(\w+)\s+from", source, re.IGNORECASE)
        if match:
            return match.group(1)

        # Look for global declaration
        match = re.search(r"global\s+\w+\s+(\w+)", source, re.IGNORECASE)
        if match:
            return match.group(1)

        return "unknown"

    def _extract_dependencies(self, ast: ASTNode) -> List[str]:
        """Extract dependencies from AST.

        Args:
            ast: AST root node

        Returns:
            List of dependency names
        """
        dependencies = []

        # Look for inheritance
        from_nodes = ast.find_all("from_clause")
        for node in from_nodes:
            if node.children:
                dep_name = str(node.children[0].value)
                if dep_name not in dependencies:
                    dependencies.append(dep_name)

        # Look for using statements
        using_nodes = ast.find_all("using_statement")
        for node in using_nodes:
            if node.children:
                dep_name = str(node.children[0].value)
                if dep_name not in dependencies:
                    dependencies.append(dep_name)

        # Look for type references
        type_nodes = ast.find_all("type_reference")
        for node in type_nodes:
            if node.value:
                dep_name = str(node.value)
                # Filter out primitive types
                if not self._is_primitive_type(dep_name):
                    if dep_name not in dependencies:
                        dependencies.append(dep_name)

        return dependencies

    def _is_primitive_type(self, type_name: str) -> bool:
        """Check if type is primitive.

        Args:
            type_name: Type name

        Returns:
            True if primitive
        """
        primitives = {
            "integer",
            "int",
            "long",
            "ulong",
            "decimal",
            "dec",
            "real",
            "double",
            "float",
            "string",
            "char",
            "boolean",
            "bool",
            "date",
            "time",
            "datetime",
            "blob",
            "any",
        }
        return type_name.lower() in primitives


# ============================================================================
# PARSE COORDINATOR
# ============================================================================


class ParseCoordinator(BaseCoordinator):
    """Coordinator for parsing stage.

    Parses PowerBuilder source files to AST.
    """

    @property
    def stage_name(self) -> str:
        """Get stage name."""
        return "parse"

    def discover_files(self) -> List[Path]:
        """Discover source files to process.

        Returns:
            List of source files
        """
        if self.input_path.is_file():
            # Single file - check if it's a source file
            if self._is_source_file(self.input_path):
                return [self.input_path]
            else:
                raise ValueError(f"Not a source file: {self.input_path}")
        else:
            # Directory - find all source files
            files = []
            for ext in [".sru", ".srw", ".srm", ".srd", ".srs", ".srf", ".sra"]:
                files.extend(self.input_path.rglob(f"*{ext}"))
            return files

    def process_file(self, input_file: Path, output_dir: Path) -> bool:
        """Process a single source file.

        Args:
            input_file: Source file path
            output_dir: Output directory

        Returns:
            True if successful
        """
        try:
            self.logger.info(f"Parsing: {input_file}")

            # Read source
            file_handler = FileHandler()
            source = file_handler.read_text(input_file)

            # Detect object type from extension
            object_type = self._detect_type_from_extension(input_file)

            # Parse to AST
            parser = PowerBuilderParser(object_type)
            result = parser.parse(source)

            if not result.success:
                self.logger.warning(f"Parse errors in {input_file}: {result.errors}")

            # Convert AST to JSON for storage
            ast_json = self._ast_to_json(result.data.ast)

            # Create output structure
            output_data = {
                "object_name": result.data.object_name,
                "object_type": result.data.object_type.value,
                "ast": ast_json,
                "dependencies": result.data.dependencies,
                "parse_errors": result.data.parse_errors,
                "source_file": str(input_file),
            }

            # Write AST to JSON file
            output_file = output_dir / f"{input_file.stem}.ast.json"
            file_handler.write_json(output_file, output_data, indent=2)

            self.logger.info(f"Parsed to: {output_file}")
            return result.success

        except Exception as e:
            self.logger.error(f"Failed to parse {input_file}: {e}")
            return False

    def _is_source_file(self, path: Path) -> bool:
        """Check if file is a PowerBuilder source file.

        Args:
            path: File path

        Returns:
            True if source file
        """
        source_extensions = {".sru", ".srw", ".srm", ".srd", ".srs", ".srf", ".sra"}
        return path.suffix.lower() in source_extensions

    def _detect_type_from_extension(self, path: Path) -> ObjectType:
        """Detect object type from file extension.

        Args:
            path: File path

        Returns:
            Object type
        """
        ext_map = {
            ".sra": ObjectType.APPLICATION,
            ".srw": ObjectType.WINDOW,
            ".sru": ObjectType.USER_OBJECT,
            ".srm": ObjectType.MENU,
            ".srf": ObjectType.FUNCTION,
            ".srd": ObjectType.DATAWINDOW,
            ".srs": ObjectType.STRUCTURE,
        }
        return ext_map.get(path.suffix.lower(), ObjectType.USER_OBJECT)

    def _ast_to_json(self, ast: ASTNode) -> Dict[str, Any]:
        """Convert AST to JSON-serializable format.

        Args:
            ast: AST node

        Returns:
            JSON dictionary
        """
        result = {
            "node_type": ast.node_type,
            "value": ast.value,
            "children": [],
            "attributes": ast.attributes,
        }

        if ast.line is not None:
            result["line"] = ast.line
        if ast.column is not None:
            result["column"] = ast.column

        # Convert children
        for child in ast.children:
            result["children"].append(self._ast_to_json(child))

        return result
