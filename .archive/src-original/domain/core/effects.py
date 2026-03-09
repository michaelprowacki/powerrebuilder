"""Core Effects and Side Effects Semantic Invariants.

Universal concepts of computational effects that exist across all languages.
These represent state changes, I/O, and other observable behaviors.
Pure data types following Scott Wlaschin's FDM principles.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Any, Set
from enum import Enum
from datetime import datetime


# ============================================================================
# FUNDAMENTAL EFFECT CONCEPTS
# ============================================================================


@dataclass(frozen=True)
class Effect:
    """An observable effect of computation.

    Something that affects the world outside the computation.
    """

    effect_type: "EffectType"
    is_observable: bool = True
    is_reversible: bool = False  # Can be undone
    dependencies: List["Effect"] = field(default_factory=list)


class EffectType(str, Enum):
    """Types of computational effects."""

    STATE = "state"  # State modification
    IO = "io"  # Input/output
    EXCEPTION = "exception"  # Exception/error
    NONTERMINATION = "nontermination"  # Infinite loop/divergence
    NONDETERMINISM = "nondeterminism"  # Random/undefined behavior
    CONCURRENCY = "concurrency"  # Thread/process effects
    MEMORY = "memory"  # Allocation/deallocation
    TIME = "time"  # Time-dependent behavior


@dataclass(frozen=True)
class SideEffect(Effect):
    """A side effect - modification outside the computation's result.

    Breaks referential transparency.
    """

    target: "EffectTarget"
    operation: "EffectOperation"
    is_idempotent: bool = False  # Same effect if applied multiple times


@dataclass(frozen=True)
class EffectTarget:
    """What is being affected."""

    target_type: "EffectTargetType"
    identifier: Any  # Variable name, file path, etc.
    scope: str = "local"  # local, global, external


class EffectTargetType(str, Enum):
    """Types of effect targets."""

    VARIABLE = "variable"
    FILE = "file"
    NETWORK = "network"
    DATABASE = "database"
    CONSOLE = "console"
    MEMORY = "memory"
    PROCESS = "process"
    ENVIRONMENT = "environment"


class EffectOperation(str, Enum):
    """Operations that cause effects."""

    READ = "read"
    WRITE = "write"
    APPEND = "append"
    DELETE = "delete"
    CREATE = "create"
    MODIFY = "modify"
    EXECUTE = "execute"


# ============================================================================
# PURITY AND REFERENTIAL TRANSPARENCY
# ============================================================================


@dataclass(frozen=True)
class PureComputation:
    """A computation with no side effects.

    Always returns same output for same input.
    """

    computation: Any  # Would be Computation from computation.py
    is_deterministic: bool = True
    is_total: bool = True  # Defined for all inputs
    is_referentially_transparent: bool = True


@dataclass(frozen=True)
class ReferentialTransparency:
    """Property that expressions can be replaced with their values.

    Foundation of equational reasoning.
    """

    expression: Any
    can_substitute: bool = True
    preserves_meaning: bool = True


@dataclass(frozen=True)
class Impurity:
    """Reason why a computation is not pure."""

    reason: "ImpurityReason"
    effects: List[Effect]


class ImpurityReason(str, Enum):
    """Reasons for impurity."""

    MUTATES_STATE = "mutates_state"
    PERFORMS_IO = "performs_io"
    THROWS_EXCEPTION = "throws_exception"
    NON_DETERMINISTIC = "non_deterministic"
    DEPENDS_ON_TIME = "depends_on_time"
    DEPENDS_ON_EXTERNAL = "depends_on_external"


# ============================================================================
# STATE EFFECTS
# ============================================================================


@dataclass(frozen=True)
class State:
    """Mutable state."""

    variables: Dict[str, Any]
    is_global: bool = False
    version: int = 0  # For tracking changes


@dataclass(frozen=True)
class StateChange:
    """A change to state."""

    variable: str
    old_value: Any
    new_value: Any
    change_type: "StateChangeType"
    is_atomic: bool = True


class StateChangeType(str, Enum):
    """Types of state changes."""

    ASSIGNMENT = "assignment"
    INCREMENT = "increment"
    DECREMENT = "decrement"
    APPEND = "append"
    REMOVE = "remove"
    SWAP = "swap"


@dataclass(frozen=True)
class StateTransaction:
    """Transactional state changes."""

    changes: List[StateChange]
    is_atomic: bool = True
    is_isolated: bool = True
    can_rollback: bool = True


# ============================================================================
# I/O EFFECTS
# ============================================================================


@dataclass(frozen=True)
class IO:
    """Input/output effect."""

    io_type: "IOType"
    channel: "IOChannel"
    data: Optional[Any] = None
    is_blocking: bool = True


class IOType(str, Enum):
    """Types of I/O."""

    READ = "read"
    WRITE = "write"
    SEEK = "seek"
    FLUSH = "flush"
    CLOSE = "close"


@dataclass(frozen=True)
class IOChannel:
    """An I/O channel/stream."""

    channel_type: "ChannelType"
    identifier: str  # File path, URL, etc.
    is_buffered: bool = True
    encoding: Optional[str] = None


class ChannelType(str, Enum):
    """Types of I/O channels."""

    FILE = "file"
    CONSOLE = "console"
    NETWORK = "network"
    PIPE = "pipe"
    MEMORY = "memory"


@dataclass(frozen=True)
class FileIO(IO):
    """File I/O operation."""

    file_path: str
    mode: str  # read, write, append
    offset: Optional[int] = None


@dataclass(frozen=True)
class NetworkIO(IO):
    """Network I/O operation."""

    protocol: str  # TCP, UDP, HTTP
    address: str
    port: Optional[int] = None


# ============================================================================
# EXCEPTION EFFECTS
# ============================================================================


@dataclass(frozen=True)
class ExceptionEffect(Effect):
    """Effect of raising/throwing an exception."""

    exception_type: str
    message: str
    is_checked: bool = False  # Checked vs unchecked
    is_recoverable: bool = True


@dataclass(frozen=True)
class ErrorPropagation:
    """How errors propagate through the system."""

    propagation_type: "PropagationType"
    error_chain: List[Any]


class PropagationType(str, Enum):
    """Types of error propagation."""

    THROW = "throw"  # Exception throwing
    RETURN = "return"  # Error return values
    CALLBACK = "callback"  # Error callbacks
    MONAD = "monad"  # Maybe/Either monads
    PANIC = "panic"  # Unrecoverable panic


# ============================================================================
# CONCURRENCY EFFECTS
# ============================================================================


@dataclass(frozen=True)
class ConcurrencyEffect(Effect):
    """Effects related to concurrent execution."""

    concurrency_type: "ConcurrencyType"
    threads: List[str]  # Thread/process identifiers
    shared_resources: List[str]


class ConcurrencyType(str, Enum):
    """Types of concurrency effects."""

    RACE_CONDITION = "race_condition"
    DEADLOCK = "deadlock"
    LIVELOCK = "livelock"
    STARVATION = "starvation"
    MEMORY_CONSISTENCY = "memory_consistency"


@dataclass(frozen=True)
class Synchronization:
    """Synchronization to control effects."""

    mechanism: "SyncMechanism"
    protected_resources: List[str]


class SyncMechanism(str, Enum):
    """Synchronization mechanisms."""

    LOCK = "lock"
    SEMAPHORE = "semaphore"
    MONITOR = "monitor"
    BARRIER = "barrier"
    ATOMIC = "atomic"
    TRANSACTIONAL = "transactional"


# ============================================================================
# MEMORY EFFECTS
# ============================================================================


@dataclass(frozen=True)
class MemoryEffect(Effect):
    """Effects on memory."""

    operation: "MemoryOperation"
    size: Optional[int] = None
    location: Optional[Any] = None


class MemoryOperation(str, Enum):
    """Memory operations."""

    ALLOCATE = "allocate"
    DEALLOCATE = "deallocate"
    LEAK = "leak"
    CORRUPT = "corrupt"
    OVERFLOW = "overflow"


@dataclass(frozen=True)
class AllocationEffect(MemoryEffect):
    """Memory allocation effect."""

    allocated_size: int
    is_heap: bool = True  # Heap vs stack
    is_zeroed: bool = False


@dataclass(frozen=True)
class DeallocationEffect(MemoryEffect):
    """Memory deallocation effect."""

    freed_size: int
    is_automatic: bool = False  # GC vs manual


# ============================================================================
# EFFECT HANDLING
# ============================================================================


@dataclass(frozen=True)
class EffectHandler:
    """Handler for effects (algebraic effects)."""

    handled_effects: List[EffectType]
    handler_function: Any
    is_resumable: bool = True  # Can resume after handling


@dataclass(frozen=True)
class EffectSystem:
    """Type system for tracking effects."""

    tracked_effects: Set[EffectType]
    effect_polymorphism: bool = False
    effect_inference: bool = False


@dataclass(frozen=True)
class Monad:
    """Monadic effect handling."""

    monad_type: "MonadType"
    wrapped_type: Any
    operations: List[str]  # bind, return, etc.


class MonadType(str, Enum):
    """Common monads for effects."""

    IO = "io"
    STATE = "state"
    MAYBE = "maybe"
    EITHER = "either"
    READER = "reader"
    WRITER = "writer"
    CONTINUATION = "continuation"


# ============================================================================
# DOMAIN EVENTS (Colocated with Effects aggregate)
# ============================================================================


@dataclass(frozen=True)
class EffectPerformed:
    """Event: An effect was performed."""

    effect: Effect
    context: str
    timestamp: datetime


@dataclass(frozen=True)
class StateModified:
    """Event: State was modified."""

    change: StateChange
    transaction_id: Optional[str]
    timestamp: datetime


@dataclass(frozen=True)
class IOPerformed:
    """Event: I/O operation performed."""

    io_operation: IO
    bytes_transferred: Optional[int]
    success: bool
    timestamp: datetime


@dataclass(frozen=True)
class ExceptionOccurred:
    """Event: Exception effect occurred."""

    exception: ExceptionEffect
    handled: bool
    timestamp: datetime


@dataclass(frozen=True)
class MemoryAllocated:
    """Event: Memory was allocated."""

    allocation: AllocationEffect
    timestamp: datetime


@dataclass(frozen=True)
class MemoryDeallocated:
    """Event: Memory was freed."""

    deallocation: DeallocationEffect
    timestamp: datetime
