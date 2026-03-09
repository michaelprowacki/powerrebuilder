"""Analyze Dependencies - Self-Contained FDM Module.

Following Scott Wlaschin's functional domain modeling principles:
- Types are co-located with the functions that use them (no separate type files)
- All data structures are immutable using frozen dataclasses
- Functions are pure and return Result types for error handling
- No external dependencies except the core Result type
- Uses domain language from dependency analysis problem space

This module is completely self-contained - both types and operations
for analyzing code dependencies live together in this single file.
"""

from typing import List, Dict, Set, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

from src_new._core.result import Result, Success, Failure
from src_new._core.legacy_modernization_types import LegacyApplicationModel


# ============================================================================
# DEPENDENCY TYPES
# ============================================================================


class DependencyType(str, Enum):
    """Types of dependencies."""

    # Code dependencies
    IMPORTS = "imports"  # Import/using statements
    INHERITANCE = "inheritance"  # Class inheritance
    COMPOSITION = "composition"  # Object composition
    FUNCTION_CALL = "function_call"  # Function/method calls

    # Data dependencies
    DATA_ACCESS = "data_access"  # Database table access
    FILE_ACCESS = "file_access"  # File system access
    API_CALL = "api_call"  # External API calls

    # UI dependencies
    UI_NAVIGATION = "ui_navigation"  # Screen navigation
    UI_EMBEDDING = "ui_embedding"  # Embedded controls
    EVENT_HANDLER = "event_handler"  # Event handling

    # External
    LIBRARY = "library"  # External library
    FRAMEWORK = "framework"  # Framework dependency
    SERVICE = "service"  # External service


class DependencyScope(str, Enum):
    """Scope of dependencies."""

    INTERNAL = "internal"  # Within same module
    LOCAL = "local"  # Within same package
    PROJECT = "project"  # Within same project
    EXTERNAL = "external"  # External dependency
    SYSTEM = "system"  # System/OS dependency


class ImpactLevel(str, Enum):
    """Impact level of changes."""

    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(frozen=True)
class Dependency:
    """A dependency between components."""

    source: str  # Source component
    target: str  # Target component
    dependency_type: DependencyType
    scope: DependencyScope

    # Optional details
    version: Optional[str] = None
    is_required: bool = True
    is_circular: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class DependencyGraph:
    """Complete dependency graph."""

    nodes: Dict[str, "ComponentNode"]
    edges: List[Dependency]

    # Analysis results
    cycles: List[List[str]]  # Circular dependencies
    layers: List[Set[str]]  # Dependency layers
    critical_path: List[str]  # Critical dependency path

    # Metrics
    coupling_score: float  # 0.0 (low) to 1.0 (high)
    cohesion_score: float  # 0.0 (low) to 1.0 (high)
    complexity_score: float  # Overall complexity


@dataclass(frozen=True)
class ComponentNode:
    """A component in the dependency graph."""

    name: str
    component_type: str  # class, module, package, etc.

    # Dependencies
    depends_on: Set[str]  # What this component depends on
    depended_by: Set[str]  # What depends on this component

    # Metrics
    fan_in: int  # Number of incoming dependencies
    fan_out: int  # Number of outgoing dependencies
    instability: float  # Fan-out / (Fan-in + Fan-out)

    # Properties
    is_leaf: bool  # No dependencies
    is_hub: bool  # Many dependencies
    is_isolated: bool  # No connections


@dataclass(frozen=True)
class ImpactAnalysis:
    """Impact analysis results."""

    changed_component: str
    impact_level: ImpactLevel

    # Affected components
    directly_affected: Set[str]
    transitively_affected: Set[str]

    # Risk assessment
    affected_tests: List[str]
    affected_ui: List[str]
    affected_data: List[str]

    # Migration order
    migration_order: List[str]  # Order to migrate components
    can_parallelize: List[Set[str]]  # Groups that can be done in parallel


@dataclass(frozen=True)
class DependencyAnalysisError:
    """Error during dependency analysis."""

    error_type: str
    message: str
    component: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)


# ============================================================================
# DEPENDENCY EXTRACTION
# ============================================================================


