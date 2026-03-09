"""Model Feature - AST to semantic model transformation.

This module builds semantic models from parsed ASTs, resolving types and dependencies.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List

from src_new._core import (
    ApplicationModel,
    ASTNode,
    Event,
    Method,
    ObjectType,
    Parameter,
    Property,
    SemanticObject,
)
from src_new._patterns import (
    BaseCoordinator,
    FileHandler,
)

logger = logging.getLogger(__name__)


# ============================================================================
# AST VISITOR
# ============================================================================


class ASTVisitor:
    """Visitor pattern for traversing AST nodes."""

    def visit(self, node: ASTNode) -> Any:
        """Visit a node and dispatch to appropriate handler.

        Args:
            node: AST node to visit

        Returns:
            Result from handler
        """
        method_name = f"visit_{node.node_type}"
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node: ASTNode) -> Any:
        """Default visitor for unhandled node types.

        Args:
            node: AST node

        Returns:
            None by default
        """
        # Visit all children
        for child in node.children:
            self.visit(child)
        return None


class SemanticModelBuilder(ASTVisitor):
    """Builds semantic models from AST."""

    def __init__(self):
        """Initialize builder."""
        self.current_object = None
        self.properties = []
        self.methods = []
        self.events = []
        self.dependencies = []

    def build(self, ast: ASTNode, object_type: ObjectType) -> SemanticObject:
        """Build semantic model from AST.

        Args:
            ast: AST root node
            object_type: Object type

        Returns:
            Semantic model
        """
        # Initialize new object
        self.current_object = SemanticObject(
            name="",
            type=object_type,
        )
        self.properties = []
        self.methods = []
        self.events = []
        self.dependencies = []

        # Visit AST
        self.visit(ast)

        # Populate object
        self.current_object.properties = self.properties
        self.current_object.methods = self.methods
        self.current_object.events = self.events
        self.current_object.dependencies = self.dependencies

        return self.current_object

    def visit_object_declaration(self, node: ASTNode) -> None:
        """Visit object declaration node."""
        # Extract object name
        for child in node.children:
            if child.node_type == "object_name":
                self.current_object.name = str(child.value)
            elif child.node_type == "parent_name":
                self.current_object.parent = str(child.value)

        # Continue visiting children
        self.generic_visit(node)

    def visit_type_decl(self, node: ASTNode) -> None:
        """Visit type declaration."""
        for child in node.children:
            if child.node_type == "object_name":
                self.current_object.name = str(child.value)
            elif child.node_type == "parent_name":
                self.current_object.parent = str(child.value)

        self.generic_visit(node)

    def visit_variable_decl(self, node: ASTNode) -> None:
        """Visit variable declaration."""
        prop = Property(
            name="",
            type="any",
            access="public",
        )

        for child in node.children:
            if child.node_type == "variable_name":
                prop.name = str(child.value)
            elif child.node_type == "type_name":
                prop.type = str(child.value)
            elif child.node_type == "access_modifier":
                prop.access = str(child.value)
            elif child.node_type == "expression":
                prop.default_value = self._extract_value(child)

        if prop.name:
            self.properties.append(prop)

    def visit_function_decl(self, node: ASTNode) -> None:
        """Visit function declaration."""
        method = Method(
            name="",
            return_type=None,
            parameters=[],
            access="public",
        )

        for child in node.children:
            if child.node_type == "function_name":
                method.name = str(child.value)
            elif child.node_type == "type_name":
                method.return_type = str(child.value)
            elif child.node_type == "access_modifier":
                method.access = str(child.value)
            elif child.node_type == "parameter_list":
                method.parameters = self._extract_parameters(child)
            elif child.node_type == "statement_block":
                method.body = self._extract_body(child)

        if method.name:
            self.methods.append(method)

    def visit_event_decl(self, node: ASTNode) -> None:
        """Visit event declaration."""
        event = Event(
            name="",
            parameters=[],
        )

        for child in node.children:
            if child.node_type == "event_name":
                event.name = str(child.value)
            elif child.node_type == "parameter_list":
                event.parameters = self._extract_parameters(child)
            elif child.node_type == "statement_block":
                event.body = self._extract_body(child)

        if event.name:
            self.events.append(event)

    def _extract_parameters(self, node: ASTNode) -> List[Parameter]:
        """Extract parameters from parameter list node.

        Args:
            node: Parameter list node

        Returns:
            List of parameters
        """
        parameters = []

        for child in node.children:
            if child.node_type == "parameter":
                param = Parameter(
                    name="",
                    type="any",
                )

                for param_child in child.children:
                    if param_child.node_type == "variable_name":
                        param.name = str(param_child.value)
                    elif param_child.node_type == "type_name":
                        param.type = str(param_child.value)

                if param.name:
                    parameters.append(param)

        return parameters

    def _extract_body(self, node: ASTNode) -> str:
        """Extract body as string.

        Args:
            node: Statement block node

        Returns:
            Body as string
        """
        # Simple extraction - real implementation would rebuild code
        body_lines = []
        for child in node.children:
            if child.value:
                body_lines.append(str(child.value))
        return "\n".join(body_lines)

    def _extract_value(self, node: ASTNode) -> Any:
        """Extract value from expression node.

        Args:
            node: Expression node

        Returns:
            Extracted value
        """
        if node.value is not None:
            return node.value

        # Try to reconstruct from children
        if node.children:
            values = []
            for child in node.children:
                val = self._extract_value(child)
                if val is not None:
                    values.append(str(val))
            return " ".join(values) if values else None

        return None


# ============================================================================
# DEPENDENCY RESOLVER
# ============================================================================


class DependencyResolver:
    """Resolves dependencies between semantic objects."""

    def __init__(self):
        """Initialize resolver."""
        self.objects = {}
        self.resolved = {}

    def add_object(self, obj: SemanticObject) -> None:
        """Add object to resolver.

        Args:
            obj: Semantic object
        """
        self.objects[obj.name] = obj

    def resolve(self) -> None:
        """Resolve all dependencies."""
        for name, obj in self.objects.items():
            self._resolve_object(obj)

    def _resolve_object(self, obj: SemanticObject) -> None:
        """Resolve dependencies for an object.

        Args:
            obj: Object to resolve
        """
        if obj.name in self.resolved:
            return

        # Mark as being resolved to detect cycles
        self.resolved[obj.name] = False

        # Resolve parent
        if obj.parent and obj.parent in self.objects:
            parent = self.objects[obj.parent]
            if obj.parent not in self.resolved:
                self._resolve_object(parent)

            # Inherit from parent
            self._inherit_from_parent(obj, parent)

        # Resolve type references
        for prop in obj.properties:
            self._resolve_type(prop.type)

        for method in obj.methods:
            if method.return_type:
                self._resolve_type(method.return_type)
            for param in method.parameters:
                self._resolve_type(param.type)

        # Mark as resolved
        self.resolved[obj.name] = True

    def _inherit_from_parent(
        self, child: SemanticObject, parent: SemanticObject
    ) -> None:
        """Apply inheritance from parent to child.

        Args:
            child: Child object
            parent: Parent object
        """
        # Copy properties not overridden
        for parent_prop in parent.properties:
            if not any(p.name == parent_prop.name for p in child.properties):
                child.properties.append(parent_prop)

        # Copy methods not overridden
        for parent_method in parent.methods:
            if not any(m.name == parent_method.name for m in child.methods):
                child.methods.append(parent_method)

        # Copy events not overridden
        for parent_event in parent.events:
            if not any(e.name == parent_event.name for e in child.events):
                child.events.append(parent_event)

    def _resolve_type(self, type_name: str) -> str:
        """Resolve a type reference.

        Args:
            type_name: Type to resolve

        Returns:
            Resolved type
        """
        # Check if it's a known object
        if type_name in self.objects:
            return type_name

        # Map PowerBuilder types to standard types
        type_map = {
            "integer": "int",
            "long": "long",
            "decimal": "decimal",
            "real": "float",
            "double": "double",
            "string": "string",
            "boolean": "bool",
            "date": "date",
            "time": "time",
            "datetime": "datetime",
        }

        return type_map.get(type_name.lower(), type_name)


# ============================================================================
# MODEL COORDINATOR
# ============================================================================


class ModelCoordinator(BaseCoordinator):
    """Coordinator for model building stage.

    Transforms ASTs into semantic models with resolved dependencies.
    """

    def __init__(self, *args, **kwargs):
        """Initialize coordinator."""
        super().__init__(*args, **kwargs)
        self.application_model = ApplicationModel(
            name="PowerBuilderApp",
            version="1.0.0",
        )
        self.resolver = DependencyResolver()

    @property
    def stage_name(self) -> str:
        """Get stage name."""
        return "model"

    def discover_files(self) -> List[Path]:
        """Discover AST JSON files to process.

        Returns:
            List of AST files
        """
        if self.input_path.is_file():
            if self.input_path.suffix == ".json":
                return [self.input_path]
            else:
                raise ValueError(f"Not an AST JSON file: {self.input_path}")
        else:
            # Find all AST JSON files
            return list(self.input_path.rglob("*.ast.json"))

    def process_file(self, input_file: Path, output_dir: Path) -> bool:
        """Process a single AST file.

        Args:
            input_file: AST JSON file
            output_dir: Output directory

        Returns:
            True if successful
        """
        try:
            self.logger.info(f"Building model from: {input_file}")

            # Read AST JSON
            file_handler = FileHandler()
            ast_data = file_handler.read_json(input_file)

            # Reconstruct AST
            ast = self._json_to_ast(ast_data["ast"])
            object_type = ObjectType(ast_data["object_type"])

            # Build semantic model
            builder = SemanticModelBuilder()
            semantic_obj = builder.build(ast, object_type)

            # Use name from AST data if available
            if ast_data.get("object_name"):
                semantic_obj.name = ast_data["object_name"]

            # Add dependencies from AST data
            if ast_data.get("dependencies"):
                semantic_obj.dependencies = ast_data["dependencies"]

            # Add to resolver
            self.resolver.add_object(semantic_obj)

            # Add to application model
            self.application_model.objects[semantic_obj.name] = semantic_obj

            # Write individual model
            output_file = output_dir / f"{input_file.stem}.model.json"
            model_data = self._semantic_to_json(semantic_obj)
            file_handler.write_json(output_file, model_data, indent=2)

            self.logger.info(f"Built model: {output_file}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to build model from {input_file}: {e}")
            return False

    def process(self) -> Any:
        """Process all files and resolve dependencies."""
        # Process individual files
        result = super().process()

        # Resolve dependencies after all objects are loaded
        self.logger.info("Resolving dependencies...")
        self.resolver.resolve()

        # Write complete application model
        file_handler = FileHandler()
        app_model_file = self.output_path / "application_model.json"
        app_model_data = self._application_to_json(self.application_model)
        file_handler.write_json(app_model_file, app_model_data, indent=2)

        self.logger.info(f"Complete model written to: {app_model_file}")

        return result

    def _json_to_ast(self, data: Dict[str, Any]) -> ASTNode:
        """Convert JSON to AST node.

        Args:
            data: JSON data

        Returns:
            AST node
        """
        node = ASTNode(
            node_type=data["node_type"],
            value=data.get("value"),
            children=[],
            attributes=data.get("attributes", {}),
            line=data.get("line"),
            column=data.get("column"),
        )

        # Convert children
        for child_data in data.get("children", []):
            node.children.append(self._json_to_ast(child_data))

        return node

    def _semantic_to_json(self, obj: SemanticObject) -> Dict[str, Any]:
        """Convert semantic object to JSON.

        Args:
            obj: Semantic object

        Returns:
            JSON data
        """
        return {
            "name": obj.name,
            "type": obj.type.value,
            "parent": obj.parent,
            "properties": [
                {
                    "name": p.name,
                    "type": p.type,
                    "access": p.access,
                    "default_value": p.default_value,
                }
                for p in obj.properties
            ],
            "methods": [
                {
                    "name": m.name,
                    "return_type": m.return_type,
                    "access": m.access,
                    "parameters": [
                        {"name": p.name, "type": p.type} for p in m.parameters
                    ],
                }
                for m in obj.methods
            ],
            "events": [
                {
                    "name": e.name,
                    "parameters": [
                        {"name": p.name, "type": p.type} for p in e.parameters
                    ],
                }
                for e in obj.events
            ],
            "dependencies": obj.dependencies,
        }

    def _application_to_json(self, app: ApplicationModel) -> Dict[str, Any]:
        """Convert application model to JSON.

        Args:
            app: Application model

        Returns:
            JSON data
        """
        return {
            "name": app.name,
            "version": app.version,
            "entry_point": app.entry_point,
            "objects": {
                name: self._semantic_to_json(obj) for name, obj in app.objects.items()
            },
            "global_functions": [
                {
                    "name": m.name,
                    "return_type": m.return_type,
                    "parameters": [
                        {"name": p.name, "type": p.type} for p in m.parameters
                    ],
                }
                for m in app.global_functions
            ],
            "global_variables": [
                {
                    "name": p.name,
                    "type": p.type,
                    "default_value": p.default_value,
                }
                for p in app.global_variables
            ],
        }
