"""Core - Result Monad for Railway-Oriented Programming.

Implements Scott Wlaschin's Railway-Oriented Programming pattern.
A Result is either Success or Failure, enabling functional error handling.
"""

from dataclasses import dataclass
from typing import TypeVar, Generic, Callable, Union, List, Optional, Any
from abc import ABC, abstractmethod

# Type variables for generic Result
T = TypeVar("T")  # Success type
E = TypeVar("E")  # Error type
U = TypeVar("U")  # Transformed success type
F = TypeVar("F")  # Transformed error type


# ============================================================================
# RESULT ALGEBRAIC DATA TYPE
# ============================================================================


class Result(ABC, Generic[T, E]):
    """Abstract base for Result monad.

    A Result is either Success(value) or Failure(error).
    This enables railway-oriented programming where errors
    flow through the pipeline without explicit checking.
    """

    @abstractmethod
    def is_success(self) -> bool:
        """Check if this is a Success."""
        ...

    @abstractmethod
    def is_failure(self) -> bool:
        """Check if this is a Failure."""
        ...

    @abstractmethod
    def value(self) -> Optional[T]:
        """Get the success value if Success, None if Failure."""
        ...

    @abstractmethod
    def error(self) -> Optional[E]:
        """Get the error if Failure, None if Success."""
        ...

    def map(self, func: Callable[[T], U]) -> "Result[U, E]":
        """Transform the success value.

        If Success: applies function to value
        If Failure: passes through unchanged
        """
        if self.is_success():
            try:
                return Success(func(self.value()))
            except Exception as e:
                # Convert exceptions to failures
                return Failure(e)  # type: ignore
        return self  # type: ignore

    def map_error(self, func: Callable[[E], F]) -> "Result[T, F]":
        """Transform the error value.

        If Success: passes through unchanged
        If Failure: applies function to error
        """
        if self.is_failure():
            return Failure(func(self.error()))
        return self  # type: ignore

    def bind(self, func: Callable[[T], "Result[U, E]"]) -> "Result[U, E]":
        """Monadic bind (flatMap).

        Chains operations that return Results.
        If Success: applies function (which returns a Result)
        If Failure: passes through unchanged
        """
        if self.is_success():
            return func(self.value())
        return self  # type: ignore

    def tee(self, func: Callable[[T], None]) -> "Result[T, E]":
        """Execute side effect without changing the value.

        Useful for logging, notifications, etc.
        """
        if self.is_success():
            func(self.value())
        return self

    def or_else(self, default: T) -> T:
        """Get value or return default if Failure."""
        return self.value() if self.is_success() else default

    def or_else_get(self, func: Callable[[E], T]) -> T:
        """Get value or compute default from error if Failure."""
        if self.is_success():
            return self.value()
        return func(self.error())

    def match(self, success: Callable[[T], U], failure: Callable[[E], U]) -> U:
        """Pattern match on Result.

        Exhaustive pattern matching for both cases.
        """
        if self.is_success():
            return success(self.value())
        return failure(self.error())


@dataclass(frozen=True)
class Success(Result[T, E]):
    """Success case of Result."""

    _value: T

    def is_success(self) -> bool:
        return True

    def is_failure(self) -> bool:
        return False

    def value(self) -> Optional[T]:
        return self._value

    def error(self) -> Optional[E]:
        return None

    def __repr__(self) -> str:
        return f"Success({self._value!r})"


@dataclass(frozen=True)
class Failure(Result[T, E]):
    """Failure case of Result."""

    _error: E

    def is_success(self) -> bool:
        return False

    def is_failure(self) -> bool:
        return True

    def value(self) -> Optional[T]:
        return None

    def error(self) -> Optional[E]:
        return self._error

    def __repr__(self) -> str:
        return f"Failure({self._error!r})"


# ============================================================================
# RESULT WITH EVENTS (for observability)
# ============================================================================


@dataclass(frozen=True)
class EventfulResult(Generic[T, E]):
    """Result that also carries events for observability.

    Combines Result monad with event accumulation.
    """

    result: Result[T, E]
    events: List[Any]

    def map(self, func: Callable[[T], U]) -> "EventfulResult[U, E]":
        """Map over the value, preserving events."""
        return EventfulResult(self.result.map(func), self.events)

    def bind(
        self, func: Callable[[T], "EventfulResult[U, E]"]
    ) -> "EventfulResult[U, E]":
        """Bind that accumulates events."""
        if self.result.is_success():
            next_result = func(self.result.value())
            # Combine events from both results
            return EventfulResult(next_result.result, self.events + next_result.events)
        return EventfulResult(self.result, self.events)  # type: ignore

    def add_event(self, event: Any) -> "EventfulResult[T, E]":
        """Add an event to the result."""
        return EventfulResult(self.result, self.events + [event])

    @staticmethod
    def success(value: T, events: List[Any] = None) -> "EventfulResult[T, E]":
        """Create a successful EventfulResult."""
        return EventfulResult(Success(value), events or [])

    @staticmethod
    def failure(error: E, events: List[Any] = None) -> "EventfulResult[T, E]":
        """Create a failed EventfulResult."""
        return EventfulResult(Failure(error), events or [])


