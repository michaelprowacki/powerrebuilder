"""Vue 3 Domain Types.

Pure data types representing Vue 3 constructs.
These are the WHAT - no operations, just data models.
Events are colocated with their aggregates following Scott Wlaschin's FDM principles.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Union
from enum import Enum
from datetime import datetime


# ============================================================================
# VUE COMPONENT TYPES
# ============================================================================


@dataclass(frozen=True)
class VueComponent:
    """A Vue 3 component."""

    name: str
    props: List["VueProp"] = field(default_factory=list)
    emits: List["VueEmit"] = field(default_factory=list)
    setup_return: Dict[str, Any] = field(default_factory=dict)
    template: str = ""
    style: Optional["VueStyle"] = None
    is_script_setup: bool = False
    is_async: bool = False


@dataclass(frozen=True)
class VueProp:
    """A component prop."""

    name: str
    type: Union[str, List[str]]  # String, Number, Boolean, Array, Object, etc.
    default: Optional[Any] = None
    required: bool = False
    validator: Optional[str] = None


@dataclass(frozen=True)
class VueEmit:
    """An event emission."""

    name: str
    payload_type: Optional[str] = None
    validation: Optional[str] = None


@dataclass(frozen=True)
class VueStyle:
    """Component styles."""

    content: str
    scoped: bool = False
    module: bool = False
    lang: str = "css"  # css, scss, sass, less, stylus


# ============================================================================
# COMPOSITION API
# ============================================================================


@dataclass(frozen=True)
class CompositionRef:
    """A ref() reactive reference."""

    name: str
    initial_value: Any
    type: Optional[str] = None


@dataclass(frozen=True)
class CompositionReactive:
    """A reactive() object."""

    name: str
    properties: Dict[str, Any]
    type: Optional[str] = None


@dataclass(frozen=True)
class CompositionComputed:
    """A computed property."""

    name: str
    getter: str
    setter: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class CompositionWatch:
    """A watcher."""

    source: Union[str, List[str]]
    callback: str
    options: Dict[str, Any] = field(default_factory=dict)  # immediate, deep, flush


@dataclass(frozen=True)
class CompositionProvide:
    """Provide/inject pattern."""

    key: str
    value: Any
    is_readonly: bool = False


@dataclass(frozen=True)
class CompositionInject:
    """Inject a provided value."""

    key: str
    default_value: Optional[Any] = None
    treat_as_ref: bool = True


# ============================================================================
# LIFECYCLE HOOKS
# ============================================================================


@dataclass(frozen=True)
class LifecycleHook:
    """A lifecycle hook."""

    type: str  # onMounted, onUpdated, onUnmounted, etc.
    callback: str
    cleanup: Optional[str] = None


class LifecycleType(str, Enum):
    """Vue 3 lifecycle hooks."""

    BEFORE_CREATE = "onBeforeCreate"  # Options API only
    CREATED = "onCreated"  # Options API only
    BEFORE_MOUNT = "onBeforeMount"
    MOUNTED = "onMounted"
    BEFORE_UPDATE = "onBeforeUpdate"
    UPDATED = "onUpdated"
    BEFORE_UNMOUNT = "onBeforeUnmount"
    UNMOUNTED = "onUnmounted"
    ERROR_CAPTURED = "onErrorCaptured"
    RENDER_TRACKED = "onRenderTracked"
    RENDER_TRIGGERED = "onRenderTriggered"
    ACTIVATED = "onActivated"  # keep-alive
    DEACTIVATED = "onDeactivated"  # keep-alive
    SERVER_PREFETCH = "onServerPrefetch"  # SSR


# ============================================================================
# DIRECTIVES
# ============================================================================


@dataclass(frozen=True)
class VueDirective:
    """A Vue directive."""

    name: str  # v-if, v-for, v-model, custom
    value: Any
    arg: Optional[str] = None
    modifiers: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class CustomDirective:
    """A custom directive definition."""

    name: str
    created: Optional[str] = None
    before_mount: Optional[str] = None
    mounted: Optional[str] = None
    before_update: Optional[str] = None
    updated: Optional[str] = None
    before_unmount: Optional[str] = None
    unmounted: Optional[str] = None


# ============================================================================
# COMPOSABLES (CUSTOM HOOKS)
# ============================================================================


@dataclass(frozen=True)
class Composable:
    """A composable function."""

    name: str
    parameters: List[tuple[str, str]] = field(default_factory=list)
    returns: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)  # Other composables
    body: str = ""


# ============================================================================
# VUE ROUTER
# ============================================================================


@dataclass(frozen=True)
class VueRoute:
    """A Vue Router route."""

    path: str
    name: Optional[str] = None
    component: str
    props: Union[bool, Dict[str, Any]] = False
    meta: Dict[str, Any] = field(default_factory=dict)
    children: List["VueRoute"] = field(default_factory=list)
    redirect: Optional[str] = None
    alias: Optional[Union[str, List[str]]] = None
    before_enter: Optional[str] = None


@dataclass(frozen=True)
class VueRouter:
    """Router configuration."""

    routes: List[VueRoute]
    mode: str = "history"  # history, hash, abstract
    base: str = "/"
    scroll_behavior: Optional[str] = None


@dataclass(frozen=True)
class NavigationGuard:
    """A navigation guard."""

    type: str  # beforeEach, afterEach, beforeResolve
    handler: str
    is_global: bool = True


# ============================================================================
# PINIA STORE (VUEX SUCCESSOR)
# ============================================================================


@dataclass(frozen=True)
class PiniaStore:
    """A Pinia store."""

    id: str
    state: Dict[str, Any] = field(default_factory=dict)
    getters: Dict[str, str] = field(default_factory=dict)
    actions: Dict[str, str] = field(default_factory=dict)
    persist: Optional[Dict[str, Any]] = None  # Persistence options


@dataclass(frozen=True)
class PiniaGetter:
    """A store getter."""

    name: str
    dependencies: List[str]
    compute_function: str


@dataclass(frozen=True)
class PiniaAction:
    """A store action."""

    name: str
    is_async: bool = False
    parameters: List[tuple[str, str]] = field(default_factory=list)
    body: str = ""


# ============================================================================
# TEMPLATE SYNTAX
# ============================================================================


@dataclass(frozen=True)
class VueTemplate:
    """Vue template structure."""

    root_element: Optional["VueElement"] = None
    fragments: List["VueElement"] = field(
        default_factory=list
    )  # Vue 3 supports fragments


@dataclass(frozen=True)
class VueElement:
    """A template element."""

    tag: str
    attributes: Dict[str, Any] = field(default_factory=dict)
    directives: List[VueDirective] = field(default_factory=list)
    children: List[Union["VueElement", str]] = field(default_factory=list)
    slot: Optional[str] = None
    key: Optional[str] = None


@dataclass(frozen=True)
class VueSlot:
    """A slot definition."""

    name: Optional[str] = None  # None for default slot
    scope: Dict[str, Any] = field(default_factory=dict)
    fallback: Optional[str] = None


# ============================================================================
# TELEPORT AND SUSPENSE
# ============================================================================


@dataclass(frozen=True)
class VueTeleport:
    """Teleport component."""

    to: str  # CSS selector or element
    disabled: bool = False
    content: VueElement


@dataclass(frozen=True)
class VueSuspense:
    """Suspense component."""

    default_content: VueElement
    fallback_content: Optional[VueElement] = None
    timeout: Optional[int] = None


# ============================================================================
# DOMAIN EVENTS (Colocated with Vue aggregate)
# ============================================================================


@dataclass(frozen=True)
class VueComponentCreated:
    """Event: Vue component instance created."""

    component: VueComponent
    props: Dict[str, Any]
    timestamp: datetime


@dataclass(frozen=True)
class VueComponentMounted:
    """Event: Component mounted to DOM."""

    component: VueComponent
    mount_point: str
    timestamp: datetime


@dataclass(frozen=True)
class VueComponentUpdated:
    """Event: Component re-rendered."""

    component: VueComponent
    trigger: str  # prop change, state change, etc.
    patches: int  # Number of DOM patches
    timestamp: datetime


@dataclass(frozen=True)
class VueComponentUnmounted:
    """Event: Component unmounted."""

    component: VueComponent
    cleanup_performed: bool
    timestamp: datetime


@dataclass(frozen=True)
class ReactiveValueChanged:
    """Event: Reactive value changed."""

    source: str  # ref name or reactive property path
    old_value: Any
    new_value: Any
    watchers_triggered: List[str]
    timestamp: datetime


@dataclass(frozen=True)
class StoreActionDispatched:
    """Event: Pinia store action dispatched."""

    store_id: str
    action_name: str
    payload: Any
    state_before: Dict[str, Any]
    state_after: Dict[str, Any]
    timestamp: datetime


@dataclass(frozen=True)
class RouteChanged:
    """Event: Vue Router navigation."""

    from_route: Optional[str]
    to_route: str
    params: Dict[str, str]
    query: Dict[str, str]
    navigation_type: str  # push, replace, back, forward
    timestamp: datetime
