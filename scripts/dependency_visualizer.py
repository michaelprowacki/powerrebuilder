#!/usr/bin/env python3
"""
Enhanced Dependency Visualizer for PowerRebuilder
Uses Python 3.13 features and modern visualization libraries
"""

from __future__ import annotations  # Python 3.13 default

import ast
import graphlib  # Python 3.9+ for topological sorting
import json
from collections import defaultdict
from dataclasses import dataclass, field
from enum import StrEnum, auto
from pathlib import Path
from typing import Any, override

# Python 3.13 features:
# - PEP 692: Using TypedDict for **kwargs typing
# - PEP 698: Override decorator from typing
# - Better error messages with more context
# - Improved performance for pathlib operations


class NodeType(StrEnum):
    """Types of nodes in the dependency graph"""

    MODULE = auto()
    CLASS = auto()
    FUNCTION = auto()
    DATACLASS = auto()
    ENUM = auto()
    PROTOCOL = auto()
    TYPEALIAS = auto()


@dataclass(slots=True, frozen=True)  # Python 3.10+ slots, 3.13 optimized
class CodeEntity:
    """Represents a code entity (module, class, function, etc.)"""

    name: str
    type: NodeType
    file_path: Path
    line_number: int
    imports: frozenset[str] = frozenset()
    exports: frozenset[str] = frozenset()
    decorators: frozenset[str] = frozenset()
    bases: frozenset[str] = frozenset()

    def __str__(self) -> str:
        return f"{self.type.value}:{self.name}@{self.file_path}:{self.line_number}"


@dataclass
class DependencyGraph:
    """Advanced dependency graph with Python 3.13 features"""

    entities: dict[str, CodeEntity] = field(default_factory=dict)
    dependencies: dict[str, set[str]] = field(default_factory=lambda: defaultdict(set))
    reverse_deps: dict[str, set[str]] = field(default_factory=lambda: defaultdict(set))
    circular_dependencies: list[list[str]] = field(default_factory=list)
    broken_imports: dict[str, list[str]] = field(
        default_factory=lambda: defaultdict(list)
    )

    def add_entity(self, entity: CodeEntity) -> None:
        """Add an entity to the graph"""
        self.entities[entity.name] = entity

    def add_dependency(self, from_entity: str, to_entity: str) -> None:
        """Add a dependency relationship"""
        self.dependencies[from_entity].add(to_entity)
        self.reverse_deps[to_entity].add(from_entity)

    def find_circular_dependencies(self) -> list[list[str]]:
        """Find circular dependencies using Python 3.9+ graphlib"""
        try:
            ts = graphlib.TopologicalSorter(self.dependencies)
            ts.prepare()
            # If we can do topological sort, no circular deps
            return []
        except graphlib.CycleError as e:
            # Extract cycles from the error
            cycles = []
            # Python 3.13 improved error messages provide better cycle info
            if hasattr(e, "args") and e.args:
                cycle_nodes = e.args[1] if len(e.args) > 1 else []
                if cycle_nodes:
                    cycles.append(cycle_nodes)
            return cycles

    def analyze_dataclasses(self) -> dict[str, Any]:
        """Analyze dataclass usage in the codebase"""
        dataclass_stats = {
            "total": 0,
            "frozen": 0,
            "slots": 0,
            "kw_only": 0,
            "by_module": defaultdict(int),
        }

        for entity in self.entities.values():
            if entity.type == NodeType.DATACLASS:
                dataclass_stats["total"] += 1
                module = str(entity.file_path.parent.name)
                dataclass_stats["by_module"][module] += 1

                # Check decorators for dataclass options
                if "frozen=True" in str(entity.decorators):
                    dataclass_stats["frozen"] += 1
                if "slots=True" in str(entity.decorators):
                    dataclass_stats["slots"] += 1
                if "kw_only=True" in str(entity.decorators):
                    dataclass_stats["kw_only"] += 1

        return dataclass_stats