def extract_dependencies(
    model: LegacyApplicationModel,
) -> Result[DependencyGraph, DependencyAnalysisError]:
    """Extract dependencies from application model.

    Pure function: Model -> Result[Graph, Error]
    """
    nodes = {}
    edges = []

    # Extract from code modules
    for module_name, module in model.code_modules.items():
        deps = _extract_module_dependencies(module)

        # Create node
        depends_on = {d.target for d in deps}
        nodes[module_name] = ComponentNode(
            name=module_name,
            component_type="module",
            depends_on=depends_on,
            depended_by=set(),
            fan_out=len(depends_on),
            fan_in=0,
            instability=1.0,
            is_leaf=len(depends_on) == 0,
            is_hub=False,
            is_isolated=False,
        )

        edges.extend(deps)

    # Extract UI dependencies
    for ui_name, ui_container in model.ui_containers.items():
        deps = _extract_ui_dependencies(ui_container, ui_name)

        if ui_name not in nodes:
            nodes[ui_name] = ComponentNode(
                name=ui_name,
                component_type="ui_container",
                depends_on={d.target for d in deps},
                depended_by=set(),
                fan_out=len(deps),
                fan_in=0,
                instability=1.0,
                is_leaf=len(deps) == 0,
                is_hub=False,
                is_isolated=False,
            )

        edges.extend(deps)

    # Update depended_by and fan_in
    for edge in edges:
        if edge.target in nodes:
            nodes[edge.target] = ComponentNode(
                name=nodes[edge.target].name,
                component_type=nodes[edge.target].component_type,
                depends_on=nodes[edge.target].depends_on,
                depended_by=nodes[edge.target].depended_by | {edge.source},
                fan_out=nodes[edge.target].fan_out,
                fan_in=nodes[edge.target].fan_in + 1,
                instability=nodes[edge.target].instability,
                is_leaf=nodes[edge.target].is_leaf,
                is_hub=nodes[edge.target].is_hub,
                is_isolated=nodes[edge.target].is_isolated,
            )

    # Recalculate metrics
    for name, node in nodes.items():
        total = node.fan_in + node.fan_out
        instability = node.fan_out / total if total > 0 else 0
        is_hub = node.fan_in > 5 or node.fan_out > 5
        is_isolated = node.fan_in == 0 and node.fan_out == 0

        nodes[name] = ComponentNode(
            name=node.name,
            component_type=node.component_type,
            depends_on=node.depends_on,
            depended_by=node.depended_by,
            fan_out=node.fan_out,
            fan_in=node.fan_in,
            instability=instability,
            is_leaf=node.is_leaf,
            is_hub=is_hub,
            is_isolated=is_isolated,
        )

    # Detect cycles
    cycles = _detect_cycles(nodes)

    # Create layers
    layers = _create_dependency_layers(nodes)

    # Find critical path
    critical_path = _find_critical_path(nodes)

    # Calculate metrics
    coupling = _calculate_coupling(nodes, edges)
    cohesion = _calculate_cohesion(nodes, edges)
    complexity = _calculate_complexity(nodes, edges, cycles)

    graph = DependencyGraph(
        nodes=nodes,
        edges=edges,
        cycles=cycles,
        layers=layers,
        critical_path=critical_path,
        coupling_score=coupling,
        cohesion_score=cohesion,
        complexity_score=complexity,
    )

    return Success(graph)


# ============================================================================
# IMPACT ANALYSIS
# ============================================================================


