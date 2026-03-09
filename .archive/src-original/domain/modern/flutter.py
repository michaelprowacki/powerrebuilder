"""Flutter/Dart Domain Types.

Pure data types representing Flutter/Dart constructs.
These are the WHAT - no operations, just data models.
Following Scott Wlaschin's FDM principles.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum


# ============================================================================
# DART LANGUAGE TYPES
# ============================================================================


class DartType(str, Enum):
    """Dart data types."""

    INT = "int"
    DOUBLE = "double"
    NUM = "num"
    STRING = "String"
    BOOL = "bool"
    LIST = "List"
    MAP = "Map"
    SET = "Set"
    DYNAMIC = "dynamic"
    VOID = "void"
    FUTURE = "Future"
    STREAM = "Stream"
    FUNCTION = "Function"


@dataclass(frozen=True)
class DartVariable:
    """A Dart variable."""

    name: str
    type: DartType
    is_final: bool = False
    is_const: bool = False
    is_late: bool = False
    is_nullable: bool = False
    initial_value: Optional[Any] = None


@dataclass(frozen=True)
class DartFunction:
    """A Dart function."""

    name: str
    return_type: DartType
    parameters: List["DartParameter"] = field(default_factory=list)
    is_async: bool = False
    is_generator: bool = False
    body: Optional[str] = None


@dataclass(frozen=True)
class DartParameter:
    """A function parameter."""

    name: str
    type: DartType
    is_required: bool = True
    is_named: bool = False
    default_value: Optional[Any] = None


@dataclass(frozen=True)
class DartClass:
    """A Dart class."""

    name: str
    extends: Optional[str] = None
    implements: List[str] = field(default_factory=list)
    mixins: List[str] = field(default_factory=list)
    is_abstract: bool = False
    fields: List[DartVariable] = field(default_factory=list)
    methods: List[DartFunction] = field(default_factory=list)
    constructors: List["DartConstructor"] = field(default_factory=list)


@dataclass(frozen=True)
class DartConstructor:
    """A class constructor."""

    name: Optional[str] = None  # None for default constructor
    parameters: List[DartParameter] = field(default_factory=list)
    is_const: bool = False
    is_factory: bool = False
    initializers: List[str] = field(default_factory=list)


# ============================================================================
# FLUTTER WIDGET TYPES
# ============================================================================


class WidgetType(str, Enum):
    """Types of Flutter widgets."""

    STATELESS = "stateless"
    STATEFUL = "stateful"
    INHERITED = "inherited"


@dataclass(frozen=True)
class Widget:
    """A Flutter widget."""

    name: str
    type: WidgetType
    properties: Dict[str, Any] = field(default_factory=dict)
    child: Optional["Widget"] = None
    children: List["Widget"] = field(default_factory=list)


@dataclass(frozen=True)
class StatelessWidget:
    """A stateless Flutter widget."""

    name: str
    properties: List[DartVariable] = field(default_factory=list)
    build_method: str = ""


@dataclass(frozen=True)
class StatefulWidget:
    """A stateful Flutter widget."""

    name: str
    properties: List[DartVariable] = field(default_factory=list)
    state_class: "State"


@dataclass(frozen=True)
class State:
    """State for a stateful widget."""

    name: str
    widget_class: str
    state_variables: List[DartVariable] = field(default_factory=list)
    init_state: Optional[str] = None
    build_method: str = ""
    dispose: Optional[str] = None
    lifecycle_methods: Dict[str, str] = field(default_factory=dict)


# ============================================================================
# FLUTTER UI COMPONENTS
# ============================================================================


@dataclass(frozen=True)
class MaterialApp:
    """Flutter MaterialApp configuration."""

    title: str
    theme: "ThemeData"
    home: Widget
    routes: Dict[str, Widget] = field(default_factory=dict)
    debug_show_checked_mode_banner: bool = False


@dataclass(frozen=True)
class ThemeData:
    """Flutter theme configuration."""

    primary_swatch: Optional[str] = None
    primary_color: Optional[str] = None
    accent_color: Optional[str] = None
    brightness: str = "light"
    font_family: Optional[str] = None
    text_theme: Optional["TextTheme"] = None


@dataclass(frozen=True)
class TextTheme:
    """Text theme configuration."""

    headline1: Optional[Dict[str, Any]] = None
    headline2: Optional[Dict[str, Any]] = None
    body1: Optional[Dict[str, Any]] = None
    body2: Optional[Dict[str, Any]] = None
    caption: Optional[Dict[str, Any]] = None


@dataclass(frozen=True)
class Scaffold:
    """Scaffold widget structure."""

    app_bar: Optional["AppBar"] = None
    body: Optional[Widget] = None
    drawer: Optional[Widget] = None
    bottom_navigation_bar: Optional[Widget] = None
    floating_action_button: Optional[Widget] = None


@dataclass(frozen=True)
class AppBar:
    """AppBar widget."""

    title: str
    actions: List[Widget] = field(default_factory=list)
    leading: Optional[Widget] = None
    background_color: Optional[str] = None


# ============================================================================
# FLUTTER LAYOUT WIDGETS
# ============================================================================


@dataclass(frozen=True)
class Container:
    """Container widget."""

    child: Optional[Widget] = None
    width: Optional[float] = None
    height: Optional[float] = None
    padding: Optional["EdgeInsets"] = None
    margin: Optional["EdgeInsets"] = None
    decoration: Optional["BoxDecoration"] = None


@dataclass(frozen=True)
class Row:
    """Row layout widget."""

    children: List[Widget]
    main_axis_alignment: str = "start"
    cross_axis_alignment: str = "center"


@dataclass(frozen=True)
class Column:
    """Column layout widget."""

    children: List[Widget]
    main_axis_alignment: str = "start"
    cross_axis_alignment: str = "center"


@dataclass(frozen=True)
class EdgeInsets:
    """Padding/margin values."""

    left: float = 0
    top: float = 0
    right: float = 0
    bottom: float = 0


@dataclass(frozen=True)
class BoxDecoration:
    """Box decoration."""

    color: Optional[str] = None
    border_radius: Optional[float] = None
    box_shadow: Optional[List["BoxShadow"]] = None
    gradient: Optional["Gradient"] = None


@dataclass(frozen=True)
class BoxShadow:
    """Box shadow effect."""

    color: str
    offset: tuple[float, float]
    blur_radius: float
    spread_radius: float = 0


@dataclass(frozen=True)
class Gradient:
    """Gradient decoration."""

    colors: List[str]
    stops: Optional[List[float]] = None
    begin: str = "topLeft"
    end: str = "bottomRight"


# ============================================================================
# STATE MANAGEMENT
# ============================================================================


@dataclass(frozen=True)
class Provider:
    """Provider state management."""

    name: str
    type: str
    value: Any
    child: Widget


@dataclass(frozen=True)
class BlocState:
    """BLoC state."""

    name: str
    properties: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class BlocEvent:
    """BLoC event."""

    name: str
    data: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Bloc:
    """Business Logic Component."""

    name: str
    states: List[BlocState] = field(default_factory=list)
    events: List[BlocEvent] = field(default_factory=list)
    initial_state: BlocState


# ============================================================================
# ROUTING AND NAVIGATION
# ============================================================================


@dataclass(frozen=True)
class Route:
    """A navigation route."""

    name: str
    path: str
    widget: Widget
    arguments: Dict[str, DartType] = field(default_factory=dict)


@dataclass(frozen=True)
class NavigationStack:
    """Navigation stack state."""

    routes: List[Route]
    current_index: int
