"""Core Composition and Modularity Semantic Invariants.

Universal concepts of how smaller units combine into larger units.
These represent modules, interfaces, dependencies, and abstraction.
Pure data types following Scott Wlaschin's FDM principles.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime


# ============================================================================
# FUNDAMENTAL COMPOSITION CONCEPTS
# ============================================================================


@dataclass(frozen=True)
class Composition:
    """Combining smaller units into larger units.

    The fundamental principle of building complex systems.
    """

    parts: List["Component"]
    composition_type: "CompositionType"
    is_hierarchical: bool = True
    preserves_properties: List[str] = field(default_factory=list)


class CompositionType(str, Enum):
    """Ways to compose components."""

    SEQUENTIAL = "sequential"  # One after another
    PARALLEL = "parallel"  # Side by side
    NESTED = "nested"  # One inside another
    LAYERED = "layered"  # In layers/tiers
    PIPELINE = "pipeline"  # Data flow
    HIERARCHICAL = "hierarchical"  # Tree structure


@dataclass(frozen=True)
class Component:
    """A composable unit."""

    name: str
    interface: "Interface"
    implementation: Optional[Any] = None
    dependencies: List["Dependency"] = field(default_factory=list)
    is_atomic: bool = False  # Cannot be decomposed further


# ============================================================================
# MODULE CONCEPTS
# ============================================================================


@dataclass(frozen=True)
class Module:
    """A unit of organization and encapsulation.

    Universal concept of grouping related functionality.
    """

    name: str
    exports: List["Export"]
    imports: List["Import"]
    internal: List[Any]  # Internal/private elements
    is_sealed: bool = False  # Cannot be extended


@dataclass(frozen=True)
class Export:
    """Something provided by a module."""

    name: str
    exported_item: Any
    visibility: "Visibility"
    is_reexport: bool = False  # Re-exporting an import


@dataclass(frozen=True)
class Import:
    """Something required by a module."""

    module_path: str
    imported_items: List[str]
    alias: Optional[str] = None
    is_qualified: bool = False  # Requires module prefix


class Visibility(str, Enum):
    """Visibility levels."""

    PUBLIC = "public"  # Visible everywhere
    PROTECTED = "protected"  # Visible to subclasses
    INTERNAL = "internal"  # Visible within module/package
    PRIVATE = "private"  # Visible only locally


# ============================================================================
# INTERFACE CONCEPTS
# ============================================================================


@dataclass(frozen=True)
class Interface:
    """A contract/boundary between components.

    Defines what a component provides without how.
    """

    operations: List["Operation"]
    invariants: List["Invariant"]
    preconditions: List["Condition"]
    postconditions: List["Condition"]


@dataclass(frozen=True)
class Operation:
    """An operation provided by an interface."""

    name: str
    inputs: List["Parameter"]
    outputs: List["Parameter"]
    effects: List[str]  # Allowed effects
    is_required: bool = True  # vs optional


@dataclass(frozen=True)
class Parameter:
    """Parameter of an operation."""

    name: str
    parameter_type: Any  # Would be Type from types.py
    direction: str = "in"  # in, out, inout
    is_optional: bool = False


@dataclass(frozen=True)
class Invariant:
    """A property that must always hold."""

    property: str  # Property expression
    scope: str = "interface"  # Where it applies


@dataclass(frozen=True)
class Condition:
    """Pre or post condition."""

    expression: str
    must_hold: bool = True
    is_checked: bool = False  # Runtime checking


# ============================================================================
# DEPENDENCY CONCEPTS
# ============================================================================


@dataclass(frozen=True)
class Dependency:
    """A required capability."""

    required_interface: Interface
    is_optional: bool = False
    version_constraint: Optional["VersionConstraint"] = None
    injection_type: "InjectionType" = None


class InjectionType(str, Enum):
    """How dependencies are provided."""

    CONSTRUCTOR = "constructor"  # Constructor injection
    SETTER = "setter"  # Setter injection
    INTERFACE = "interface"  # Interface injection
    STATIC = "static"  # Static/compile-time
    DYNAMIC = "dynamic"  # Runtime lookup


@dataclass(frozen=True)
class VersionConstraint:
    """Version requirements."""

    minimum: Optional[str] = None
    maximum: Optional[str] = None
    exact: Optional[str] = None
    compatible_with: Optional[str] = None


@dataclass(frozen=True)
class DependencyGraph:
    """Graph of dependencies between components."""

    nodes: Dict[str, Component]
    edges: List["DependencyEdge"]
    has_cycles: bool = False


@dataclass(frozen=True)
class DependencyEdge:
    """A dependency relationship."""

    from_component: str
    to_component: str
    dependency_type: str
    is_runtime: bool = False


# ============================================================================
# ABSTRACTION CONCEPTS
# ============================================================================


@dataclass(frozen=True)
class Abstraction:
    """Hiding implementation details.

    Essential for managing complexity.
    """

    abstract_interface: Interface
    concrete_implementations: List[Component]
    abstraction_level: "AbstractionLevel"


class AbstractionLevel(str, Enum):
    """Levels of abstraction."""

    HARDWARE = "hardware"  # Physical level
    SYSTEM = "system"  # OS/runtime level
    LANGUAGE = "language"  # Programming language level
    FRAMEWORK = "framework"  # Framework/library level
    APPLICATION = "application"  # Application level
    DOMAIN = "domain"  # Business domain level


@dataclass(frozen=True)
class InformationHiding:
    """Hiding internal details."""

    public_interface: Interface
    hidden_implementation: Any
    encapsulation_boundary: str


@dataclass(frozen=True)
class AbstractDataType:
    """Type defined by operations, not representation."""

    type_name: str
    operations: List[Operation]
    axioms: List[str]  # Properties the operations satisfy
    is_algebraic: bool = True


# ============================================================================
# LAYERING AND ARCHITECTURE
# ============================================================================


@dataclass(frozen=True)
class Layer:
    """An architectural layer."""

    name: str
    level: int  # Higher levels depend on lower
    components: List[Component]
    provides: List[Interface]
    uses: List[Interface]


@dataclass(frozen=True)
class LayeredArchitecture:
    """Layered system architecture."""

    layers: List[Layer]
    is_strict: bool = True  # Can only use immediate lower layer
    allows_bypass: bool = False  # Can skip layers


@dataclass(frozen=True)
class Tier:
    """A deployment tier (physical separation)."""

    name: str
    components: List[Component]
    location: str  # Where deployed
    communication: str  # How it communicates


# ============================================================================
# COMPOSITION PATTERNS
# ============================================================================


@dataclass(frozen=True)
class CompositePattern:
    """Treat individual and composite objects uniformly."""

    component_interface: Interface
    leaf_components: List[Component]
    composite_components: List[Component]


@dataclass(frozen=True)
class DecoratorPattern:
    """Add functionality by wrapping."""

    base_component: Component
    decorators: List[Component]
    is_transparent: bool = True


@dataclass(frozen=True)
class AdapterPattern:
    """Make incompatible interfaces work together."""

    source_interface: Interface
    target_interface: Interface
    adapter: Component


@dataclass(frozen=True)
class FacadePattern:
    """Simplified interface to complex subsystem."""

    facade_interface: Interface
    subsystem_components: List[Component]


# ============================================================================
# PLUGIN AND EXTENSION
# ============================================================================


@dataclass(frozen=True)
class Plugin:
    """Dynamically loadable component."""

    plugin_interface: Interface
    metadata: Dict[str, Any]
    is_loaded: bool = False
    load_order: Optional[int] = None


@dataclass(frozen=True)
class ExtensionPoint:
    """Point where system can be extended."""

    name: str
    extension_interface: Interface
    cardinality: str = "many"  # one, many
    is_required: bool = False


@dataclass(frozen=True)
class ServiceRegistry:
    """Registry of available services."""

    services: Dict[str, Component]
    service_interface: Interface
    lookup_strategy: str = "name"  # name, type, predicate


# ============================================================================
# DOMAIN EVENTS (Colocated with Composition aggregate)
# ============================================================================


@dataclass(frozen=True)
class ComponentComposed:
    """Event: Components were composed."""

    composition: Composition
    timestamp: datetime


@dataclass(frozen=True)
class ModuleLoaded:
    """Event: Module was loaded."""

    module: Module
    load_time: float
    timestamp: datetime


@dataclass(frozen=True)
class DependencyResolved:
    """Event: Dependency was resolved."""

    dependency: Dependency
    resolved_to: Component
    timestamp: datetime


@dataclass(frozen=True)
class InterfaceImplemented:
    """Event: Interface was implemented."""

    interface: Interface
    implementation: Component
    timestamp: datetime


@dataclass(frozen=True)
class PluginLoaded:
    """Event: Plugin was loaded."""

    plugin: Plugin
    extension_point: ExtensionPoint
    timestamp: datetime


@dataclass(frozen=True)
class ServiceRegistered:
    """Event: Service registered in registry."""

    service: Component
    registry: ServiceRegistry
    timestamp: datetime