def analyze_impact(
    graph: DependencyGraph, changed_component: str
) -> Result[ImpactAnalysis, DependencyAnalysisError]:
    """Analyze impact of changing a component.

    Pure function: (Graph, Component) -> Result[Impact, Error]
    """
    if changed_component not in graph.nodes:
        return Failure(
            DependencyAnalysisError(
                error_type="ComponentNotFound",
                message=f"Component {changed_component} not found",
                component=changed_component,
            )
        )

    node = graph.nodes[changed_component]

    # Find directly affected
    directly_affected = node.depended_by.copy()

    # Find transitively affected
    transitively_affected = _find_transitive_dependents(graph.nodes, changed_component)

    # Determine impact level
    total_affected = len(directly_affected) + len(transitively_affected)
    total_components = len(graph.nodes)

    if total_affected == 0:
        impact_level = ImpactLevel.NONE
    elif total_affected / total_components < 0.1:
        impact_level = ImpactLevel.LOW
    elif total_affected / total_components < 0.3:
        impact_level = ImpactLevel.MEDIUM
    elif total_affected / total_components < 0.5:
        impact_level = ImpactLevel.HIGH
    else:
        impact_level = ImpactLevel.CRITICAL

    # Find affected subsystems
    affected_tests = []
    affected_ui = []
    affected_data = []

    for component in directly_affected | transitively_affected:
        if "test" in component.lower():
            affected_tests.append(component)
        elif graph.nodes[component].component_type == "ui_container":
            affected_ui.append(component)
        elif "data" in component.lower() or "model" in component.lower():
            affected_data.append(component)

    # Determine migration order
    migration_order = _determine_migration_order(graph, changed_component)

    # Find parallelizable groups
    can_parallelize = _find_parallel_groups(graph, migration_order)

    return Success(
        ImpactAnalysis(
            changed_component=changed_component,
            impact_level=impact_level,
            directly_affected=directly_affected,
            transitively_affected=transitively_affected,
            affected_tests=affected_tests,
            affected_ui=affected_ui,
            affected_data=affected_data,
            migration_order=migration_order,
            can_parallelize=can_parallelize,
        )
    )


# ============================================================================
# MIGRATION ORDERING
# ============================================================================


def determine_migration_order(
    graph: DependencyGraph,
) -> Result[List[str], DependencyAnalysisError]:
    """Determine optimal migration order.

    Pure function: Graph -> Result[Order, Error]
    """
    if graph.cycles:
        # Handle circular dependencies
        return _handle_circular_migration(graph)

    # Topological sort
    order = _topological_sort(graph.nodes)

    if not order:
        return Failure(
            DependencyAnalysisError(
                error_type="SortError", message="Could not determine migration order"
            )
        )

    return Success(order)


def find_migration_groups(
    graph: DependencyGraph,
) -> Result[List[Set[str]], DependencyAnalysisError]:
    """Find groups that can be migrated together.

    Pure function: Graph -> Result[Groups, Error]
    """
    # Group by dependency layers
    groups = []

    for layer in graph.layers:
        # Check if layer components are independent
        independent_group = set()

        for component in layer:
            # Check dependencies within layer
            deps_in_layer = graph.nodes[component].depends_on & layer
            if not deps_in_layer:
                independent_group.add(component)

        if independent_group:
            groups.append(independent_group)

    return Success(groups)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def _extract_module_dependencies(module: Any) -> List[Dependency]:
    """Extract dependencies from a code module."""
    deps = []

    # Check imports/dependencies
    if hasattr(module, "dependencies"):
        for dep in module.dependencies:
            deps.append(
                Dependency(
                    source=module.name,
                    target=dep,
                    dependency_type=DependencyType.IMPORTS,
                    scope=DependencyScope.PROJECT,
                )
            )

    # Check function calls
    if hasattr(module, "functions"):
        for func in module.functions:
            if hasattr(func, "calls"):
                for call in func.calls:
                    deps.append(
                        Dependency(
                            source=module.name,
                            target=call,
                            dependency_type=DependencyType.FUNCTION_CALL,
                            scope=DependencyScope.PROJECT,
                        )
                    )

    return deps


def _extract_ui_dependencies(ui_container: Any, name: str) -> List[Dependency]:
    """Extract dependencies from UI container."""
    deps = []

    # Check event handlers
    if hasattr(ui_container, "event_handlers"):
        for handler in ui_container.event_handlers:
            if hasattr(handler, "target"):
                deps.append(
                    Dependency(
                        source=name,
                        target=handler.target,
                        dependency_type=DependencyType.EVENT_HANDLER,
                        scope=DependencyScope.PROJECT,
                    )
                )

    # Check embedded controls
    if hasattr(ui_container, "controls"):
        for control in ui_container.controls:
            if hasattr(control, "type") and "embed" in control.type.lower():
                deps.append(
                    Dependency(
                        source=name,
                        target=control.name,
                        dependency_type=DependencyType.UI_EMBEDDING,
                        scope=DependencyScope.LOCAL,
                    )
                )

    return deps