class EnhancedASTVisitor(ast.NodeVisitor):
    """Enhanced AST visitor using Python 3.13 features"""

    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.entities: list[CodeEntity] = []
        self.current_class: str | None = None
        self.imports: set[str] = set()
        self.exports: set[str] = set()

    @override  # Python 3.12+ explicit override decorator
    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Visit class definitions"""
        decorators = {d.id for d in node.decorator_list if isinstance(d, ast.Name)}

        # Determine node type
        node_type = NodeType.CLASS
        if "dataclass" in decorators:
            node_type = NodeType.DATACLASS
        elif any(
            isinstance(base, ast.Name) and base.id == "Protocol" for base in node.bases
        ):
            node_type = NodeType.PROTOCOL
        elif any(
            isinstance(base, ast.Name) and base.id in ["Enum", "StrEnum", "IntEnum"]
            for base in node.bases
        ):
            node_type = NodeType.ENUM

        bases = {base.id for base in node.bases if isinstance(base, ast.Name)}

        entity = CodeEntity(
            name=node.name,
            type=node_type,
            file_path=self.file_path,
            line_number=node.lineno,
            decorators=frozenset(decorators),
            bases=frozenset(bases),
        )
        self.entities.append(entity)

        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = None

    @override
    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Visit function definitions"""
        if not self.current_class:  # Only track module-level functions
            entity = CodeEntity(
                name=node.name,
                type=NodeType.FUNCTION,
                file_path=self.file_path,
                line_number=node.lineno,
            )
            self.entities.append(entity)
        self.generic_visit(node)

    @override
    def visit_Import(self, node: ast.Import) -> None:
        """Track imports"""
        for alias in node.names:
            self.imports.add(alias.name)

    @override
    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Track from imports"""
        if node.module:
            self.imports.add(node.module)
            for alias in node.names:
                self.imports.add(f"{node.module}.{alias.name}")


class DependencyVisualizer:
    """Main visualizer class with multiple output formats"""

    def __init__(self, root_dir: Path = Path("src")):
        self.root_dir = root_dir
        self.graph = DependencyGraph()

    def analyze_codebase(self) -> DependencyGraph:
        """Analyze the entire codebase"""
        py_files = list(self.root_dir.rglob("*.py"))

        print(f"Analyzing {len(py_files)} Python files...")

        for py_file in py_files:
            if "__pycache__" in str(py_file):
                continue

            try:
                self._analyze_file(py_file)
            except Exception as e:
                print(f"Error analyzing {py_file}: {e}")

        # Find circular dependencies
        self.graph.circular_dependencies = self.graph.find_circular_dependencies()

        return self.graph

    def _analyze_file(self, file_path: Path) -> None:
        """Analyze a single Python file"""
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        try:
            tree = ast.parse(content, filename=str(file_path))
            visitor = EnhancedASTVisitor(file_path)
            visitor.visit(tree)

            # Add entities to graph
            for entity in visitor.entities:
                self.graph.add_entity(entity)

            # Track module-level imports
            module_name = self._path_to_module(file_path)
            for imp in visitor.imports:
                self.graph.add_dependency(module_name, imp)

        except SyntaxError as e:
            print(f"Syntax error in {file_path}: {e}")

    def _path_to_module(self, path: Path) -> str:
        """Convert file path to module name"""
        relative = path.relative_to(self.root_dir.parent)
        parts = list(relative.parts[:-1]) + [relative.stem]
        return ".".join(parts)

    def generate_mermaid_diagram(self) -> str:
        """Generate Mermaid diagram for visualization"""
        lines = ["graph TD"]

        # Add nodes
        for name, entity in self.graph.entities.items():
            match entity.type:  # Python 3.10+ pattern matching
                case NodeType.DATACLASS:
                    shape = "[" + name + "]"
                case NodeType.CLASS | NodeType.PROTOCOL:
                    shape = "(" + name + ")"
                case NodeType.FUNCTION:
                    shape = "{" + name + "}"
                case NodeType.ENUM:
                    shape = "{{" + name + "}}"
                case _:
                    shape = name

            lines.append(f"    {name.replace('.', '_')} {shape}")

        # Add edges
        for from_entity, to_entities in self.graph.dependencies.items():
            from_clean = from_entity.replace(".", "_")
            for to_entity in to_entities:
                to_clean = to_entity.replace(".", "_")
                lines.append(f"    {from_clean} --> {to_clean}")

        return "\n".join(lines)

    def generate_dot_graph(self) -> str:
        """Generate DOT format for Graphviz"""
        lines = ["digraph Dependencies {"]
        lines.append("    rankdir=LR;")
        lines.append("    node [shape=box];")

        # Group by module
        modules = defaultdict(list)
        for name, entity in self.graph.entities.items():
            module = str(entity.file_path.parent.name)
            modules[module].append(entity)

        # Create subgraphs for modules
        for module, entities in modules.items():
            lines.append(f"    subgraph cluster_{module} {{")
            lines.append(f'        label="{module}";')
            lines.append("        style=filled;")
            lines.append("        color=lightgrey;")

            for entity in entities:
                match entity.type:
                    case NodeType.DATACLASS:
                        color = "lightblue"
                    case NodeType.CLASS:
                        color = "lightgreen"
                    case NodeType.FUNCTION:
                        color = "lightyellow"
                    case NodeType.ENUM:
                        color = "lightcoral"
                    case _:
                        color = "white"

                lines.append(
                    f'        "{entity.name}" [fillcolor={color}, style=filled];'
                )

            lines.append("    }")

        # Add edges
        for from_entity, to_entities in self.graph.dependencies.items():
            for to_entity in to_entities:
                lines.append(f'    "{from_entity}" -> "{to_entity}";')

        lines.append("}")
        return "\n".join(lines)

    def generate_json_report(self) -> str:
        """Generate detailed JSON report"""
        report = {
            "statistics": {
                "total_entities": len(self.graph.entities),
                "total_dependencies": sum(
                    len(deps) for deps in self.graph.dependencies.values()
                ),
                "circular_dependencies": len(self.graph.circular_dependencies),
                "broken_imports": len(self.graph.broken_imports),
            },
            "entity_breakdown": defaultdict(int),
            "dataclass_analysis": self.graph.analyze_dataclasses(),
            "circular_dependencies": self.graph.circular_dependencies,
            "broken_imports": dict(self.graph.broken_imports),
            "most_dependent": [],
            "most_dependencies": [],
        }

        # Count entity types
        for entity in self.graph.entities.values():
            report["entity_breakdown"][entity.type.value] += 1

        # Find most dependent modules
        dependency_counts = [(k, len(v)) for k, v in self.graph.dependencies.items()]
        report["most_dependencies"] = sorted(
            dependency_counts, key=lambda x: x[1], reverse=True
        )[:10]

        reverse_counts = [(k, len(v)) for k, v in self.graph.reverse_deps.items()]
        report["most_dependent"] = sorted(
            reverse_counts, key=lambda x: x[1], reverse=True
        )[:10]

        return json.dumps(report, indent=2, default=str)


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Analyze and visualize Python dependencies"
    )
    parser.add_argument("--root", default="src", help="Root directory to analyze")
    parser.add_argument(
        "--format",
        choices=["mermaid", "dot", "json", "all"],
        default="json",
        help="Output format",
    )
    parser.add_argument("--output", help="Output file (default: stdout)")

    args = parser.parse_args()

    visualizer = DependencyVisualizer(Path(args.root))
    graph = visualizer.analyze_codebase()

    # Generate output
    match args.format:
        case "mermaid":
            output = visualizer.generate_mermaid_diagram()
        case "dot":
            output = visualizer.generate_dot_graph()
        case "json":
            output = visualizer.generate_json_report()
        case "all":
            output = f"""# Dependency Analysis Report

## Mermaid Diagram
```mermaid
{visualizer.generate_mermaid_diagram()}
```

## Statistics
{visualizer.generate_json_report()}

## DOT Graph
```dot
{visualizer.generate_dot_graph()}
```
"""
        case _:
            output = visualizer.generate_json_report()

    if args.output:
        Path(args.output).write_text(output)
        print(f"Output written to {args.output}")
    else:
        print(output)


if __name__ == "__main__":
    main()
