"""Core Control Flow Semantic Invariants.

Universal control flow concepts that exist across all programming languages.
These represent sequencing, branching, and transfer of control.
Pure data types following Scott Wlaschin's FDM principles.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Any
from enum import Enum
from datetime import datetime


# ============================================================================
# FUNDAMENTAL CONTROL CONCEPTS
# ============================================================================


@dataclass(frozen=True)
class Control:
    """Abstract control flow construct.

    The flow of execution through a program.
    """

    control_type: "ControlType"
    entry_point: "ControlPoint"
    exit_points: List["ControlPoint"]


class ControlType(str, Enum):
    """Types of control flow."""

    SEQUENCE = "sequence"  # Sequential execution
    BRANCH = "branch"  # Conditional execution
    LOOP = "loop"  # Repetition
    TRANSFER = "transfer"  # Jump/goto/return
    EXCEPTION = "exception"  # Exception handling
    CONCURRENT = "concurrent"  # Parallel execution


@dataclass(frozen=True)
class ControlPoint:
    """A point in the control flow."""

    label: Optional[str] = None
    is_entry: bool = False
    is_exit: bool = False


# ============================================================================
# SEQUENCE (LINEAR EXECUTION)
# ============================================================================


@dataclass(frozen=True)
class Sequence:
    """Sequential execution - statements executed in order.

    The most fundamental control structure.
    """

    statements: List[Any]  # Would be Statement from computation.py
    is_atomic: bool = False  # All-or-nothing execution


@dataclass(frozen=True)
class Block:
    """A block of statements with its own scope.

    Groups statements together.
    """

    statements: List[Any]
    has_local_scope: bool = True
    label: Optional[str] = None


# ============================================================================
# SELECTION (CONDITIONAL EXECUTION)
# ============================================================================


@dataclass(frozen=True)
class Branch:
    """Conditional execution based on a predicate.

    The fundamental selection mechanism.
    """

    condition: "Condition"
    then_branch: Control
    else_branch: Optional[Control] = None


@dataclass(frozen=True)
class Condition:
    """A boolean condition/predicate."""

    expression: Any  # Would be Expression from computation.py
    is_compile_time: bool = False  # Can be evaluated at compile time


@dataclass(frozen=True)
class MultiWayBranch:
    """Multiple-way branching (switch/case/match).

    Selects from multiple alternatives.
    """

    scrutinee: Any  # Expression being matched
    branches: List["CaseBranch"]
    default_branch: Optional[Control] = None
    is_exhaustive: bool = False


@dataclass(frozen=True)
class CaseBranch:
    """One branch in a multi-way selection."""

    pattern: "Pattern"
    guard: Optional[Condition] = None  # Additional condition
    body: Control
    fallthrough: bool = False  # Continue to next case


@dataclass(frozen=True)
class Pattern:
    """A pattern to match against."""

    pattern_type: "PatternType"
    value: Any
    bindings: List[str] = field(default_factory=list)  # Variables bound by pattern


class PatternType(str, Enum):
    """Types of patterns."""

    LITERAL = "literal"  # Exact value
    VARIABLE = "variable"  # Bind to variable
    WILDCARD = "wildcard"  # Match anything
    CONSTRUCTOR = "constructor"  # Data constructor
    ARRAY = "array"  # Array/list pattern
    RECORD = "record"  # Record/object pattern


# ============================================================================
# ITERATION (REPETITION)
# ============================================================================


@dataclass(frozen=True)
class Loop:
    """Repetitive execution.

    The fundamental iteration mechanism.
    """

    loop_type: "LoopType"
    body: Control
    is_infinite: bool = False


class LoopType(str, Enum):
    """Types of loops."""

    WHILE = "while"  # Test at beginning
    DO_WHILE = "do_while"  # Test at end
    FOR = "for"  # Counter-based
    FOR_EACH = "for_each"  # Collection iteration
    RECURSIVE = "recursive"  # Tail recursion


@dataclass(frozen=True)
class WhileLoop(Loop):
    """Loop with condition tested before each iteration."""

    condition: Condition
    invariant: Optional[Any] = None  # Loop invariant for verification


@dataclass(frozen=True)
class DoWhileLoop(Loop):
    """Loop with condition tested after each iteration."""

    condition: Condition
    min_iterations: int = 1


@dataclass(frozen=True)
class ForLoop(Loop):
    """Counter-based loop."""

    initialization: Any  # Initial statement
    condition: Condition
    increment: Any  # Update statement
    loop_variable: str


@dataclass(frozen=True)
class ForEachLoop(Loop):
    """Iteration over collection."""

    iterator_variable: str
    collection: Any  # Expression yielding collection
    is_parallel: bool = False


# ============================================================================
# CONTROL TRANSFER
# ============================================================================


@dataclass(frozen=True)
class Transfer:
    """Transfer of control to another point.

    Breaks normal sequential flow.
    """

    transfer_type: "TransferType"
    target: Optional[ControlPoint] = None


class TransferType(str, Enum):
    """Types of control transfer."""

    GOTO = "goto"  # Unconditional jump
    BREAK = "break"  # Exit loop
    CONTINUE = "continue"  # Next iteration
    RETURN = "return"  # Exit function
    YIELD = "yield"  # Generator/coroutine
    THROW = "throw"  # Raise exception
    EXIT = "exit"  # Exit program


@dataclass(frozen=True)
class Goto:
    """Unconditional jump to label."""

    target_label: str
    is_computed: bool = False  # Computed goto


@dataclass(frozen=True)
class Break:
    """Exit from loop or switch."""

    levels: int = 1  # Number of levels to break
    label: Optional[str] = None  # Labeled break


@dataclass(frozen=True)
class Continue:
    """Skip to next iteration."""

    levels: int = 1  # Number of levels
    label: Optional[str] = None  # Labeled continue


@dataclass(frozen=True)
class Return:
    """Return from function."""

    value: Optional[Any] = None
    is_early_return: bool = False


@dataclass(frozen=True)
class Yield:
    """Yield control (generators/coroutines)."""

    value: Optional[Any] = None
    is_yield_from: bool = False  # Delegating yield


# ============================================================================
# EXCEPTION HANDLING
# ============================================================================


@dataclass(frozen=True)
class ExceptionHandling:
    """Exception/error handling mechanism."""

    try_block: Control
    handlers: List["ExceptionHandler"]
    finally_block: Optional[Control] = None


@dataclass(frozen=True)
class ExceptionHandler:
    """Handler for specific exception type."""

    exception_type: Any  # Type of exception to catch
    variable: Optional[str] = None  # Bind exception to variable
    handler_body: Control
    is_catch_all: bool = False


@dataclass(frozen=True)
class Throw:
    """Raise/throw an exception."""

    exception: Any
    is_rethrow: bool = False


@dataclass(frozen=True)
class Finally:
    """Code that always executes."""

    body: Control
    executes_on_exception: bool = True
    executes_on_normal: bool = True


# ============================================================================
# CONCURRENCY CONTROL
# ============================================================================


@dataclass(frozen=True)
class ConcurrentControl:
    """Concurrent/parallel execution."""

    branches: List[Control]
    synchronization: "SynchronizationType"


class SynchronizationType(str, Enum):
    """Types of synchronization."""

    FORK_JOIN = "fork_join"  # All must complete
    SELECT = "select"  # First to complete
    PIPELINE = "pipeline"  # Staged execution
    ASYNC = "async"  # Asynchronous execution


@dataclass(frozen=True)
class Synchronization:
    """Synchronization primitive."""

    sync_type: "SyncPrimitive"
    participants: List[str]  # Thread/process IDs


class SyncPrimitive(str, Enum):
    """Synchronization primitives."""

    MUTEX = "mutex"
    SEMAPHORE = "semaphore"
    BARRIER = "barrier"
    CONDITION = "condition"
    CHANNEL = "channel"


# ============================================================================
# STRUCTURED CONTROL
# ============================================================================


@dataclass(frozen=True)
class StructuredControl:
    """Structured programming constructs.

    No arbitrary gotos - well-nested control.
    """

    has_single_entry: bool = True
    has_single_exit: bool = True
    is_well_nested: bool = True


@dataclass(frozen=True)
class ControlFlowGraph:
    """Graph representation of control flow."""

    nodes: List["CFGNode"]
    edges: List["CFGEdge"]
    entry_node: "CFGNode"
    exit_nodes: List["CFGNode"]


@dataclass(frozen=True)
class CFGNode:
    """Node in control flow graph."""

    id: str
    statement: Any
    is_branch: bool = False
    is_merge: bool = False


@dataclass(frozen=True)
class CFGEdge:
    """Edge in control flow graph."""

    source: CFGNode
    target: CFGNode
    condition: Optional[Condition] = None
    is_back_edge: bool = False  # Loop back edge


# ============================================================================
# DOMAIN EVENTS (Colocated with Control aggregate)
# ============================================================================


@dataclass(frozen=True)
class ControlFlowEntered:
    """Event: Control flow entered a construct."""

    control: Control
    entry_point: ControlPoint
    timestamp: datetime


@dataclass(frozen=True)
class BranchTaken:
    """Event: Conditional branch was taken."""

    branch: Branch
    condition_result: bool
    branch_taken: str  # "then" or "else"
    timestamp: datetime


@dataclass(frozen=True)
class LoopIteration:
    """Event: Loop iteration occurred."""

    loop: Loop
    iteration_number: int
    continue_condition: bool
    timestamp: datetime


@dataclass(frozen=True)
class ControlTransferred:
    """Event: Control was transferred."""

    transfer: Transfer
    from_point: ControlPoint
    to_point: Optional[ControlPoint]
    timestamp: datetime


@dataclass(frozen=True)
class ExceptionRaised:
    """Event: Exception was raised."""

    exception: Any
    location: ControlPoint
    timestamp: datetime


@dataclass(frozen=True)
class ExceptionCaught:
    """Event: Exception was caught."""

    exception: Any
    handler: ExceptionHandler
    timestamp: datetime
