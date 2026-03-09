"""Rust Ownership Domain Types.

Rust's unique ownership system for memory safety without GC.
These are Rust-specific manifestations of core Memory concepts.
Pure data types following Scott Wlaschin's FDM principles.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Any, Generic, TypeVar
from enum import Enum
from datetime import datetime


T = TypeVar("T")


# ============================================================================
# OWNERSHIP (Rust's unique memory model)
# ============================================================================


@dataclass(frozen=True)
class Ownership:
    """Rust ownership - each value has exactly one owner.

    Manifestation of core Ownership concept with Rust's strict rules.
    """

    value: Any
    owner: "Owner"
    is_moved: bool = False  # Has ownership been transferred?
    drop_order: Optional[int] = None  # Order in which it will be dropped


@dataclass(frozen=True)
class Owner:
    """The owner of a value in Rust."""

    owner_type: "OwnerType"
    name: str  # Variable name, field name, etc.
    scope: "Scope"
    can_move: bool = True  # Can transfer ownership


class OwnerType(str, Enum):
    """Types of owners in Rust."""

    VARIABLE = "variable"  # let x = ...
    FIELD = "field"  # Struct/enum field
    HEAP = "heap"  # Box, Vec, String, etc.
    STATIC = "static"  # Static variable
    TEMPORARY = "temporary"  # Temporary value


@dataclass(frozen=True)
class Scope:
    """Scope that determines when values are dropped."""

    scope_type: "ScopeType"
    level: int  # Nesting level
    lifetime: "Lifetime"


class ScopeType(str, Enum):
    """Types of scopes in Rust."""

    FUNCTION = "function"
    BLOCK = "block"
    IF = "if"
    MATCH = "match"
    LOOP = "loop"
    UNSAFE = "unsafe"
    ASYNC = "async"
    CONST = "const"


# ============================================================================
# BORROWING (References without ownership)
# ============================================================================


@dataclass(frozen=True)
class Borrow:
    """Borrowing in Rust - temporary access without ownership.

    Manifestation of core Reference concept with Rust's borrow rules.
    """

    borrowed_value: Any
    borrow_kind: "BorrowKind"
    lifetime: "Lifetime"
    is_active: bool = True


class BorrowKind(str, Enum):
    """Kinds of borrows in Rust."""

    IMMUTABLE = "&"  # Shared reference
    MUTABLE = "&mut"  # Exclusive reference
    RAW_CONST = "*const"  # Raw pointer (unsafe)
    RAW_MUT = "*mut"  # Mutable raw pointer (unsafe)


@dataclass(frozen=True)
class BorrowChecker:
    """The borrow checker's view of the program.

    Ensures memory safety at compile time.
    """

    active_borrows: List[Borrow]
    borrow_conflicts: List["BorrowConflict"]
    is_valid: bool = True


@dataclass(frozen=True)
class BorrowConflict:
    """A conflict detected by the borrow checker."""

    conflict_type: "ConflictType"
    first_borrow: Borrow
    second_borrow: Borrow
    error_message: str


class ConflictType(str, Enum):
    """Types of borrow conflicts."""

    MULTIPLE_MUTABLE = "multiple_mutable"  # Two &mut
    MUTABLE_AND_IMMUTABLE = "mut_and_immut"  # &mut and &
    USE_AFTER_MOVE = "use_after_move"
    USE_AFTER_FREE = "use_after_free"
    LIFETIME_MISMATCH = "lifetime_mismatch"


# ============================================================================
# LIFETIMES (How long references are valid)
# ============================================================================


@dataclass(frozen=True)
class Lifetime:
    """Lifetime annotation in Rust.

    Ensures references don't outlive their data.
    """

    name: str  # 'a, 'static, etc.
    scope: Scope
    outlives: List["Lifetime"] = field(default_factory=list)  # 'a: 'b
    is_static: bool = False  # 'static lifetime


@dataclass(frozen=True)
class LifetimeParameter:
    """Lifetime parameter in function/struct definition."""

    name: str
    bounds: List["LifetimeBound"] = field(default_factory=list)


@dataclass(frozen=True)
class LifetimeBound:
    """Bound on a lifetime."""

    bound_type: "LifetimeBoundType"
    target: str  # The lifetime it relates to


class LifetimeBoundType(str, Enum):
    """Types of lifetime bounds."""

    OUTLIVES = "outlives"  # 'a: 'b
    EQUALS = "equals"  # Same lifetime
    STATIC = "static"  # Must be 'static


@dataclass(frozen=True)
class LifetimeElision:
    """Lifetime elision rules - when lifetimes can be inferred."""

    rule: "ElisionRule"
    can_elide: bool = True


class ElisionRule(str, Enum):
    """Lifetime elision rules."""

    SINGLE_INPUT = "single_input"  # One input lifetime
    SELF_REFERENCE = "self_reference"  # &self or &mut self
    STATIC = "static"  # 'static can be elided


# ============================================================================
# MOVE SEMANTICS
# ============================================================================


@dataclass(frozen=True)
class Move:
    """Move semantics - transferring ownership.

    Fundamental to Rust's memory model.
    """

    moved_value: Any
    from_owner: Owner
    to_owner: Owner
    invalidates_source: bool = True  # Always true in Rust


@dataclass(frozen=True)
class Copy:
    """Copy trait - types that can be copied bitwise.

    Alternative to move for simple types.
    """

    value: Any
    implements_copy: bool
    size_bytes: int


@dataclass(frozen=True)
class Clone:
    """Clone trait - explicit duplication."""

    value: Any
    implements_clone: bool
    is_deep_clone: bool = True


# ============================================================================
# SMART POINTERS (Owned pointers with special behavior)
# ============================================================================


@dataclass(frozen=True)
class Box(Generic[T]):
    """Box<T> - heap allocation with single owner.

    Maps to PowerBuilder dynamic memory allocation.
    """

    value: T
    is_pinned: bool = False  # Pin<Box<T>>


@dataclass(frozen=True)
class Rc(Generic[T]):
    """Rc<T> - reference counted pointer.

    Multiple owners, immutable access.
    """

    value: T
    strong_count: int = 1
    weak_count: int = 0
    is_cyclic: bool = False  # Can cause memory leak


@dataclass(frozen=True)
class Arc(Generic[T]):
    """Arc<T> - atomic reference counted.

    Thread-safe version of Rc.
    """

    value: T
    strong_count: int = 1
    weak_count: int = 0
    is_send: bool = True
    is_sync: bool = True


@dataclass(frozen=True)
class RefCell(Generic[T]):
    """RefCell<T> - interior mutability with runtime borrow checking.

    Allows mutation of immutable references.
    """

    value: T
    borrow_state: "BorrowState"


class BorrowState(str, Enum):
    """State of RefCell borrow."""

    UNUSED = "unused"
    SHARED = "shared"  # One or more &T
    EXCLUSIVE = "exclusive"  # Exactly one &mut T


@dataclass(frozen=True)
class Cell(Generic[T]):
    """Cell<T> - interior mutability for Copy types."""

    value: T
    requires_copy: bool = True


# ============================================================================
# DROP AND RAII
# ============================================================================


@dataclass(frozen=True)
class Drop:
    """Drop trait - custom destructor.

    RAII (Resource Acquisition Is Initialization) in Rust.
    """

    value: Any
    custom_drop: bool = False
    drop_order: int  # Order within scope
    drops_recursively: bool = True


@dataclass(frozen=True)
class ManuallyDrop(Generic[T]):
    """ManuallyDrop<T> - prevent automatic drop."""

    value: T
    is_dropped: bool = False


@dataclass(frozen=True)
class Forget:
    """std::mem::forget - leak memory intentionally."""

    value: Any
    reason: str


# ============================================================================
# UNSAFE AND RAW POINTERS
# ============================================================================


@dataclass(frozen=True)
class UnsafeBlock:
    """Unsafe block - bypass safety checks."""

    operations: List["UnsafeOperation"]
    justification: str  # Why is this safe?


@dataclass(frozen=True)
class UnsafeOperation:
    """Operation that requires unsafe."""

    operation_type: "UnsafeOpType"
    target: Any


class UnsafeOpType(str, Enum):
    """Types of unsafe operations."""

    DEREF_RAW = "deref_raw"  # Dereference raw pointer
    CALL_UNSAFE_FN = "call_unsafe"  # Call unsafe function
    ACCESS_STATIC_MUT = "static_mut"  # Access mutable static
    IMPLEMENT_UNSAFE_TRAIT = "unsafe_trait"
    ACCESS_UNION_FIELD = "union_field"


@dataclass(frozen=True)
class RawPointer:
    """Raw pointer - no safety guarantees."""

    address: int
    pointer_type: str  # *const T or *mut T
    is_aligned: bool = True
    is_valid: bool = True  # May be invalid!
    is_null: bool = False


# ============================================================================
# PINNING (Preventing moves)
# ============================================================================


@dataclass(frozen=True)
class Pin(Generic[T]):
    """Pin<T> - guarantee value won't move in memory.

    Important for async and self-referential structs.
    """

    value: T
    is_pinned: bool = True
    can_unpin: bool = False


@dataclass(frozen=True)
class Unpin:
    """Unpin trait - safe to move even when pinned."""

    implements_unpin: bool = True


# ============================================================================
# PHANTOM DATA
# ============================================================================


@dataclass(frozen=True)
class PhantomData(Generic[T]):
    """PhantomData<T> - zero-sized marker for lifetime/type relationships.

    Tells compiler about ownership without storing data.
    """

    phantom_type: str  # The type it pretends to own
    variance: "Variance"


class Variance(str, Enum):
    """Variance of type parameters."""

    COVARIANT = "covariant"  # T -> U implies F<T> -> F<U>
    CONTRAVARIANT = "contravariant"  # T -> U implies F<U> -> F<T>
    INVARIANT = "invariant"  # No subtyping relationship


# ============================================================================
# DOMAIN EVENTS (Colocated with Ownership aggregate)
# ============================================================================


@dataclass(frozen=True)
class OwnershipTransferred:
    """Event: Ownership was moved."""

    move: Move
    location: str
    timestamp: datetime


@dataclass(frozen=True)
class BorrowCreated:
    """Event: Borrow was created."""

    borrow: Borrow
    checker_approved: bool
    timestamp: datetime


@dataclass(frozen=True)
class BorrowConflictDetected:
    """Event: Borrow checker found conflict."""

    conflict: BorrowConflict
    compilation_failed: bool
    timestamp: datetime


@dataclass(frozen=True)
class ValueDropped:
    """Event: Value was dropped."""

    drop: Drop
    freed_memory: int
    timestamp: datetime


@dataclass(frozen=True)
class UnsafeBlockEntered:
    """Event: Entered unsafe block."""

    unsafe_block: UnsafeBlock
    timestamp: datetime


@dataclass(frozen=True)
class LifetimeInferred:
    """Event: Lifetime was inferred by compiler."""

    lifetime: Lifetime
    elision_rule: ElisionRule
    timestamp: datetime
