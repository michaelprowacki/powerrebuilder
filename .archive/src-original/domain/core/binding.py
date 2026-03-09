"""Core Binding and Scope Semantic Invariants.

Universal concepts of naming, binding, and scope that exist across all languages.
These represent how names are associated with values and their visibility.
Pure data types following Scott Wlaschin's FDM principles.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime


# ============================================================================
# FUNDAMENTAL NAMING CONCEPTS
# ============================================================================


@dataclass(frozen=True)
class Name:
    """A name/identifier in a program.

    Universal concept of naming things.
    """

    identifier: str
    namespace: Optional["Namespace"] = None
    is_qualified: bool = False  # Fully qualified name


@dataclass(frozen=True)
class Binding:
    """Association between a name and what it refers to.

    The fundamental concept from lambda calculus.
    """

    name: Name
    target: "BindingTarget"
    scope: "Scope"
    is_mutable: bool = False
    binding_time: "BindingTime" = None


@dataclass(frozen=True)
class BindingTarget:
    """What a name can be bound to."""

    target_type: "BindingTargetType"
    value: Optional[Any] = None  # The actual value/reference
    location: Optional["Location"] = None  # Memory location


class BindingTargetType(str, Enum):
    """Types of things names can refer to."""

    VALUE = "value"  # Bound to a value (R-value)
    LOCATION = "location"  # Bound to a location (L-value)
    TYPE = "type"  # Bound to a type
    FUNCTION = "function"  # Bound to a function
    MODULE = "module"  # Bound to a module/namespace


class BindingTime(str, Enum):
    """When binding occurs."""

    COMPILE_TIME = "compile"  # Static binding
    LINK_TIME = "link"  # Linking phase
    LOAD_TIME = "load"  # Program load
    RUN_TIME = "runtime"  # Dynamic binding


# ============================================================================
# SCOPE CONCEPTS
# ============================================================================


@dataclass(frozen=True)
class Scope:
    """Region where bindings are valid.

    Universal concept of visibility and lifetime.
    """

    name: str
    scope_type: "ScopeType"
    parent: Optional["Scope"] = None  # Enclosing scope
    bindings: Dict[str, Binding] = field(default_factory=dict)
    is_closed: bool = False  # Can new bindings be added


class ScopeType(str, Enum):
    """Types of scopes."""

    GLOBAL = "global"  # Program-wide
    MODULE = "module"  # Module/file scope
    CLASS = "class"  # Class/object scope
    FUNCTION = "function"  # Function/method scope
    BLOCK = "block"  # Block scope (if, while, etc.)
    LOCAL = "local"  # Local scope


@dataclass(frozen=True)
class LexicalScope(Scope):
    """Lexical/static scoping - scope determined by program text.

    Most modern languages use lexical scoping.
    """

    definition_location: "SourceLocation"
    captures: List[Binding] = field(default_factory=list)  # Closed-over bindings


@dataclass(frozen=True)
class DynamicScope(Scope):
    """Dynamic scoping - scope determined by call stack.

    Less common (Lisp, Perl, some shell scripts).
    """

    call_stack: List["CallFrame"]


# ============================================================================
# ENVIRONMENT AND CONTEXT
# ============================================================================


@dataclass(frozen=True)
class Environment:
    """Collection of all bindings visible at a point.

    Maps names to their values/locations.
    """

    bindings: Dict[Name, BindingTarget]
    parent: Optional["Environment"] = None  # Outer environment
    is_global: bool = False


@dataclass(frozen=True)
class Context:
    """Execution context - environment plus control state.

    The complete context for evaluating expressions.
    """

    environment: Environment
    scope_chain: List[Scope]
    this_binding: Optional[BindingTarget] = None  # For OOP
    return_continuation: Optional[Any] = None  # Where to return to


@dataclass(frozen=True)
class CallFrame:
    """A frame in the call stack."""

    function_name: Name
    local_environment: Environment
    return_address: Any  # Where to return
    arguments: Dict[Name, Any]


# ============================================================================
# NAMESPACE CONCEPTS
# ============================================================================


@dataclass(frozen=True)
class Namespace:
    """Named collection of bindings.

    Prevents name collisions.
    """

    name: Name
    parent: Optional["Namespace"] = None
    members: Dict[str, Binding] = field(default_factory=dict)
    imports: List["Import"] = field(default_factory=list)
    exports: List["Export"] = field(default_factory=list)


@dataclass(frozen=True)
class Import:
    """Importing names from another namespace."""

    source_namespace: Namespace
    imported_names: List[Name]
    alias: Optional[Name] = None  # Import as different name
    is_wildcard: bool = False  # Import all


@dataclass(frozen=True)
class Export:
    """Exporting names from a namespace."""

    exported_name: Name
    internal_name: Name  # May be different from exported
    is_default: bool = False


# ============================================================================
# SPECIAL BINDING CONCEPTS
# ============================================================================


@dataclass(frozen=True)
class Location:
    """Memory location (L-value from Strachey).

    Where a value is stored.
    """

    address: Any  # Abstract address
    size: Optional[int] = None
    is_stack: bool = True  # Stack vs heap
    is_mutable: bool = True


@dataclass(frozen=True)
class Reference:
    """Reference/pointer to a location."""

    location: Location
    is_nullable: bool = False
    is_mutable: bool = True


@dataclass(frozen=True)
class Closure:
    """Function with captured environment.

    Bindings from enclosing scope.
    """

    function: Any  # Would be Function from computation.py
    captured_bindings: Dict[Name, BindingTarget]
    capturing_scope: Scope


@dataclass(frozen=True)
class ThisBinding:
    """The 'this'/'self' binding in OOP."""

    object_instance: Any
    class_scope: Scope
    is_bound: bool = True  # False for unbound methods


# ============================================================================
# SHADOWING AND RESOLUTION
# ============================================================================


@dataclass(frozen=True)
class Shadowing:
    """Name shadowing - inner binding hides outer."""

    inner_binding: Binding
    outer_binding: Binding
    is_intentional: bool = False


@dataclass(frozen=True)
class NameResolution:
    """Process of resolving a name to its binding."""

    name: Name
    search_path: List[Scope]  # Scopes searched in order
    resolved_binding: Optional[Binding] = None
    resolution_type: str = "lexical"  # lexical, dynamic


@dataclass(frozen=True)
class Qualification:
    """Fully qualified name."""

    namespace_path: List[Name]
    local_name: Name
    separator: str = "."  # . or :: or : etc.


# ============================================================================
# MUTABILITY AND ALIASING
# ============================================================================


@dataclass(frozen=True)
class MutableBinding:
    """Binding that can be changed."""

    binding: Binding
    can_rebind: bool = True  # Can point to different target
    can_mutate: bool = True  # Can mutate the target


@dataclass(frozen=True)
class Alias:
    """Multiple names for same location/value."""

    primary_binding: Binding
    alias_bindings: List[Binding]
    is_strong: bool = True  # Strong vs weak reference


@dataclass(frozen=True)
class ImmutableBinding:
    """Binding that cannot be changed."""

    binding: Binding
    is_deeply_immutable: bool = True  # Transitive immutability


# ============================================================================
# DOMAIN EVENTS (Colocated with Binding aggregate)
# ============================================================================


@dataclass(frozen=True)
class NameBound:
    """Event: Name was bound to a value/location."""

    binding: Binding
    scope: Scope
    timestamp: datetime


@dataclass(frozen=True)
class NameRebound:
    """Event: Mutable binding was changed."""

    binding: Binding
    old_target: BindingTarget
    new_target: BindingTarget
    timestamp: datetime


@dataclass(frozen=True)
class NameResolved:
    """Event: Name was resolved to its binding."""

    resolution: NameResolution
    success: bool
    timestamp: datetime


@dataclass(frozen=True)
class ScopeEntered:
    """Event: Execution entered a new scope."""

    scope: Scope
    context: Context
    timestamp: datetime


@dataclass(frozen=True)
class ScopeExited:
    """Event: Execution left a scope."""

    scope: Scope
    bindings_freed: List[Binding]
    timestamp: datetime


@dataclass(frozen=True)
class NameShadowed:
    """Event: Name shadowing occurred."""

    shadowing: Shadowing
    timestamp: datetime


# ============================================================================
# SOURCE LOCATION (for error reporting)
# ============================================================================


@dataclass(frozen=True)
class SourceLocation:
    """Location in source code."""

    file: str
    line: int
    column: int
    offset: Optional[int] = None
