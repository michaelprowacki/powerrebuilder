"""PowerBuilder Object Domain Types.

Pure data types representing PowerBuilder objects (Windows, DataWindows, etc).
These are the WHAT - no operations, just data models.
Following Scott Wlaschin's FDM principles.

These types are PowerBuilder-specific manifestations of core semantic invariants.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime

from src_new.domain.core.computation import Computation, Function
from src_new.domain.core.types import CompositeType
from src_new.domain.core.binding import Binding, Scope
from src_new.domain.core.effects import SideEffect, IOEffect
from src_new.domain.core.composition import Module, Interface


# ============================================================================
# WINDOW OBJECTS
# ============================================================================


class WindowType(str, Enum):
    """Types of PowerBuilder windows."""

    MAIN = "main"
    CHILD = "child"
    POPUP = "popup"
    RESPONSE = "response"
    MDI = "mdi"
    MDICLIENT = "mdiclient"


@dataclass(frozen=True)
class WindowControl:
    """A control on a PowerBuilder window."""

    name: str
    type: str  # commandbutton, statictext, datawindow, etc.
    x: int
    y: int
    width: int
    height: int
    properties: Dict[str, Any] = field(default_factory=dict)
    events: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class Window:
    """A PowerBuilder window object.

    Manifestation of core Module and Interface concepts.
    Windows are modules that compose controls and handle events.
    """

    name: str
    type: WindowType
    title: str
    width: int
    height: int
    controls: List[WindowControl] = field(default_factory=list)
    menu: Optional[str] = None
    icon: Optional[str] = None
    properties: Dict[str, Any] = field(default_factory=dict)

    # These are manifestations of core concepts
    instance_variables: Dict[str, "Binding"] = field(default_factory=dict)  # Bindings
    events: Dict[str, "Computation"] = field(
        default_factory=dict
    )  # Event handlers are computations
    functions: Dict[str, "Function"] = field(
        default_factory=dict
    )  # Functions with signatures

    # Window as module
    module: Optional["Module"] = None
    interface: Optional["Interface"] = None


# ============================================================================
# DATAWINDOW OBJECTS
# ============================================================================


class DataWindowStyle(str, Enum):
    """DataWindow presentation styles."""

    FREEFORM = "freeform"
    GRID = "grid"
    TABULAR = "tabular"
    GROUP = "group"
    LABEL = "label"
    NUPLABEL = "nuplabel"
    CROSSTAB = "crosstab"
    GRAPH = "graph"
    COMPOSITE = "composite"
    RICHTEXT = "richtext"
    OLE = "ole"
    TREEVIEW = "treeview"


@dataclass(frozen=True)
class DataWindowColumn:
    """A column in a DataWindow."""

    name: str
    datatype: str
    width: int
    label: str
    format: Optional[str] = None
    validation: Optional[str] = None
    edit_style: Optional[str] = None  # edit, dropdown, checkbox, etc.


@dataclass(frozen=True)
class DataWindow:
    """A PowerBuilder DataWindow object.

    Manifestation of core Computation and SideEffect concepts.
    DataWindows perform database I/O (effects) and data transformation (computation).
    """

    name: str
    style: DataWindowStyle
    sql: Optional[str]
    columns: List[DataWindowColumn] = field(default_factory=list)
    retrieve_args: List[str] = field(default_factory=list)
    update_table: Optional[str] = None
    key_columns: List[str] = field(default_factory=list)
    properties: Dict[str, Any] = field(default_factory=dict)

    # DataWindow as computation with effects
    retrieve_computation: Optional["Computation"] = None  # SQL query computation
    update_computation: Optional["Computation"] = None  # Update computation
    io_effects: List["IOEffect"] = field(default_factory=list)  # Database I/O


# ============================================================================
# MENU OBJECTS
# ============================================================================


@dataclass(frozen=True)
class MenuItem:
    """A menu item in a PowerBuilder menu."""

    name: str
    text: str
    enabled: bool = True
    visible: bool = True
    checked: bool = False
    shortcut: Optional[str] = None
    script: Optional[str] = None
    children: List["MenuItem"] = field(default_factory=list)


@dataclass(frozen=True)
class Menu:
    """A PowerBuilder menu object."""

    name: str
    items: List[MenuItem] = field(default_factory=list)
    properties: Dict[str, Any] = field(default_factory=dict)


# ============================================================================
# USER OBJECTS
# ============================================================================


class UserObjectType(str, Enum):
    """Types of user objects."""

    STANDARD = "standard"
    VISUAL = "visual"
    CUSTOM = "custom"
    EXTERNAL = "external"


@dataclass(frozen=True)
class UserObject:
    """A PowerBuilder user object.

    Manifestation of core CompositeType concept.
    User objects are custom types that compose other types.
    """

    name: str
    type: UserObjectType
    ancestor: Optional[str] = None
    controls: List[WindowControl] = field(default_factory=list)
    instance_variables: Dict[str, "Binding"] = field(default_factory=dict)
    events: Dict[str, "Computation"] = field(default_factory=dict)
    functions: Dict[str, "Function"] = field(default_factory=dict)
    properties: Dict[str, Any] = field(default_factory=dict)

    # User object as composite type
    composite_type: Optional["CompositeType"] = None


# ============================================================================
# STRUCTURE OBJECTS
# ============================================================================


@dataclass(frozen=True)
class StructureMember:
    """A member of a PowerBuilder structure."""

    name: str
    datatype: str
    array_bounds: Optional[List[int]] = None
    initial_value: Optional[Any] = None


@dataclass(frozen=True)
class Structure:
    """A PowerBuilder structure object.

    Direct manifestation of core CompositeType (product type).
    """

    name: str
    members: List[StructureMember] = field(default_factory=list)
    scope: "Scope" = None  # Use core Scope concept


# ============================================================================
# APPLICATION OBJECT
# ============================================================================


@dataclass(frozen=True)
class Application:
    """A PowerBuilder application object.

    Top-level module that composes other modules.
    """

    name: str
    library_list: List[str] = field(default_factory=list)
    default_font: Optional[str] = None
    default_pitch: Optional[str] = None
    icon: Optional[str] = None
    open_script: Optional["Computation"] = None  # Startup computation
    close_script: Optional["Computation"] = None  # Shutdown computation
    idle_script: Optional["Computation"] = None  # Idle computation
    properties: Dict[str, Any] = field(default_factory=dict)

    # Application as top-level module
    module: Optional["Module"] = None


# ============================================================================
# FUNCTION OBJECTS
# ============================================================================


class AccessModifier(str, Enum):
    """Access modifiers for functions."""

    PUBLIC = "public"
    PRIVATE = "private"
    PROTECTED = "protected"


@dataclass(frozen=True)
class FunctionArgument:
    """An argument to a function."""

    name: str
    datatype: str
    pass_by: str = "value"  # value, reference
    optional: bool = False
    default_value: Optional[Any] = None


@dataclass(frozen=True)
class PBFunction:
    """A PowerBuilder function object.

    Note: Renamed to avoid conflict with core Function.
    Direct manifestation of core Function concept.
    """

    name: str
    return_type: Optional[str]
    arguments: List[FunctionArgument] = field(default_factory=list)
    access: AccessModifier = AccessModifier.PUBLIC
    script: str = ""
    throws: List[str] = field(default_factory=list)

    # Function as computation
    computation: Optional["Function"] = None


@dataclass(frozen=True)
class Event:
    """A PowerBuilder event.

    Events are computations triggered by external stimuli.
    """

    name: str
    arguments: List[FunctionArgument] = field(default_factory=list)
    return_type: Optional[str] = None
    script: str = ""
    extends: Optional[str] = None  # Parent event

    # Event as computation with possible effects
    computation: Optional["Computation"] = None
    effects: List["SideEffect"] = field(default_factory=list)


# ============================================================================
# DOMAIN EVENTS (Colocated with PowerBuilder aggregate)
# ============================================================================


@dataclass(frozen=True)
class WindowCreated:
    """Event: PowerBuilder window was created."""

    window: Window
    timestamp: datetime


@dataclass(frozen=True)
class DataWindowRetrieved:
    """Event: DataWindow performed retrieve."""

    datawindow: DataWindow
    row_count: int
    timestamp: datetime


@dataclass(frozen=True)
class DataWindowUpdated:
    """Event: DataWindow performed update."""

    datawindow: DataWindow
    rows_affected: int
    timestamp: datetime


@dataclass(frozen=True)
class EventTriggered:
    """Event: PowerBuilder event was triggered."""

    event: Event
    source_object: str
    arguments: Dict[str, Any]
    timestamp: datetime


@dataclass(frozen=True)
class FunctionCalled:
    """Event: PowerBuilder function was called."""

    function: PBFunction
    caller: str
    arguments: Dict[str, Any]
    timestamp: datetime


@dataclass(frozen=True)
class UserObjectInstantiated:
    """Event: User object was instantiated."""

    user_object: UserObject
    parent: Optional[str]
    timestamp: datetime


@dataclass(frozen=True)
class ApplicationStarted:
    """Event: PowerBuilder application started."""

    application: Application
    timestamp: datetime


@dataclass(frozen=True)
class MenuItemClicked:
    """Event: Menu item was clicked."""

    menu_item: MenuItem
    window: str
    timestamp: datetime