def _detect_cycles(nodes: Dict[str, ComponentNode]) -> List[List[str]]:
    """Detect circular dependencies using DFS."""
    cycles = []
    visited = set()
    rec_stack = set()

    def dfs(node_name: str, path: List[str]) -> None:
        visited.add(node_name)
        rec_stack.add(node_name)
        path.append(node_name)

        for neighbor in nodes[node_name].depends_on:
            if neighbor not in visited:
                dfs(neighbor, path.copy())
            elif neighbor in rec_stack:
                # Found cycle
                cycle_start = path.index(neighbor)
                cycle = path[cycle_start:] + [neighbor]
                cycles.append(cycle)

        path.pop()
        rec_stack.remove(node_name)

    for node_name in nodes:
        if node_name not in visited:
            dfs(node_name, [])

    return cycles


def _create_dependency_layers(nodes: Dict[str, ComponentNode]) -> List[Set[str]]:
    """Create dependency layers (level-order)."""
    layers = []
    processed = set()

    # Find leaf nodes (no dependencies)
    current_layer = {name for name, node in nodes.items() if node.is_leaf}

    while current_layer:
        layers.append(current_layer)
        processed.update(current_layer)

        # Find next layer
        next_layer = set()
        for name, node in nodes.items():
            if name not in processed:
                # Check if all dependencies are processed
                if node.depends_on.issubset(processed):
                    next_layer.add(name)

        current_layer = next_layer

    # Add remaining nodes (likely in cycles)
    remaining = set(nodes.keys()) - processed
    if remaining:
        layers.append(remaining)

    return layers


def _find_critical_path(nodes: Dict[str, ComponentNode]) -> List[str]:
    """Find the critical dependency path."""
    # Find node with highest fan-out
    if not nodes:
        return []

    start_node = max(nodes.values(), key=lambda n: n.fan_out)

    # DFS to find longest path
    def find_longest_path(node_name: str, visited: Set[str]) -> List[str]:
        if node_name in visited:
            return []

        visited.add(node_name)

        longest = []
        for dep in nodes[node_name].depends_on:
            if dep in nodes:
                path = find_longest_path(dep, visited.copy())
                if len(path) > len(longest):
                    longest = path

        return [node_name] + longest

    return find_longest_path(start_node.name, set())


def _calculate_coupling(
    nodes: Dict[str, ComponentNode], edges: List[Dependency]
) -> float:
    """Calculate coupling score (0.0 = low, 1.0 = high)."""
    if not nodes:
        return 0.0

    total_possible = len(nodes) * (len(nodes) - 1)
    actual_edges = len(edges)

    if total_possible == 0:
        return 0.0

    return min(actual_edges / total_possible, 1.0)


def _calculate_cohesion(
    nodes: Dict[str, ComponentNode], edges: List[Dependency]
) -> float:
    """Calculate cohesion score (0.0 = low, 1.0 = high)."""
    # Group components by type
    groups = {}
    for node in nodes.values():
        if node.component_type not in groups:
            groups[node.component_type] = []
        groups[node.component_type].append(node.name)

    # Calculate intra-group vs inter-group edges
    intra_edges = 0
    inter_edges = 0

    for edge in edges:
        source_group = None
        target_group = None

        for group_type, members in groups.items():
            if edge.source in members:
                source_group = group_type
            if edge.target in members:
                target_group = group_type

        if source_group == target_group:
            intra_edges += 1
        else:
            inter_edges += 1

    total = intra_edges + inter_edges
    if total == 0:
        return 1.0

    return intra_edges / total


def _calculate_complexity(
    nodes: Dict[str, ComponentNode], edges: List[Dependency], cycles: List[List[str]]
) -> float:
    """Calculate overall complexity score."""
    # Factors:
    # 1. Number of nodes
    # 2. Number of edges
    # 3. Number of cycles
    # 4. Average fan-out

    node_factor = len(nodes) / 100  # Normalize to 100 nodes
    edge_factor = len(edges) / (len(nodes) * 2) if nodes else 0
    cycle_factor = len(cycles) / 10  # Normalize to 10 cycles

    avg_fanout = sum(n.fan_out for n in nodes.values()) / len(nodes) if nodes else 0
    fanout_factor = avg_fanout / 10  # Normalize to 10 dependencies

    # Weighted average
    complexity = (
        node_factor * 0.2 + edge_factor * 0.3 + cycle_factor * 0.3 + fanout_factor * 0.2
    )

    return min(complexity, 1.0)


