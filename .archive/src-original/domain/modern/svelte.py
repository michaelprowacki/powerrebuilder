"""Svelte/SvelteKit Domain Types.

Pure data types representing Svelte constructs.
These are the WHAT - no operations, just data models.
Events are colocated with their aggregates following Scott Wlaschin's FDM principles.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime


# ============================================================================
# SVELTE COMPONENT TYPES
# ============================================================================


@dataclass(frozen=True)
class SvelteComponent:
    """A Svelte component."""

    name: str
    props: List["SvelteProp"] = field(default_factory=list)
    state: List["SvelteState"] = field(default_factory=list)
    stores: List["SvelteStore"] = field(default_factory=list)
    slots: List["SvelteSlot"] = field(default_factory=list)
    events: List["SvelteEvent"] = field(default_factory=list)
    script: str = ""
    template: str = ""
    style: Optional[str] = None
    is_module: bool = False  # <script context="module">


@dataclass(frozen=True)
class SvelteProp:
    """A component prop."""

    name: str
    type: Optional[str] = None
    default: Optional[Any] = None
    is_required: bool = False
    is_readonly: bool = False


@dataclass(frozen=True)
class SvelteState:
    """Component state variable."""

    name: str
    initial_value: Any
    type: Optional[str] = None
    is_reactive: bool = False  # $: reactive statement


@dataclass(frozen=True)
class SvelteStore:
    """A Svelte store reference."""

    name: str
    store_type: str  # writable, readable, derived, custom
    initial_value: Optional[Any] = None
    is_subscribed: bool = False  # Using $ prefix


@dataclass(frozen=True)
class SvelteSlot:
    """A component slot."""

    name: Optional[str] = None  # None for default slot
    props: Dict[str, Any] = field(default_factory=dict)
    fallback: Optional[str] = None


@dataclass(frozen=True)
class SvelteEvent:
    """A component event."""

    name: str
    handler: Optional[str] = None
    modifiers: List[str] = field(
        default_factory=list
    )  # preventDefault, stopPropagation
    is_forwarded: bool = False


# ============================================================================
# SVELTE REACTIVITY
# ============================================================================


@dataclass(frozen=True)
class ReactiveStatement:
    """A reactive statement ($:)."""

    dependencies: List[str]
    expression: str
    is_assignment: bool = False


@dataclass(frozen=True)
class ReactiveBlock:
    """A reactive block."""

    dependencies: List[str]
    statements: List[str]


# ============================================================================
# SVELTE DIRECTIVES
# ============================================================================


@dataclass(frozen=True)
class SvelteDirective:
    """A Svelte directive."""

    type: str  # bind, on, use, transition, animate, class, style
    target: str
    value: Any
    modifiers: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class SvelteBinding:
    """Two-way binding."""

    property: str
    variable: str
    is_group: bool = False  # bind:group for radio/checkbox


@dataclass(frozen=True)
class SvelteTransition:
    """A transition directive."""

    name: str  # fade, fly, slide, scale, draw, crossfade
    direction: str  # in, out, both
    parameters: Dict[str, Any] = field(default_factory=dict)
    is_local: bool = False


@dataclass(frozen=True)
class SvelteAction:
    """A use: action."""

    name: str
    parameters: Optional[Any] = None
    update_function: Optional[str] = None
    destroy_function: Optional[str] = None


# ============================================================================
# SVELTE STORES
# ============================================================================


@dataclass(frozen=True)
class WritableStore:
    """A writable store."""

    name: str
    initial_value: Any
    subscribers: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class ReadableStore:
    """A readable store."""

    name: str
    initial_value: Any
    start_function: str  # Start/stop notifications


@dataclass(frozen=True)
class DerivedStore:
    """A derived store."""

    name: str
    dependencies: List[str]
    derivation_function: str


@dataclass(frozen=True)
class CustomStore:
    """A custom store."""

    name: str
    subscribe_method: str
    set_method: Optional[str] = None
    update_method: Optional[str] = None


# ============================================================================
# SVELTEKIT TYPES
# ============================================================================


@dataclass(frozen=True)
class SvelteKitRoute:
    """A SvelteKit route."""

    path: str
    page_component: Optional[str] = None
    layout_component: Optional[str] = None
    error_component: Optional[str] = None
    load_function: Optional["SvelteKitLoad"] = None
    actions: Dict[str, "SvelteKitAction"] = field(default_factory=dict)
    params: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class SvelteKitLoad:
    """A +page.server.js load function."""

    is_server: bool = True
    depends: List[str] = field(default_factory=list)
    returns_data: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SvelteKitAction:
    """A form action."""

    name: Optional[str] = None  # None for default action
    is_async: bool = True
    validates_data: bool = True
    returns_redirect: Optional[str] = None


@dataclass(frozen=True)
class SvelteKitLayout:
    """A layout component."""

    path: str
    component: SvelteComponent
    load_function: Optional[SvelteKitLoad] = None
    applies_to: List[str] = field(default_factory=list)  # Child routes


@dataclass(frozen=True)
class SvelteKitHook:
    """A SvelteKit hook."""

    type: str  # handle, handleError, handleFetch
    file: str  # hooks.server.js or hooks.client.js
    function: str


# ============================================================================
# SVELTE BLOCKS
# ============================================================================


@dataclass(frozen=True)
class IfBlock:
    """An {#if} block."""

    condition: str
    then_content: str
    else_if_blocks: List[tuple[str, str]] = field(default_factory=list)
    else_content: Optional[str] = None


@dataclass(frozen=True)
class EachBlock:
    """An {#each} block."""

    expression: str
    as_pattern: str  # item, index
    key: Optional[str] = None
    content: str
    else_content: Optional[str] = None  # Empty state


@dataclass(frozen=True)
class AwaitBlock:
    """An {#await} block."""

    promise: str
    pending_content: Optional[str] = None
    then_pattern: Optional[str] = None
    then_content: Optional[str] = None
    catch_pattern: Optional[str] = None
    catch_content: Optional[str] = None


@dataclass(frozen=True)
class KeyBlock:
    """A {#key} block."""

    expression: str
    content: str


# ============================================================================
# DOMAIN EVENTS (Colocated with Svelte aggregate)
# ============================================================================


@dataclass(frozen=True)
class ComponentMounted:
    """Event: Svelte component mounted."""

    component: SvelteComponent
    props: Dict[str, Any]
    timestamp: datetime


@dataclass(frozen=True)
class ComponentUpdated:
    """Event: Component updated due to prop/state change."""

    component: SvelteComponent
    changed_props: List[str]
    changed_state: List[str]
    timestamp: datetime


@dataclass(frozen=True)
class ComponentDestroyed:
    """Event: Component destroyed."""

    component: SvelteComponent
    cleanup_performed: bool
    timestamp: datetime


@dataclass(frozen=True)
class StoreUpdated:
    """Event: Store value updated."""

    store_name: str
    old_value: Any
    new_value: Any
    subscriber_count: int
    timestamp: datetime


@dataclass(frozen=True)
class RouteNavigated:
    """Event: SvelteKit route navigation."""

    from_route: Optional[str]
    to_route: str
    params: Dict[str, str]
    is_client_navigation: bool
    timestamp: datetime


@dataclass(frozen=True)
class FormSubmitted:
    """Event: SvelteKit form action submitted."""

    action: SvelteKitAction
    form_data: Dict[str, Any]
    success: bool
    error: Optional[str]
    timestamp: datetime


@dataclass(frozen=True)
class TransitionStarted:
    """Event: Transition animation started."""

    element: str
    transition: SvelteTransition
    duration_ms: float
    timestamp: datetime
