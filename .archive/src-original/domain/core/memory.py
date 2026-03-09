"""Core Memory Management Semantic Invariants.

Universal concepts of memory allocation, lifetime, and ownership.
These represent how programs manage storage and resources.
Pure data types following Scott Wlaschin's FDM principles.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Any
from enum import Enum
from datetime import datetime


# ============================================================================
# FUNDAMENTAL MEMORY CONCEPTS
# ============================================================================


@dataclass(frozen=True)
class Memory:
    """Abstract memory/storage concept.

    Where data lives during program execution.
    """

    size: int  # Size in bytes
    location: "MemoryLocation"
    is_accessible: bool = True
    is_initialized: bool = False


@dataclass(frozen=True)
class MemoryLocation:
    """A location in memory."""

    address: Any  # Abstract address
    segment: "MemorySegment"
    offset: Optional[int] = None
    is_valid: bool = True


class MemorySegment(str, Enum):
    """Memory segments/regions."""

    STACK = "stack"  # Function call stack
    HEAP = "heap"  # Dynamic allocation
    STATIC = "static"  # Static/global data
    CODE = "code"  # Program code
    REGISTER = "register"  # CPU registers
    CACHE = "cache"  # CPU cache


# ============================================================================
# ALLOCATION CONCEPTS
# ============================================================================


@dataclass(frozen=True)
class Allocation:
    """Memory allocation."""

    size: int
    location: MemoryLocation
    allocation_type: "AllocationType"
    alignment: int = 1  # Byte alignment
    is_zeroed: bool = False


class AllocationType(str, Enum):
    """Types of allocation."""

    STATIC = "static"  # Compile-time allocation
    STACK = "stack"  # Stack allocation
    HEAP = "heap"  # Heap allocation
    POOL = "pool"  # Memory pool
    ARENA = "arena"  # Arena/region allocation


@dataclass(frozen=True)
class Deallocation:
    """Memory deallocation."""

    location: MemoryLocation
    size: int
    deallocation_type: "DeallocationType"


class DeallocationType(str, Enum):
    """Types of deallocation."""

    MANUAL = "manual"  # Explicit free
    AUTOMATIC = "automatic"  # Stack unwind
    GARBAGE_COLLECTED = "gc"  # GC
    REFERENCE_COUNTED = "refcount"  # Reference counting
    RAII = "raii"  # Resource acquisition is initialization


# ============================================================================
# LIFETIME CONCEPTS
# ============================================================================


@dataclass(frozen=True)
class Lifetime:
    """The duration for which memory/reference is valid.

    Universal concept, explicit in Rust, implicit elsewhere.
    """

    name: str
    scope: "LifetimeScope"
    is_static: bool = False  # Lives for entire program
    outlives: List["Lifetime"] = field(default_factory=list)


@dataclass(frozen=True)
class LifetimeScope:
    """Scope that defines a lifetime."""

    scope_type: "LifetimeScopeType"
    entry_point: Any  # When lifetime begins
    exit_point: Any  # When lifetime ends


class LifetimeScopeType(str, Enum):
    """Types of lifetime scopes."""

    STATIC = "static"  # Entire program
    FUNCTION = "function"  # Function call
    BLOCK = "block"  # Block scope
    EXPRESSION = "expression"  # Expression temporary
    DYNAMIC = "dynamic"  # Until explicitly freed


@dataclass(frozen=True)
class LifetimeBound:
    """Constraint on lifetime relationships."""

    subject: Lifetime
    constraint: str  # "outlives", "equals", "shorter_than"
    target: Lifetime


# ============================================================================
# OWNERSHIP CONCEPTS
# ============================================================================


@dataclass(frozen=True)
class Ownership:
    """Ownership of memory/resources.

    Most explicit in Rust, but exists conceptually everywhere.
    """

    owner: "Owner"
    resource: Memory
    ownership_type: "OwnershipType"
    can_transfer: bool = True


@dataclass(frozen=True)
class Owner:
    """Entity that owns memory."""

    owner_type: "OwnerType"
    identifier: str  # Variable name, object id, etc.
    is_unique: bool = True  # Single owner


class OwnerType(str, Enum):
    """Types of owners."""

    VARIABLE = "variable"  # Variable owns value
    OBJECT = "object"  # Object owns fields
    SMART_POINTER = "smart_pointer"  # Smart pointer
    RUNTIME = "runtime"  # Runtime/GC owns
    SYSTEM = "system"  # OS owns


class OwnershipType(str, Enum):
    """Types of ownership."""

    UNIQUE = "unique"  # Single owner (Rust)
    SHARED = "shared"  # Multiple owners (Rc)
    BORROWED = "borrowed"  # Temporary use (reference)
    LEAKED = "leaked"  # No owner (memory leak)


@dataclass(frozen=True)
class Borrow:
    """Borrowing/referencing memory.

    Temporary access without ownership.
    """

    borrowed_from: Owner
    borrow_type: "BorrowType"
    lifetime: Lifetime
    is_exclusive: bool = False  # Mutable borrow


class BorrowType(str, Enum):
    """Types of borrows."""

    IMMUTABLE = "immutable"  # Read-only borrow
    MUTABLE = "mutable"  # Read-write borrow
    RAW = "raw"  # Raw pointer
    WEAK = "weak"  # Weak reference


@dataclass(frozen=True)
class Move:
    """Transfer of ownership."""

    from_owner: Owner
    to_owner: Owner
    resource: Memory
    invalidates_source: bool = True  # Source no longer valid


# ============================================================================
# REFERENCE CONCEPTS
# ============================================================================


@dataclass(frozen=True)
class Reference:
    """A reference/pointer to memory."""

    target: MemoryLocation
    reference_type: "ReferenceType"
    is_valid: bool = True
    can_be_null: bool = False


class ReferenceType(str, Enum):
    """Types of references."""

    STRONG = "strong"  # Strong reference
    WEAK = "weak"  # Weak reference
    RAW = "raw"  # Raw pointer
    SMART = "smart"  # Smart pointer
    BORROWED = "borrowed"  # Borrowed reference


@dataclass(frozen=True)
class Pointer:
    """A pointer (address of memory)."""

    address: int
    pointed_type: Any  # Type of pointed-to data
    is_aligned: bool = True
    is_valid: bool = True


@dataclass(frozen=True)
class SmartPointer:
    """Smart pointer with automatic management."""

    pointer_type: "SmartPointerType"
    target: Memory
    reference_count: Optional[int] = None
    deleter: Optional[Any] = None  # Custom deleter


class SmartPointerType(str, Enum):
    """Types of smart pointers."""

    UNIQUE = "unique"  # unique_ptr, Box
    SHARED = "shared"  # shared_ptr, Rc
    WEAK = "weak"  # weak_ptr
    INTRUSIVE = "intrusive"  # Intrusive pointer


# ============================================================================
# GARBAGE COLLECTION
# ============================================================================


@dataclass(frozen=True)
class GarbageCollection:
    """Automatic memory management."""

    gc_type: "GCType"
    heap_size: int
    collection_threshold: int
    is_generational: bool = False


class GCType(str, Enum):
    """Types of garbage collection."""

    MARK_SWEEP = "mark_sweep"
    COPYING = "copying"
    REFERENCE_COUNTING = "refcount"
    GENERATIONAL = "generational"
    INCREMENTAL = "incremental"
    CONCURRENT = "concurrent"


@dataclass(frozen=True)
class GCRoot:
    """Root for garbage collection."""

    root_type: str  # stack, global, register
    references: List[Reference]


@dataclass(frozen=True)
class GCCycle:
    """A garbage collection cycle."""

    collected_bytes: int
    remaining_bytes: int
    duration_ms: float
    was_full: bool = False


# ============================================================================
# MEMORY SAFETY
# ============================================================================


@dataclass(frozen=True)
class MemorySafety:
    """Memory safety guarantees."""

    prevents_null_deref: bool
    prevents_use_after_free: bool
    prevents_double_free: bool
    prevents_buffer_overflow: bool
    prevents_data_races: bool
    is_enforced: str = "runtime"  # compile-time, runtime, none


@dataclass(frozen=True)
class MemoryError:
    """Memory-related error."""

    error_type: "MemoryErrorType"
    location: MemoryLocation
    is_recoverable: bool = False


class MemoryErrorType(str, Enum):
    """Types of memory errors."""

    NULL_DEREFERENCE = "null_deref"
    USE_AFTER_FREE = "use_after_free"
    DOUBLE_FREE = "double_free"
    BUFFER_OVERFLOW = "buffer_overflow"
    BUFFER_UNDERFLOW = "buffer_underflow"
    MEMORY_LEAK = "memory_leak"
    STACK_OVERFLOW = "stack_overflow"
    SEGMENTATION_FAULT = "segfault"
    DATA_RACE = "data_race"


# ============================================================================
# RESOURCE MANAGEMENT
# ============================================================================


@dataclass(frozen=True)
class Resource:
    """Any managed resource (not just memory)."""

    resource_type: "ResourceType"
    handle: Any
    is_acquired: bool = False
    requires_cleanup: bool = True


class ResourceType(str, Enum):
    """Types of resources."""

    MEMORY = "memory"
    FILE = "file"
    SOCKET = "socket"
    LOCK = "lock"
    THREAD = "thread"
    HANDLE = "handle"


@dataclass(frozen=True)
class RAII:
    """Resource Acquisition Is Initialization."""

    resource: Resource
    constructor_acquires: bool = True
    destructor_releases: bool = True
    is_exception_safe: bool = True


@dataclass(frozen=True)
class Finalizer:
    """Cleanup code for resource."""

    resource: Resource
    cleanup_function: Any
    is_guaranteed: bool = False  # Guaranteed to run?


# ============================================================================
# DOMAIN EVENTS (Colocated with Memory aggregate)
# ============================================================================


@dataclass(frozen=True)
class MemoryAllocated:
    """Event: Memory was allocated."""

    allocation: Allocation
    requestor: str
    timestamp: datetime


@dataclass(frozen=True)
class MemoryDeallocated:
    """Event: Memory was freed."""

    deallocation: Deallocation
    freed_by: str
    timestamp: datetime


@dataclass(frozen=True)
class OwnershipTransferred:
    """Event: Ownership was moved."""

    move: Move
    timestamp: datetime


@dataclass(frozen=True)
class MemoryLeaked:
    """Event: Memory leak detected."""

    leaked_memory: Memory
    last_owner: Optional[Owner]
    timestamp: datetime


@dataclass(frozen=True)
class GarbageCollected:
    """Event: Garbage collection occurred."""

    gc_cycle: GCCycle
    timestamp: datetime


@dataclass(frozen=True)
class MemoryErrorOccurred:
    """Event: Memory error occurred."""

    error: MemoryError
    timestamp: datetime