def _find_transitive_dependents(
    nodes: Dict[str, ComponentNode], component: str
) -> Set[str]:
    """Find all transitive dependents of a component."""
    dependents = set()
    to_process = list(nodes[component].depended_by)

    while to_process:
        current = to_process.pop()
        if current not in dependents:
            dependents.add(current)
            if current in nodes:
                to_process.extend(nodes[current].depended_by)

    return dependents


def _determine_migration_order(graph: DependencyGraph, start: str) -> List[str]:
    """Determine migration order starting from a component."""
    # BFS to find all reachable components
    order = []
    visited = set()
    queue = [start]

    while queue:
        current = queue.pop(0)
        if current not in visited:
            visited.add(current)
            order.append(current)

            # Add dependencies first
            if current in graph.nodes:
                for dep in graph.nodes[current].depends_on:
                    if dep not in visited:
                        queue.insert(0, dep)  # Priority to dependencies

    return order


def _find_parallel_groups(graph: DependencyGraph, order: List[str]) -> List[Set[str]]:
    """Find groups that can be migrated in parallel."""
    groups = []
    processed = set()

    for component in order:
        if component in processed:
            continue

        # Find components at same level
        group = {component}

        for other in order:
            if other not in processed and other != component:
                # Check if they don't depend on each other
                if (
                    other not in graph.nodes[component].depends_on
                    and component not in graph.nodes[other].depends_on
                ):
                    # Check if they have same dependencies already processed
                    if graph.nodes[other].depends_on.issubset(processed):
                        group.add(other)

        groups.append(group)
        processed.update(group)

    return groups


def _topological_sort(nodes: Dict[str, ComponentNode]) -> List[str]:
    """Topological sort of dependency graph."""
    in_degree = {name: node.fan_in for name, node in nodes.items()}
    queue = [name for name, degree in in_degree.items() if degree == 0]
    result = []

    while queue:
        current = queue.pop(0)
        result.append(current)

        # Reduce in-degree of dependents
        if current in nodes:
            for dependent in nodes[current].depended_by:
                if dependent in in_degree:
                    in_degree[dependent] -= 1
                    if in_degree[dependent] == 0:
                        queue.append(dependent)

    # Check if all nodes are processed
    if len(result) != len(nodes):
        return []  # Cycle detected

    return result


def _handle_circular_migration(
    graph: DependencyGraph,
) -> Result[List[str], DependencyAnalysisError]:
    """Handle migration order when cycles exist."""
    # Strategy: Break cycles at weakest points
    order = []

    # Start with non-cycle components
    cycle_components = set()
    for cycle in graph.cycles:
        cycle_components.update(cycle)

    non_cycle = [name for name in graph.nodes if name not in cycle_components]

    # Sort non-cycle components
    non_cycle_nodes = {name: graph.nodes[name] for name in non_cycle}
    non_cycle_order = _topological_sort(non_cycle_nodes)
    order.extend(non_cycle_order)

    # Add cycle components (need special handling)
    for cycle in graph.cycles:
        # Find component with least external dependencies
        min_deps = float("inf")
        start = None

        for component in cycle:
            external_deps = len(graph.nodes[component].depends_on - set(cycle))
            if external_deps < min_deps:
                min_deps = external_deps
                start = component

        # Add cycle components starting from weakest point
        cycle_order = [start]
        remaining = set(cycle) - {start}

        while remaining:
            # Find next component with most dependencies satisfied
            next_comp = None
            max_satisfied = -1

            for comp in remaining:
                satisfied = len(set(cycle_order) & graph.nodes[comp].depends_on)
                if satisfied > max_satisfied:
                    max_satisfied = satisfied
                    next_comp = comp

            if next_comp:
                cycle_order.append(next_comp)
                remaining.remove(next_comp)
            else:
                # Add remaining arbitrarily
                cycle_order.extend(remaining)
                break

        order.extend(cycle_order)

    return Success(order)
