"""Iced Widgets Domain Types.

Iced widget types - the building blocks of the UI.
These are Iced-specific manifestations of universal UI concepts.
Pure data types following Scott Wlaschin's FDM principles.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Generic, TypeVar, Any, Callable
from enum import Enum
from datetime import datetime


M = TypeVar("M")  # Message type


# ============================================================================
# CORE WIDGET CONCEPTS
# ============================================================================


@dataclass(frozen=True)
class Widget(Generic[M]):
    """Base widget type - an element of the UI.

    Manifestation of core UI Component concept.
    """

    widget_type: "WidgetType"
    width: "Length" = field(default_factory=lambda: Length())
    height: "Length" = field(default_factory=lambda: Length())
    padding: "Padding" = field(default_factory=lambda: Padding())
    id: Optional[str] = None


class WidgetType(str, Enum):
    """Types of Iced widgets."""

    BUTTON = "button"
    TEXT = "text"
    TEXT_INPUT = "text_input"
    CHECKBOX = "checkbox"
    RADIO = "radio"
    SLIDER = "slider"
    PICK_LIST = "pick_list"
    TOGGLER = "toggler"
    CONTAINER = "container"
    ROW = "row"
    COLUMN = "column"
    SCROLLABLE = "scrollable"
    PROGRESS_BAR = "progress_bar"
    RULE = "rule"  # Horizontal/vertical line
    SPACE = "space"
    IMAGE = "image"
    SVG = "svg"
    CANVAS = "canvas"
    PANE_GRID = "pane_grid"
    TOOLTIP = "tooltip"
    CUSTOM = "custom"


# ============================================================================
# LAYOUT TYPES
# ============================================================================


@dataclass(frozen=True)
class Length:
    """Length specification for widgets."""

    length_type: "LengthType" = "LengthType.SHRINK"
    value: Optional[float] = None  # For fixed length


class LengthType(str, Enum):
    """Types of length specifications."""

    SHRINK = "shrink"  # Minimum size
    FILL = "fill"  # Fill available space
    FILL_PORTION = "fill_portion"  # Fill with portion
    FIXED = "fixed"  # Fixed size in pixels


@dataclass(frozen=True)
class Padding:
    """Padding around widget content."""

    top: float = 0
    right: float = 0
    bottom: float = 0
    left: float = 0

    @staticmethod
    def all(value: float) -> "Padding":
        """Uniform padding."""
        return Padding(value, value, value, value)


@dataclass(frozen=True)
class Alignment:
    """Alignment of content."""

    horizontal: "HorizontalAlignment" = "HorizontalAlignment.LEFT"
    vertical: "VerticalAlignment" = "VerticalAlignment.TOP"


class HorizontalAlignment(str, Enum):
    """Horizontal alignment options."""

    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"


class VerticalAlignment(str, Enum):
    """Vertical alignment options."""

    TOP = "top"
    CENTER = "center"
    BOTTOM = "bottom"


@dataclass(frozen=True)
class Spacing:
    """Spacing between elements."""

    amount: float = 0


# ============================================================================
# INPUT WIDGETS
# ============================================================================


@dataclass(frozen=True)
class Button(Widget[M]):
    """A clickable button.

    Maps to PowerBuilder CommandButton.
    """

    label: str
    on_press: Optional[M] = None
    style: Optional["ButtonStyle"] = None


@dataclass(frozen=True)
class TextInput(Widget[M]):
    """Text input field.

    Maps to PowerBuilder SingleLineEdit/MultiLineEdit.
    """

    placeholder: str = ""
    value: str = ""
    on_change: Optional[Callable[[str], M]] = None
    on_submit: Optional[M] = None
    is_password: bool = False
    max_length: Optional[int] = None
    style: Optional["TextInputStyle"] = None


@dataclass(frozen=True)
class Checkbox(Widget[M]):
    """A checkbox widget.

    Maps to PowerBuilder CheckBox.
    """

    label: str
    is_checked: bool = False
    on_toggle: Optional[Callable[[bool], M]] = None
    style: Optional["CheckboxStyle"] = None


@dataclass(frozen=True)
class Radio(Widget[M]):
    """Radio button widget.

    Maps to PowerBuilder RadioButton.
    """

    label: str
    value: Any
    selected: Optional[Any] = None
    on_select: Optional[Callable[[Any], M]] = None
    style: Optional["RadioStyle"] = None


@dataclass(frozen=True)
class Slider(Widget[M]):
    """A slider for numeric input.

    Maps to PowerBuilder HScrollBar/VScrollBar when used for input.
    """

    range: tuple[float, float]
    value: float
    step: float = 1.0
    on_change: Optional[Callable[[float], M]] = None
    on_release: Optional[M] = None
    style: Optional["SliderStyle"] = None


@dataclass(frozen=True)
class PickList(Widget[M]):
    """Dropdown selection widget.

    Maps to PowerBuilder DropDownListBox.
    """

    options: List[Any]
    selected: Optional[Any] = None
    placeholder: str = "Select..."
    on_select: Optional[Callable[[Any], M]] = None
    style: Optional["PickListStyle"] = None


@dataclass(frozen=True)
class Toggler(Widget[M]):
    """Toggle switch widget."""

    label: Optional[str] = None
    is_toggled: bool = False
    on_toggle: Optional[Callable[[bool], M]] = None
    style: Optional["TogglerStyle"] = None


# ============================================================================
# DISPLAY WIDGETS
# ============================================================================


@dataclass(frozen=True)
class Text(Widget[M]):
    """Text display widget.

    Maps to PowerBuilder StaticText.
    """

    content: str
    size: Optional[float] = None
    color: Optional[str] = None
    font: Optional["Font"] = None
    horizontal_alignment: HorizontalAlignment = HorizontalAlignment.LEFT
    vertical_alignment: VerticalAlignment = VerticalAlignment.TOP


@dataclass(frozen=True)
class Image(Widget[M]):
    """Image display widget.

    Maps to PowerBuilder Picture.
    """

    source: str  # Path or bytes
    content_fit: "ContentFit" = "ContentFit.CONTAIN"


class ContentFit(str, Enum):
    """How image fits in bounds."""

    CONTAIN = "contain"  # Maintain aspect ratio, fit inside
    COVER = "cover"  # Maintain aspect ratio, cover area
    FILL = "fill"  # Stretch to fill
    NONE = "none"  # Original size
    SCALE_DOWN = "scale_down"  # Like contain but never upscale


@dataclass(frozen=True)
class ProgressBar(Widget[M]):
    """Progress bar widget."""

    value: float  # 0.0 to 1.0
    style: Optional["ProgressBarStyle"] = None


@dataclass(frozen=True)
class Rule(Widget[M]):
    """Horizontal or vertical line."""

    is_horizontal: bool = True
    style: Optional["RuleStyle"] = None


@dataclass(frozen=True)
class Space(Widget[M]):
    """Empty space for layout."""

    width: Length
    height: Length


# ============================================================================
# CONTAINER WIDGETS
# ============================================================================


@dataclass(frozen=True)
class Container(Widget[M]):
    """Container for a single child widget.

    Maps to PowerBuilder GroupBox or general container.
    """

    child: Widget[M]
    padding: Padding = field(default_factory=lambda: Padding.all(0))
    width: Length = field(default_factory=lambda: Length())
    height: Length = field(default_factory=lambda: Length())
    max_width: Optional[float] = None
    max_height: Optional[float] = None
    horizontal_alignment: HorizontalAlignment = HorizontalAlignment.LEFT
    vertical_alignment: VerticalAlignment = VerticalAlignment.TOP
    style: Optional["ContainerStyle"] = None


@dataclass(frozen=True)
class Row(Widget[M]):
    """Horizontal layout container.

    Maps to horizontal arrangement in PowerBuilder.
    """

    children: List[Widget[M]]
    spacing: float = 0
    padding: Padding = field(default_factory=lambda: Padding.all(0))
    align_items: VerticalAlignment = VerticalAlignment.CENTER


@dataclass(frozen=True)
class Column(Widget[M]):
    """Vertical layout container.

    Maps to vertical arrangement in PowerBuilder.
    """

    children: List[Widget[M]]
    spacing: float = 0
    padding: Padding = field(default_factory=lambda: Padding.all(0))
    align_items: HorizontalAlignment = HorizontalAlignment.LEFT


@dataclass(frozen=True)
class Scrollable(Widget[M]):
    """Scrollable container.

    Maps to scrollable areas in PowerBuilder windows.
    """

    child: Widget[M]
    horizontal_scroll: bool = False
    vertical_scroll: bool = True
    on_scroll: Optional[Callable[[float], M]] = None
    style: Optional["ScrollableStyle"] = None


# ============================================================================
# ADVANCED WIDGETS
# ============================================================================


@dataclass(frozen=True)
class PaneGrid(Widget[M]):
    """Resizable pane grid.

    Maps to PowerBuilder split windows.
    """

    panes: List["Pane"]
    on_resize: Optional[Callable[[Any], M]] = None
    style: Optional["PaneGridStyle"] = None


@dataclass(frozen=True)
class Pane:
    """A pane in a PaneGrid."""

    content: Widget
    can_resize: bool = True
    min_size: Optional[float] = None
    max_size: Optional[float] = None


@dataclass(frozen=True)
class Canvas(Widget[M]):
    """Canvas for custom drawing.

    Maps to PowerBuilder drawing areas.
    """

    program: "CanvasProgram[M]"
    width: Length
    height: Length


@dataclass(frozen=True)
class CanvasProgram(Generic[M]):
    """Drawing program for canvas."""

    draw_commands: List["DrawCommand"]
    on_event: Optional[Callable[[Any], M]] = None


@dataclass(frozen=True)
class DrawCommand:
    """A drawing command."""

    command_type: str  # line, rect, circle, text, etc.
    parameters: Dict[str, Any]


@dataclass(frozen=True)
class Tooltip(Widget[M]):
    """Tooltip wrapper widget."""

    content: Widget[M]
    tooltip: str
    position: "TooltipPosition" = "TooltipPosition.TOP"
    style: Optional["TooltipStyle"] = None


class TooltipPosition(str, Enum):
    """Tooltip positions."""

    TOP = "top"
    BOTTOM = "bottom"
    LEFT = "left"
    RIGHT = "right"
    FOLLOW_CURSOR = "follow_cursor"


# ============================================================================
# STYLING
# ============================================================================


@dataclass(frozen=True)
class Style:
    """Base style type."""

    background: Optional[str] = None  # Color
    text_color: Optional[str] = None
    border_radius: float = 0
    border_width: float = 0
    border_color: Optional[str] = None


@dataclass(frozen=True)
class ButtonStyle(Style):
    """Button-specific styling."""

    active_background: Optional[str] = None
    hovered_background: Optional[str] = None
    pressed_background: Optional[str] = None


@dataclass(frozen=True)
class TextInputStyle(Style):
    """Text input styling."""

    selection_color: Optional[str] = None
    placeholder_color: Optional[str] = None


@dataclass(frozen=True)
class ContainerStyle(Style):
    """Container styling."""

    text_color: Optional[str] = None


@dataclass(frozen=True)
class Font:
    """Font specification."""

    family: str = "default"
    size: float = 16
    weight: "FontWeight" = "FontWeight.NORMAL"
    style: "FontStyle" = "FontStyle.NORMAL"


class FontWeight(str, Enum):
    """Font weights."""

    THIN = "thin"
    LIGHT = "light"
    NORMAL = "normal"
    MEDIUM = "medium"
    SEMIBOLD = "semibold"
    BOLD = "bold"
    BLACK = "black"


class FontStyle(str, Enum):
    """Font styles."""

    NORMAL = "normal"
    ITALIC = "italic"
    OBLIQUE = "oblique"


# ============================================================================
# DOMAIN EVENTS (Colocated with Widget aggregate)
# ============================================================================


@dataclass(frozen=True)
class WidgetCreated:
    """Event: Widget was created."""

    widget: Widget
    parent: Optional[Widget]
    timestamp: datetime


@dataclass(frozen=True)
class WidgetInteraction:
    """Event: User interacted with widget."""

    widget: Widget
    interaction_type: str  # click, input, scroll, etc.
    message_produced: Optional[Any]
    timestamp: datetime


@dataclass(frozen=True)
class WidgetUpdated:
    """Event: Widget properties changed."""

    widget: Widget
    changed_properties: Dict[str, Any]
    timestamp: datetime


@dataclass(frozen=True)
class LayoutCalculated:
    """Event: Layout was calculated."""

    root_widget: Widget
    layout_time_ms: float
    total_widgets: int
    timestamp: datetime
