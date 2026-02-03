"""Model Domain - Symbol Resolution.

Pure functions for resolving symbols and building dependency graphs.
Events track the resolution process for observability.
"""

from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional, Set, Union
from enum import Enum


# ============================================================================
# SYMBOL TYPES
# ============================================================================


class SymbolType(str, Enum):
    """Types of symbols in PowerBuilder."""

    CLASS = "class"
    FUNCTION = "function"
    METHOD = "method"
    PROPERTY = "property"
    VARIABLE = "variable"
    CONSTANT = "constant"
    EVENT = "event"
    DATAWINDOW = "datawindow"


class ResolutionScope(str, Enum):
    """Scope of symbol resolution."""

    LOCAL = "local"  # Within same function/method
    CLASS = "class"  # Within same class
    MODULE = "module"  # Within same file/module
    GLOBAL = "global"  # Across entire application
    IMPORTED = "imported"  # From imported module


@dataclass(frozen=True)
class Symbol:
    """Resolved symbol information."""

    name: str
    type: SymbolType
    scope: ResolutionScope
    defined_in: str  # File/module where defined
    line_number: Optional[int] = None
    signature: Optional[str] = None  # For functions/methods


@dataclass(frozen=True)
class SymbolReference:
    """Reference to a symbol in code."""

    name: str
    location: str  # File/module containing reference
    line_number: int
    context: str  # e.g., "method_call", "variable_access"


@dataclass(frozen=True)
class SymbolTable:
    """Collection of resolved symbols."""

    symbols: Dict[str, Symbol]
    references: Dict[str, List[SymbolReference]]
    unresolved: List[SymbolReference]


@dataclass(frozen=True)
class DependencyGraph:
    """Graph of module dependencies."""

    nodes: Set[str]  # Module names
    edges: Dict[str, Set[str]]  # module -> dependencies
    cycles: List[List[str]]  # Detected circular dependencies


# ============================================================================
# SYMBOL RESOLUTION EVENTS
# ============================================================================


@dataclass(frozen=True)
class SymbolResolved:
    """Event emitted when a symbol is successfully resolved."""

    symbol_name: str
    resolved_to: str  # Full path to definition
    resolution_scope: ResolutionScope
    confidence: float  # 0.0 to 1.0


@dataclass(frozen=True)
class UnresolvedReference:
    """Event emitted when a reference cannot be resolved."""

    reference: str
    from_location: str
    line_number: int
    possible_matches: List[str]


@dataclass(frozen=True)
class CircularDependency:
    """Event emitted when circular dependency is detected."""

    cycle: List[str]
    severity: str  # "low", "medium", "high"


@dataclass(frozen=True)
class DependencyFound:
    """Event emitted when a dependency is discovered."""

    from_module: str
    to_module: str
    dependency_type: str  # "import", "inheritance", "reference"


@dataclass(frozen=True)
class SymbolTableBuilt:
    """Event emitted when symbol table is completed."""

    total_symbols: int
    resolved_references: int
    unresolved_references: int
    resolution_rate: float


# Union type for all symbol events
SymbolEvent = Union[
    SymbolResolved,
    UnresolvedReference,
    CircularDependency,
    DependencyFound,
    SymbolTableBuilt,
]


# ============================================================================
# SYMBOL RESOLUTION FUNCTIONS
# ============================================================================


def resolve_symbols(
    references: List[SymbolReference], known_symbols: Dict[str, Symbol]
) -> Tuple[SymbolTable, List[SymbolEvent]]:
    """Resolve symbol references against known symbols.

    Pure function: (references, symbols) -> (symbol_table, events)
    """
    events = []
    resolved_refs = {}
    unresolved = []

    for ref in references:
        # Try to resolve the reference
        symbol = lookup_symbol(ref.name, known_symbols, ref.location)

        if symbol:
            # Track resolved reference
            if symbol.name not in resolved_refs:
                resolved_refs[symbol.name] = []
            resolved_refs[symbol.name].append(ref)

            # Emit resolution event
            events.append(
                SymbolResolved(
                    symbol_name=ref.name,
                    resolved_to=f"{symbol.defined_in}:{symbol.name}",
                    resolution_scope=symbol.scope,
                    confidence=calculate_confidence(ref, symbol),
                )
            )
        else:
            # Track unresolved reference
            unresolved.append(ref)

            # Find possible matches
            matches = find_similar_symbols(ref.name, known_symbols)

            # Emit unresolved event
            events.append(
                UnresolvedReference(
                    reference=ref.name,
                    from_location=ref.location,
                    line_number=ref.line_number,
                    possible_matches=matches[:3],  # Top 3 suggestions
                )
            )

    # Build symbol table
    table = SymbolTable(
        symbols=known_symbols, references=resolved_refs, unresolved=unresolved
    )

    # Emit summary event
    total_refs = len(references)
    resolved_count = total_refs - len(unresolved)
    events.append(
        SymbolTableBuilt(
            total_symbols=len(known_symbols),
            resolved_references=resolved_count,
            unresolved_references=len(unresolved),
            resolution_rate=resolved_count / total_refs if total_refs > 0 else 0.0,
        )
    )

    return table, events