# ============================================================================
# COMBINATORS AND UTILITIES
# ============================================================================


def traverse(results: List[Result[T, E]]) -> Result[List[T], E]:
    """Convert list of Results to Result of list.

    If all are Success: returns Success with list of values
    If any is Failure: returns first Failure
    """
    values = []
    for result in results:
        if result.is_failure():
            return Failure(result.error())
        values.append(result.value())
    return Success(values)


def sequence(results: List[Result[T, E]]) -> Result[List[T], E]:
    """Alias for traverse (common in FP)."""
    return traverse(results)


def try_catch(
    func: Callable[[], T], error_mapper: Callable[[Exception], E] = None
) -> Result[T, Union[E, Exception]]:
    """Execute function and wrap result in Result.

    Catches exceptions and converts to Failure.
    """
    try:
        return Success(func())
    except Exception as e:
        if error_mapper:
            return Failure(error_mapper(e))
        return Failure(e)  # type: ignore


def pipeline(*functions: Callable) -> Callable:
    """Compose functions into a pipeline.

    Functions are applied left to right.
    Useful for building data transformation pipelines.
    """

    def piped(value):
        result = value
        for func in functions:
            if isinstance(result, Result):
                result = result.bind(func) if callable(func) else result.map(func)
            else:
                result = func(result)
        return result

    return piped


# ============================================================================
# RAILWAY OPERATORS (for ergonomic chaining)
# ============================================================================


class Railway:
    """Builder for railway-oriented pipelines.

    Provides fluent interface for chaining operations.
    """

    def __init__(self, result: Result[T, E]):
        self.result = result

    def map(self, func: Callable[[T], U]) -> "Railway[U, E]":
        """Transform success value."""
        return Railway(self.result.map(func))

    def bind(self, func: Callable[[T], Result[U, E]]) -> "Railway[U, E]":
        """Chain operation returning Result."""
        return Railway(self.result.bind(func))

    def tee(self, func: Callable[[T], None]) -> "Railway[T, E]":
        """Execute side effect."""
        return Railway(self.result.tee(func))

    def validate(self, predicate: Callable[[T], bool], error: E) -> "Railway[T, E]":
        """Validate value with predicate."""
        if self.result.is_success():
            if not predicate(self.result.value()):
                return Railway(Failure(error))
        return self

    def recover(self, func: Callable[[E], T]) -> "Railway[T, E]":
        """Recover from failure."""
        if self.result.is_failure():
            return Railway(Success(func(self.result.error())))
        return self

    def switch(
        self,
        cases: dict[Any, Callable[[T], Result[U, E]]],
        default: Callable[[T], Result[U, E]] = None,
    ) -> "Railway[U, E]":
        """Switch on value (pattern matching)."""
        if self.result.is_success():
            value = self.result.value()
            handler = cases.get(value, default)
            if handler:
                return Railway(handler(value))
        return Railway(self.result)  # type: ignore

    def get(self) -> Result[T, E]:
        """Get the final Result."""
        return self.result


# ============================================================================
# ASYNC SUPPORT
# ============================================================================

from typing import Awaitable


class AsyncResult(Generic[T, E]):
    """Async version of Result for IO operations."""

    def __init__(self, awaitable: Awaitable[Result[T, E]]):
        self.awaitable = awaitable

    async def map(self, func: Callable[[T], U]) -> Result[U, E]:
        """Async map."""
        result = await self.awaitable
        return result.map(func)

    async def bind(self, func: Callable[[T], Awaitable[Result[U, E]]]) -> Result[U, E]:
        """Async bind."""
        result = await self.awaitable
        if result.is_success():
            return await func(result.value())
        return result  # type: ignore

    async def get(self) -> Result[T, E]:
        """Get the Result."""
        return await self.awaitable


# ============================================================================
# EXAMPLES AND USAGE PATTERNS
# ============================================================================


def example_usage():
    """Example of railway-oriented programming."""

    # Basic Result usage
    result = Success(42)
    doubled = result.map(lambda x: x * 2)  # Success(84)

    # Chaining with bind
    def safe_divide(x: int) -> Result[float, str]:
        if x == 0:
            return Failure("Division by zero")
        return Success(10.0 / x)

    chain = Success(5).bind(safe_divide)  # Success(2.0)

    # Railway builder pattern
    railway = (
        Railway(Success(10))
        .map(lambda x: x * 2)
        .validate(lambda x: x > 0, "Value must be positive")
        .bind(safe_divide)
        .tee(print)  # Side effect for logging
        .get()
    )

    # Pattern matching
    message = result.match(
        success=lambda v: f"Got value: {v}", failure=lambda e: f"Got error: {e}"
    )

    # EventfulResult for tracking
    eventful = EventfulResult.success(42, ["Started processing"])
    eventful = eventful.add_event("Validation passed")
    eventful = eventful.map(lambda x: x * 2)

    return railway, eventful
