"""Core Computation Semantic Invariants.

Universal computational concepts that exist across all programming languages.
These are the fundamental semantic building blocks.
Pure data types following Scott Wlaschin's FDM principles.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Any
from enum import Enum
from datetime import datetime


# ============================================================================
# FUNDAMENTAL COMPUTATION CONCEPTS
# ============================================================================


@dataclass(frozen=True)
class Computation:
    """The universal concept of computation: input → output transformation.

    This is the most fundamental concept in all programming languages.
    A computation takes inputs and produces outputs, possibly with effects.
    """

    name: str
    inputs: List["Value"]
    output: Optional["Value"]
    is_pure: bool = True  # No side effects
    effects: List["SideEffect"] = field(default_factory=list)


@dataclass(frozen=True)
class Expression:
    """A construct that evaluates to a value.

    Universal across all languages - something that can be reduced to a value.
    """

    result_type: "Type"
    is_constant: bool = False  # Can be evaluated at compile time
    dependencies: List["Name"] = field(default_factory=list)  # Names it depends on


@dataclass(frozen=True)
class Statement:
    """A construct that performs effects without producing a value.

    Universal concept of imperative action.
    """

    effects: List["SideEffect"]
    modifies: List["Name"] = field(default_factory=list)  # Names it modifies


@dataclass(frozen=True)
class Function:
    """A named, reusable computation.

    Present in all languages in some form (procedure, method, function, lambda).
    """

    name: "Name"
    parameters: List["Parameter"]
    return_type: Optional["Type"]
    body: "Computation"
    is_pure: bool = True
    is_recursive: bool = False


@dataclass(frozen=True)
class Parameter:
    """A function input specification.

    Universal concept of parameterization.
    """

    name: "Name"
    parameter_type: "Type"
    is_optional: bool = False
    default_value: Optional["Value"] = None
    pass_by: str = "value"  # value, reference, name


@dataclass(frozen=True)
class Return:
    """The result of a computation.

    Universal concept of producing output.
    """

    value: Optional["Value"]
    return_type: Optional["Type"]


# ============================================================================
# EVALUATION CONCEPTS
# ============================================================================


class EvaluationStrategy(str, Enum):
    """How expressions are evaluated."""

    EAGER = "eager"  # Call-by-value
    LAZY = "lazy"  # Call-by-need
    NORMAL = "normal"  # Call-by-name


@dataclass(frozen=True)
class Evaluation:
    """The process of reducing an expression to a value.

    Universal concept of computation execution.
    """

    expression: Expression
    environment: "Environment"
    strategy: EvaluationStrategy = EvaluationStrategy.EAGER
    result: Optional["Value"] = None


@dataclass(frozen=True)
class Application:
    """Function application - the fundamental operation.

    Applying a function to arguments (from lambda calculus).
    """

    function: Function
    arguments: List["Value"]
    result: Optional["Value"] = None


# ============================================================================
# LAMBDA CALCULUS FOUNDATIONS
# ============================================================================


@dataclass(frozen=True)
class Lambda:
    """Lambda abstraction - anonymous function.

    The foundation of functional programming.
    """

    parameter: Parameter
    body: Expression
    closure: "Environment" = field(default_factory=dict)  # Captured environment


@dataclass(frozen=True)
class Closure:
    """A function with its captured environment.

    Universal concept in languages with lexical scope.
    """

    function: Function
    captured_environment: "Environment"


# ============================================================================
# COMPOSITION PATTERNS
# ============================================================================


@dataclass(frozen=True)
class Composition:
    """Function composition: (f ∘ g)(x) = f(g(x)).

    Universal concept of combining computations.
    """

    outer: Function
    inner: Function


@dataclass(frozen=True)
class Pipeline:
    """Sequential composition of computations.

    Data flows through a series of transformations.
    """

    stages: List[Function]
    is_parallel: bool = False


@dataclass(frozen=True)
class HigherOrderFunction:
    """A function that operates on other functions.

    Takes functions as input or returns functions.
    """

    name: Name
    function_parameters: List[Function]
    returns_function: bool


# ============================================================================
# RECURSION AND ITERATION
# ============================================================================


@dataclass(frozen=True)
class Recursion:
    """Self-referential computation.

    Universal concept of recursive definition.
    """

    base_case: Expression
    recursive_case: Function
    termination_condition: Expression


@dataclass(frozen=True)
class TailRecursion:
    """Optimizable recursion pattern.

    Last operation is recursive call.
    """

    function: Function
    accumulator: Parameter
    is_optimizable: bool = True


# ============================================================================
# PARTIAL APPLICATION AND CURRYING
# ============================================================================


@dataclass(frozen=True)
class PartialApplication:
    """Fixing some arguments of a function.

    Creates a new function with fewer parameters.
    """

    original_function: Function
    fixed_arguments: Dict[str, "Value"]
    remaining_parameters: List[Parameter]


@dataclass(frozen=True)
class Curry:
    """Transform multi-argument function to nested single-argument functions.

    f(a,b,c) becomes f(a)(b)(c).
    """

    original_function: Function
    curried_form: Lambda


# ============================================================================
# DOMAIN EVENTS (Colocated with Computation aggregate)
# ============================================================================


@dataclass(frozen=True)
class ComputationStarted:
    """Event: Computation began execution."""

    computation: Computation
    input_values: List[Any]
    timestamp: datetime


@dataclass(frozen=True)
class ComputationCompleted:
    """Event: Computation finished successfully."""

    computation: Computation
    result: Any
    execution_time: float
    timestamp: datetime


@dataclass(frozen=True)
class ComputationFailed:
    """Event: Computation failed with error."""

    computation: Computation
    error: str
    timestamp: datetime


@dataclass(frozen=True)
class FunctionDefined:
    """Event: New function was defined."""

    function: Function
    module: str
    timestamp: datetime


@dataclass(frozen=True)
class FunctionApplied:
    """Event: Function was applied to arguments."""

    function: Function
    arguments: List[Any]
    result: Any
    timestamp: datetime


# ============================================================================
# TYPE IMPORTS (to avoid circular dependencies)
# ============================================================================

# These would normally come from types.py, binding.py, effects.py
# Using forward references for now

Name = str  # Will be imported from binding.py
Type = Any  # Will be imported from types.py
Value = Any  # Will be imported from types.py
Environment = Dict[Name, Value]  # Will be imported from binding.py
SideEffect = Any  # Will be imported from effects.py
