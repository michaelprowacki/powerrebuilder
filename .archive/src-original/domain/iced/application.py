"""Iced Application Domain Types.

Iced-specific manifestations of core semantic concepts.
Iced is a cross-platform GUI library for Rust with Elm-inspired architecture.
Pure data types following Scott Wlaschin's FDM principles.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Generic, TypeVar, Any, Dict
from enum import Enum
from datetime import datetime


# Type variables for generic Message and State
M = TypeVar("M")  # Message type
S = TypeVar("S")  # State type


# ============================================================================
# ICED APPLICATION ARCHITECTURE (Elm-inspired)
# ============================================================================


@dataclass(frozen=True)
class IcedApplication(Generic[S, M]):
    """An Iced application following The Elm Architecture.

    Manifestation of core Computation + State + UI concepts.
    """

    title: str
    state: S  # Application state
    update: "UpdateFunction[S, M]"
    view: "ViewFunction[S, M]"
    subscription: Optional["SubscriptionFunction[S, M]"] = None
    theme: Optional["Theme"] = None
    scale_factor: float = 1.0


@dataclass(frozen=True)
class State:
    """Application state - the single source of truth.

    Manifestation of core State concept.
    """

    data: Dict[str, Any]
    is_immutable: bool = True  # Iced uses immutable state updates


@dataclass(frozen=True)
class Message:
    """A message that triggers state updates.

    Manifestation of core Event/Effect concepts.
    """

    message_type: str
    payload: Optional[Any] = None
    is_async: bool = False


# ============================================================================
# THE ELM ARCHITECTURE FUNCTIONS
# ============================================================================


@dataclass(frozen=True)
class UpdateFunction(Generic[S, M]):
    """Update function: (State, Message) -> (State, Command).

    Pure function that updates state based on messages.
    Manifestation of core Computation concept.
    """

    name: str = "update"
    is_pure: bool = True  # Must be pure
    returns_command: bool = True  # Can return async commands


@dataclass(frozen=True)
class ViewFunction(Generic[S, M]):
    """View function: State -> Element<Message>.

    Pure function that renders UI from state.
    Manifestation of core Expression concept.
    """

    name: str = "view"
    is_pure: bool = True  # Must be pure
    is_memoized: bool = False  # Can be memoized


@dataclass(frozen=True)
class SubscriptionFunction(Generic[S, M]):
    """Subscription function: State -> Subscription<Message>.

    Subscribes to external events (time, keyboard, etc).
    Manifestation of core Effect concept.
    """

    name: str = "subscription"
    event_sources: List["EventSource"] = field(default_factory=list)


# ============================================================================
# COMMANDS (Async Effects)
# ============================================================================


@dataclass(frozen=True)
class Command(Generic[M]):
    """An async command that produces messages.

    Manifestation of core IO/Effect concepts.
    """

    command_type: "CommandType"
    produces_message: bool = True
    is_cancelable: bool = False


class CommandType(str, Enum):
    """Types of commands."""

    NONE = "none"  # No effect
    PERFORM = "perform"  # Async operation
    BATCH = "batch"  # Multiple commands
    CUSTOM = "custom"  # Custom async operation


@dataclass(frozen=True)
class AsyncCommand(Command[M]):
    """Async operation that produces a message."""

    operation: str  # HTTP request, file I/O, etc.
    on_success: Optional[M] = None
    on_error: Optional[M] = None


@dataclass(frozen=True)
class BatchCommand(Command[M]):
    """Multiple commands executed together."""

    commands: List[Command[M]]
    is_parallel: bool = True


# ============================================================================
# SUBSCRIPTIONS (Event Streams)
# ============================================================================


@dataclass(frozen=True)
class Subscription(Generic[M]):
    """Subscription to external events.

    Manifestation of core Event/Stream concepts.
    """

    subscription_type: "SubscriptionType"
    produces_messages: List[M] = field(default_factory=list)


class SubscriptionType(str, Enum):
    """Types of subscriptions."""

    NONE = "none"  # No subscription
    TIME = "time"  # Timer events
    KEYBOARD = "keyboard"  # Keyboard events
    MOUSE = "mouse"  # Mouse events
    WINDOW = "window"  # Window events
    CUSTOM = "custom"  # Custom event stream


@dataclass(frozen=True)
class TimeSubscription(Subscription[M]):
    """Timer subscription."""

    interval_ms: int
    message_constructor: str  # Function that creates message


@dataclass(frozen=True)
class KeyboardSubscription(Subscription[M]):
    """Keyboard event subscription."""

    key_filter: Optional[List[str]] = None  # Specific keys to listen for
    on_press: Optional[M] = None
    on_release: Optional[M] = None


@dataclass(frozen=True)
class EventSource:
    """Source of events for subscriptions."""

    source_type: str
    filter: Optional[Any] = None
    debounce_ms: Optional[int] = None


# ============================================================================
# RUNTIME AND EXECUTION
# ============================================================================


@dataclass(frozen=True)
class Runtime:
    """The Iced runtime that coordinates everything.

    Manifestation of core Environment/Context concepts.
    """

    event_loop: "EventLoop"
    renderer: "Renderer"
    is_running: bool = False


@dataclass(frozen=True)
class EventLoop:
    """Event loop that processes messages."""

    pending_messages: List[Message]
    is_busy: bool = False
    fps_limit: Optional[int] = 60


@dataclass(frozen=True)
class Renderer:
    """Renderer for drawing UI."""

    backend: "RendererBackend"
    is_gpu_accelerated: bool = True


class RendererBackend(str, Enum):
    """Rendering backends."""

    WGPU = "wgpu"  # WebGPU (default)
    OPENGL = "opengl"  # OpenGL
    SOFTWARE = "software"  # Software rendering


# ============================================================================
# APPLICATION LIFECYCLE
# ============================================================================


@dataclass(frozen=True)
class ApplicationLifecycle:
    """Lifecycle events of an Iced application."""

    phase: "LifecyclePhase"
    timestamp: datetime


class LifecyclePhase(str, Enum):
    """Application lifecycle phases."""

    INITIALIZING = "initializing"
    RUNNING = "running"
    SUSPENDED = "suspended"
    TERMINATING = "terminating"


@dataclass(frozen=True)
class Sandbox:
    """Simplified Iced application without async."""

    title: str
    state: State
    update: UpdateFunction
    view: ViewFunction
    # No subscriptions or commands in sandbox


# ============================================================================
# THEME AND STYLING
# ============================================================================


@dataclass(frozen=True)
class Theme:
    """Application theme."""

    name: str
    palette: "Palette"
    is_dark: bool = False
    is_custom: bool = False


@dataclass(frozen=True)
class Palette:
    """Color palette for theme."""

    background: str  # Hex color
    surface: str
    primary: str
    secondary: str
    success: str
    danger: str
    text: str


# ============================================================================
# FLAGS AND SETTINGS
# ============================================================================


@dataclass(frozen=True)
class Flags:
    """Initial flags/settings for application."""

    window_settings: "WindowSettings"
    debug: bool = False
    antialiasing: bool = True


@dataclass(frozen=True)
class WindowSettings:
    """Window configuration."""

    size: tuple[int, int] = (800, 600)
    position: Optional[tuple[int, int]] = None
    min_size: Optional[tuple[int, int]] = None
    max_size: Optional[tuple[int, int]] = None
    resizable: bool = True
    decorations: bool = True
    transparent: bool = False
    always_on_top: bool = False


# ============================================================================
# PERFORMANCE AND OPTIMIZATION
# ============================================================================


@dataclass(frozen=True)
class PerformanceMetrics:
    """Performance metrics for Iced app."""

    fps: float
    frame_time_ms: float
    message_queue_size: int
    memory_usage_mb: float


@dataclass(frozen=True)
class Optimization:
    """Optimization settings."""

    lazy_widgets: bool = True  # Lazy widget evaluation
    cache_rendering: bool = True  # Cache rendered elements
    batch_commands: bool = True  # Batch command execution


# ============================================================================
# DOMAIN EVENTS (Colocated with Iced Application aggregate)
# ============================================================================


@dataclass(frozen=True)
class ApplicationStarted:
    """Event: Iced application started."""

    application: IcedApplication
    initial_state: Any
    timestamp: datetime


@dataclass(frozen=True)
class MessageDispatched:
    """Event: Message was dispatched."""

    message: Message
    state_before: Any
    state_after: Any
    command_produced: Optional[Command]
    timestamp: datetime


@dataclass(frozen=True)
class ViewRendered:
    """Event: View was rendered."""

    state: Any
    render_time_ms: float
    widgets_count: int
    timestamp: datetime


@dataclass(frozen=True)
class CommandExecuted:
    """Event: Async command was executed."""

    command: Command
    result: Optional[Message]
    error: Optional[str]
    timestamp: datetime


@dataclass(frozen=True)
class SubscriptionTriggered:
    """Event: Subscription produced a message."""

    subscription: Subscription
    message: Message
    timestamp: datetime


@dataclass(frozen=True)
class ApplicationTerminated:
    """Event: Application shut down."""

    application: IcedApplication
    final_state: Any
    runtime_seconds: float
    timestamp: datetime
