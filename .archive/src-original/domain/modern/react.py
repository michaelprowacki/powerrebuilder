"""React/TypeScript Domain Types.

Pure data types representing React/TypeScript constructs.
These are the WHAT - no operations, just data models.
Following Scott Wlaschin's FDM principles.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum


# ============================================================================
# TYPESCRIPT LANGUAGE TYPES
# ============================================================================


class TypeScriptType(str, Enum):
    """TypeScript types."""

    NUMBER = "number"
    STRING = "string"
    BOOLEAN = "boolean"
    VOID = "void"
    NULL = "null"
    UNDEFINED = "undefined"
    ANY = "any"
    UNKNOWN = "unknown"
    NEVER = "never"
    OBJECT = "object"
    ARRAY = "Array"
    TUPLE = "Tuple"
    ENUM = "enum"
    UNION = "union"
    INTERSECTION = "intersection"
    LITERAL = "literal"


@dataclass(frozen=True)
class TypeScriptVariable:
    """A TypeScript variable."""

    name: str
    type: str
    is_const: bool = False
    is_let: bool = True
    is_readonly: bool = False
    is_optional: bool = False
    initial_value: Optional[Any] = None


@dataclass(frozen=True)
class TypeScriptParameter:
    """A function parameter."""

    name: str
    type: str
    is_optional: bool = False
    is_rest: bool = False  # ...args
    default_value: Optional[Any] = None


@dataclass(frozen=True)
class TypeScriptFunction:
    """A TypeScript function."""

    name: str
    parameters: List[TypeScriptParameter] = field(default_factory=list)
    return_type: str = "void"
    generics: List[str] = field(default_factory=list)
    is_async: bool = False
    is_arrow: bool = False
    body: str = ""


@dataclass(frozen=True)
class TypeScriptInterface:
    """A TypeScript interface."""

    name: str
    extends: List[str] = field(default_factory=list)
    properties: List["InterfaceProperty"] = field(default_factory=list)
    methods: List[TypeScriptFunction] = field(default_factory=list)
    generics: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class InterfaceProperty:
    """An interface property."""

    name: str
    type: str
    is_optional: bool = False
    is_readonly: bool = False


@dataclass(frozen=True)
class TypeScriptClass:
    """A TypeScript class."""

    name: str
    extends: Optional[str] = None
    implements: List[str] = field(default_factory=list)
    is_abstract: bool = False
    properties: List[TypeScriptVariable] = field(default_factory=list)
    methods: List[TypeScriptFunction] = field(default_factory=list)
    constructor: Optional[TypeScriptFunction] = None
    generics: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class TypeScriptEnum:
    """A TypeScript enum."""

    name: str
    members: Dict[str, Any] = field(default_factory=dict)
    is_const: bool = False


@dataclass(frozen=True)
class TypeScriptType:
    """A TypeScript type alias."""

    name: str
    definition: str
    generics: List[str] = field(default_factory=list)


# ============================================================================
# REACT COMPONENT TYPES
# ============================================================================


class ComponentType(str, Enum):
    """Types of React components."""

    FUNCTIONAL = "functional"
    CLASS = "class"
    MEMO = "memo"
    FORWARD_REF = "forwardRef"
    LAZY = "lazy"


@dataclass(frozen=True)
class ReactComponent:
    """A React component."""

    name: str
    type: ComponentType
    props: List[InterfaceProperty] = field(default_factory=list)
    state: Optional[List[InterfaceProperty]] = None  # For class components
    hooks: List["ReactHook"] = field(default_factory=list)
    children: Optional[str] = None


@dataclass(frozen=True)
class FunctionalComponent:
    """A functional React component."""

    name: str
    props_type: Optional[TypeScriptInterface] = None
    hooks: List["ReactHook"] = field(default_factory=list)
    jsx: str = ""
    is_memo: bool = False


@dataclass(frozen=True)
class ClassComponent:
    """A class-based React component."""

    name: str
    props_type: Optional[TypeScriptInterface] = None
    state_type: Optional[TypeScriptInterface] = None
    lifecycle_methods: Dict[str, str] = field(default_factory=dict)
    methods: List[TypeScriptFunction] = field(default_factory=list)
    render_method: str = ""


# ============================================================================
# REACT HOOKS
# ============================================================================


class HookType(str, Enum):
    """Types of React hooks."""

    STATE = "useState"
    EFFECT = "useEffect"
    CONTEXT = "useContext"
    REDUCER = "useReducer"
    CALLBACK = "useCallback"
    MEMO = "useMemo"
    REF = "useRef"
    IMPERATIVE_HANDLE = "useImperativeHandle"
    LAYOUT_EFFECT = "useLayoutEffect"
    DEBUG_VALUE = "useDebugValue"
    CUSTOM = "custom"


@dataclass(frozen=True)
class ReactHook:
    """A React hook usage."""

    type: HookType
    name: Optional[str] = None  # For custom hooks
    dependencies: List[str] = field(default_factory=list)
    initial_value: Optional[Any] = None


@dataclass(frozen=True)
class UseStateHook:
    """useState hook."""

    state_name: str
    setter_name: str
    type: str
    initial_value: Any


@dataclass(frozen=True)
class UseEffectHook:
    """useEffect hook."""

    effect_body: str
    dependencies: List[str]
    cleanup: Optional[str] = None


@dataclass(frozen=True)
class UseContextHook:
    """useContext hook."""

    context_name: str
    value_name: str
    type: str


@dataclass(frozen=True)
class CustomHook:
    """A custom React hook."""

    name: str
    parameters: List[TypeScriptParameter] = field(default_factory=list)
    return_type: str
    body: str
    hooks_used: List[ReactHook] = field(default_factory=list)


# ============================================================================
# JSX ELEMENTS
# ============================================================================


@dataclass(frozen=True)
class JSXElement:
    """A JSX element."""

    tag: str
    props: Dict[str, Any] = field(default_factory=dict)
    children: List["JSXChild"] = field(default_factory=list)
    is_self_closing: bool = False


@dataclass(frozen=True)
class JSXChild:
    """A child of a JSX element."""

    type: str  # element, text, expression, fragment
    value: Any


@dataclass(frozen=True)
class JSXProps:
    """JSX element props."""

    attributes: Dict[str, Any] = field(default_factory=dict)
    event_handlers: Dict[str, str] = field(default_factory=dict)
    ref: Optional[str] = None
    key: Optional[str] = None
    style: Optional[Dict[str, Any]] = None
    className: Optional[str] = None


# ============================================================================
# STATE MANAGEMENT
# ============================================================================


@dataclass(frozen=True)
class ReduxStore:
    """Redux store configuration."""

    name: str
    initial_state: Dict[str, Any]
    reducers: List["ReduxReducer"]
    middleware: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class ReduxReducer:
    """A Redux reducer."""

    name: str
    initial_state: Any
    actions: Dict[str, str]  # action_type -> handler


@dataclass(frozen=True)
class ReduxAction:
    """A Redux action."""

    type: str
    payload: Optional[Any] = None
    meta: Optional[Dict[str, Any]] = None


@dataclass(frozen=True)
class ContextProvider:
    """React Context provider."""

    name: str
    value_type: str
    default_value: Any
    provider_component: str
    consumer_hook: str


@dataclass(frozen=True)
class ZustandStore:
    """Zustand state store."""

    name: str
    state: Dict[str, Any]
    actions: Dict[str, str]
    selectors: Dict[str, str] = field(default_factory=dict)


# ============================================================================
# ROUTING
# ============================================================================


@dataclass(frozen=True)
class ReactRoute:
    """A React Router route."""

    path: str
    component: str
    exact: bool = False
    props: Dict[str, Any] = field(default_factory=dict)
    children: List["ReactRoute"] = field(default_factory=list)
    guards: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class RouterConfig:
    """Router configuration."""

    type: str  # BrowserRouter, HashRouter, MemoryRouter
    basename: Optional[str] = None
    routes: List[ReactRoute] = field(default_factory=list)


# ============================================================================
# STYLING
# ============================================================================


@dataclass(frozen=True)
class StyledComponent:
    """A styled-component."""

    name: str
    base_element: str
    styles: str
    props_type: Optional[TypeScriptInterface] = None


@dataclass(frozen=True)
class CSSModule:
    """CSS Module."""

    name: str
    classes: Dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class EmotionStyle:
    """Emotion CSS-in-JS style."""

    name: str
    css: str
    is_global: bool = False


# ============================================================================
# PROJECT STRUCTURE
# ============================================================================


@dataclass(frozen=True)
class ReactProject:
    """React project structure."""

    name: str
    components: List[ReactComponent] = field(default_factory=list)
    pages: List[ReactComponent] = field(default_factory=list)
    hooks: List[CustomHook] = field(default_factory=list)
    contexts: List[ContextProvider] = field(default_factory=list)
    services: List[TypeScriptClass] = field(default_factory=list)
    types: List[TypeScriptInterface] = field(default_factory=list)
    router_config: Optional[RouterConfig] = None
    package_json: Dict[str, Any] = field(default_factory=dict)
    tsconfig: Dict[str, Any] = field(default_factory=dict)