def build_dependency_graph(
    modules: Dict[str, List[str]],  # module -> imports
) -> Tuple[DependencyGraph, List[SymbolEvent]]:
    """Build dependency graph from module imports.

    Pure function: module_imports -> (graph, events)
    """
    events = []
    nodes = set(modules.keys())
    edges = {}

    for module, imports in modules.items():
        edges[module] = set()

        for imported in imports:
            # Add edge
            edges[module].add(imported)

            # Add imported as node if not present
            nodes.add(imported)

            # Emit dependency event
            events.append(
                DependencyFound(
                    from_module=module, to_module=imported, dependency_type="import"
                )
            )

    # Detect circular dependencies
    cycles = detect_cycles(edges)

    for cycle in cycles:
        # Emit circular dependency event
        severity = "high" if len(cycle) > 3 else "medium"
        events.append(CircularDependency(cycle=cycle, severity=severity))

    return DependencyGraph(nodes=nodes, edges=edges, cycles=cycles), events


def detect_cycles(edges: Dict[str, Set[str]]) -> List[List[str]]:
    """Detect circular dependencies in graph.

    Pure function using DFS to find cycles.
    """
    cycles = []
    visited = set()
    rec_stack = []

    def visit(node: str, path: List[str]) -> None:
        if node in path:
            # Found a cycle
            cycle_start = path.index(node)
            cycle = path[cycle_start:] + [node]
            cycles.append(cycle)
            return

        if node in visited:
            return

        visited.add(node)
        path.append(node)

        for neighbor in edges.get(node, set()):
            visit(neighbor, path.copy())

    for node in edges:
        if node not in visited:
            visit(node, [])

    return cycles


def lookup_symbol(
    name: str, symbols: Dict[str, Symbol], context: str
) -> Optional[Symbol]:
    """Look up a symbol by name, considering context.

    Pure function for symbol lookup.
    """
    # Direct lookup
    if name in symbols:
        return symbols[name]

    # Try with context prefix (e.g., class.method)
    qualified_name = f"{context}.{name}"
    if qualified_name in symbols:
        return symbols[qualified_name]

    # Try parent context
    if "." in context:
        parent_context = context.rsplit(".", 1)[0]
        return lookup_symbol(name, symbols, parent_context)

    return None


def calculate_confidence(ref: SymbolReference, symbol: Symbol) -> float:
    """Calculate confidence score for symbol resolution.

    Pure function returning 0.0 to 1.0.
    """
    confidence = 0.5  # Base confidence

    # Exact name match
    if ref.name == symbol.name:
        confidence += 0.3

    # Same file/module
    if ref.location == symbol.defined_in:
        confidence += 0.2
    # Same scope
    elif symbol.scope in [ResolutionScope.GLOBAL, ResolutionScope.IMPORTED]:
        confidence += 0.1

    return min(confidence, 1.0)


def find_similar_symbols(name: str, symbols: Dict[str, Symbol]) -> List[str]:
    """Find symbols with similar names.

    Pure function for suggestions.
    """
    similar = []
    name_lower = name.lower()

    for symbol_name in symbols:
        # Case-insensitive match
        if symbol_name.lower() == name_lower:
            similar.append(symbol_name)
        # Prefix match
        elif symbol_name.lower().startswith(name_lower):
            similar.append(symbol_name)
        # Suffix match
        elif symbol_name.lower().endswith(name_lower):
            similar.append(symbol_name)
        # Contains
        elif name_lower in symbol_name.lower():
            similar.append(symbol_name)

    # Sort by similarity (simple length difference)
    similar.sort(key=lambda s: abs(len(s) - len(name)))

    return similar[:10]  # Return top 10
