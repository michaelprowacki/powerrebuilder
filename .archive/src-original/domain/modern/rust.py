"""Rust/Dioxus/Tauri Domain Types.

Pure data types representing Rust constructs and frameworks.
These are the WHAT - no operations, just data models.
Events are colocated with their aggregates following Scott Wlaschin's FDM principles.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime


# ============================================================================
# RUST LANGUAGE TYPES
# ============================================================================


class RustType(str, Enum):
    """Rust data types."""

    # Primitive types
    I8 = "i8"
    I16 = "i16"
    I32 = "i32"
    I64 = "i64"
    I128 = "i128"
    ISIZE = "isize"
    U8 = "u8"
    U16 = "u16"
    U32 = "u32"
    U64 = "u64"
    U128 = "u128"
    USIZE = "usize"
    F32 = "f32"
    F64 = "f64"
    BOOL = "bool"
    CHAR = "char"
    STR = "str"
    STRING = "String"

    # Compound types
    VEC = "Vec"
    ARRAY = "Array"
    TUPLE = "Tuple"
    OPTION = "Option"
    RESULT = "Result"
    HASHMAP = "HashMap"
    HASHSET = "HashSet"
    BOX = "Box"
    RC = "Rc"
    ARC = "Arc"
    REFCELL = "RefCell"
    MUTEX = "Mutex"


@dataclass(frozen=True)
class RustVariable:
    """A Rust variable."""

    name: str
    rust_type: str
    is_mutable: bool = False
    is_static: bool = False
    is_const: bool = False
    visibility: str = "private"  # pub, pub(crate), pub(super), private
    lifetime: Optional[str] = None
    initial_value: Optional[Any] = None


@dataclass(frozen=True)
class RustFunction:
    """A Rust function."""

    name: str
    parameters: List["RustParameter"] = field(default_factory=list)
    return_type: Optional[str] = None
    generics: List["RustGeneric"] = field(default_factory=list)
    where_clause: Optional[str] = None
    is_async: bool = False
    is_unsafe: bool = False
    is_const: bool = False
    visibility: str = "private"
    body: str = ""


@dataclass(frozen=True)
class RustParameter:
    """A function parameter."""

    name: str
    rust_type: str
    is_mutable: bool = False
    is_reference: bool = False
    lifetime: Optional[str] = None
    default: Optional[Any] = None


@dataclass(frozen=True)
class RustGeneric:
    """A generic type parameter."""

    name: str
    bounds: List[str] = field(default_factory=list)
    default: Optional[str] = None


@dataclass(frozen=True)
class RustStruct:
    """A Rust struct."""

    name: str
    fields: List["RustField"] = field(default_factory=list)
    generics: List[RustGeneric] = field(default_factory=list)
    derives: List[str] = field(default_factory=list)  # Debug, Clone, etc.
    visibility: str = "private"
    is_tuple: bool = False


@dataclass(frozen=True)
class RustField:
    """A struct field."""

    name: str
    rust_type: str
    visibility: str = "private"
    default: Optional[Any] = None
    attributes: List[str] = field(default_factory=list)  # serde attributes etc.


@dataclass(frozen=True)
class RustEnum:
    """A Rust enum."""

    name: str
    variants: List["RustVariant"] = field(default_factory=list)
    generics: List[RustGeneric] = field(default_factory=list)
    derives: List[str] = field(default_factory=list)
    visibility: str = "private"


@dataclass(frozen=True)
class RustVariant:
    """An enum variant."""

    name: str
    data: Optional[Any] = None  # Unit, Tuple, or Struct variant
    discriminant: Optional[int] = None


@dataclass(frozen=True)
class RustTrait:
    """A Rust trait."""

    name: str
    methods: List[RustFunction] = field(default_factory=list)
    associated_types: List[str] = field(default_factory=list)
    supertraits: List[str] = field(default_factory=list)
    generics: List[RustGeneric] = field(default_factory=list)
    visibility: str = "public"


@dataclass(frozen=True)
class RustImpl:
    """A trait implementation."""

    struct_name: str
    trait_name: Optional[str] = None  # None for inherent impl
    methods: List[RustFunction] = field(default_factory=list)
    generics: List[RustGeneric] = field(default_factory=list)
    where_clause: Optional[str] = None


# ============================================================================
# DIOXUS FRAMEWORK TYPES
# ============================================================================


@dataclass(frozen=True)
class DioxusComponent:
    """A Dioxus component."""

    name: str
    props: Optional["DioxusProps"] = None
    hooks: List["DioxusHook"] = field(default_factory=list)
    rsx: str = ""  # The RSX template
    is_async: bool = False


@dataclass(frozen=True)
class DioxusProps:
    """Component props."""

    name: str
    fields: List[RustField] = field(default_factory=list)
    derives: List[str] = field(default_factory=lambda: ["Props", "PartialEq", "Clone"])


@dataclass(frozen=True)
class DioxusHook:
    """A Dioxus hook."""

    hook_type: str  # use_state, use_ref, use_future, etc.
    name: str
    initial_value: Optional[Any] = None
    dependencies: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class DioxusRouter:
    """Dioxus router configuration."""

    routes: List["DioxusRoute"] = field(default_factory=list)
    not_found: Optional[str] = None


@dataclass(frozen=True)
class DioxusRoute:
    """A route definition."""

    path: str
    component: str
    children: List["DioxusRoute"] = field(default_factory=list)
    guards: List[str] = field(default_factory=list)


# ============================================================================
# TAURI FRAMEWORK TYPES
# ============================================================================


@dataclass(frozen=True)
class TauriApp:
    """A Tauri application."""

    name: str
    version: str
    windows: List["TauriWindow"] = field(default_factory=list)
    commands: List["TauriCommand"] = field(default_factory=list)
    menu: Optional["TauriMenu"] = None
    system_tray: Optional["TauriSystemTray"] = None


@dataclass(frozen=True)
class TauriWindow:
    """A Tauri window."""

    label: str
    title: str
    width: int = 800
    height: int = 600
    resizable: bool = True
    fullscreen: bool = False
    decorations: bool = True
    transparent: bool = False
    always_on_top: bool = False
    webview_url: Optional[str] = None


@dataclass(frozen=True)
class TauriCommand:
    """A Tauri command (IPC)."""

    name: str
    function: RustFunction
    is_async: bool = False


@dataclass(frozen=True)
class TauriMenu:
    """Application menu."""

    items: List["TauriMenuItem"] = field(default_factory=list)


@dataclass(frozen=True)
class TauriMenuItem:
    """A menu item."""

    label: str
    accelerator: Optional[str] = None  # Keyboard shortcut
    command: Optional[str] = None
    submenu: Optional[List["TauriMenuItem"]] = None
    is_separator: bool = False
    enabled: bool = True


@dataclass(frozen=True)
class TauriSystemTray:
    """System tray configuration."""

    icon: str
    menu: TauriMenu
    tooltip: Optional[str] = None


# ============================================================================
# CARGO/CRATE STRUCTURE
# ============================================================================


@dataclass(frozen=True)
class CrateConfig:
    """Cargo.toml configuration."""

    name: str
    version: str = "0.1.0"
    edition: str = "2021"
    authors: List[str] = field(default_factory=list)
    dependencies: Dict[str, str] = field(default_factory=dict)
    dev_dependencies: Dict[str, str] = field(default_factory=dict)
    build_dependencies: Dict[str, str] = field(default_factory=dict)
    features: Dict[str, List[str]] = field(default_factory=dict)


@dataclass(frozen=True)
class RustModule:
    """A Rust module."""

    name: str
    path: str
    structs: List[RustStruct] = field(default_factory=list)
    enums: List[RustEnum] = field(default_factory=list)
    functions: List[RustFunction] = field(default_factory=list)
    traits: List[RustTrait] = field(default_factory=list)
    impls: List[RustImpl] = field(default_factory=list)
    submodules: List["RustModule"] = field(default_factory=list)
    uses: List[str] = field(default_factory=list)  # use statements


# ============================================================================
# DOMAIN EVENTS (Colocated with Rust aggregate)
# ============================================================================


@dataclass(frozen=True)
class RustCompiled:
    """Event: Rust code was compiled."""

    crate_name: str
    target: str  # debug, release
    success: bool
    warnings: List[str]
    errors: List[str]
    timestamp: datetime


@dataclass(frozen=True)
class ComponentRendered:
    """Event: Dioxus component rendered."""

    component: DioxusComponent
    props: Optional[Dict[str, Any]]
    render_time_ms: float
    timestamp: datetime


@dataclass(frozen=True)
class TauriCommandInvoked:
    """Event: Tauri command was invoked from frontend."""

    command: TauriCommand
    arguments: Dict[str, Any]
    result: Optional[Any]
    error: Optional[str]
    timestamp: datetime


@dataclass(frozen=True)
class WindowCreated:
    """Event: Tauri window was created."""

    window: TauriWindow
    timestamp: datetime


@dataclass(frozen=True)
class CratePublished:
    """Event: Crate was published to registry."""

    crate_config: CrateConfig
    registry: str  # crates.io, private, etc.
    timestamp: datetime
