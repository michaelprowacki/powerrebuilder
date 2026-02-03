"""Base Parser Pattern - Abstract base for all parsing operations.

Consolidates parsing patterns found in:
- Binary file parsing (PBL/PBD)
- P-code parsing
- PowerBuilder source parsing
- Grammar-based parsing
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Generic, List, Optional, TypeVar, Union

T = TypeVar("T")


@dataclass
class ParseResult:
    """Standard result from parsing operations."""

    success: bool
    data: Any
    errors: List[str]
    warnings: List[str]
    position: int = 0
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class BaseParser(ABC, Generic[T]):
    """Abstract base for all parsers.

    Provides common parsing patterns and error handling.
    """

    def __init__(self, strict: bool = False):
        """Initialize parser.

        Args:
            strict: Whether to fail on warnings
        """
        self.strict = strict
        self.errors = []
        self.warnings = []

    @abstractmethod
    def parse_impl(self, data: Union[str, bytes]) -> T:
        """Implementation-specific parsing logic.

        Args:
            data: Data to parse

        Returns:
            Parsed result

        Raises:
            ParseError: If parsing fails
        """
        pass

    def parse(self, data: Union[str, bytes]) -> ParseResult:
        """Parse data with error handling.

        Args:
            data: Data to parse

        Returns:
            ParseResult with parsed data or errors
        """
        self.errors = []
        self.warnings = []

        try:
            result = self.parse_impl(data)

            success = len(self.errors) == 0
            if self.strict and len(self.warnings) > 0:
                success = False

            return ParseResult(
                success=success,
                data=result,
                errors=self.errors.copy(),
                warnings=self.warnings.copy(),
            )

        except ParseError as e:
            self.errors.append(str(e))
            return ParseResult(
                success=False,
                data=None,
                errors=self.errors.copy(),
                warnings=self.warnings.copy(),
                position=e.position if hasattr(e, "position") else 0,
            )
        except Exception as e:
            self.errors.append(f"Unexpected error: {e}")
            return ParseResult(
                success=False,
                data=None,
                errors=self.errors.copy(),
                warnings=self.warnings.copy(),
            )

    def add_error(self, message: str, position: Optional[int] = None) -> None:
        """Add parsing error.

        Args:
            message: Error message
            position: Position in input where error occurred
        """
        if position is not None:
            message = f"{message} at position {position}"
        self.errors.append(message)

    def add_warning(self, message: str, position: Optional[int] = None) -> None:
        """Add parsing warning.

        Args:
            message: Warning message
            position: Position in input where warning occurred
        """
        if position is not None:
            message = f"{message} at position {position}"
        self.warnings.append(message)


class ParseError(Exception):
    """Base exception for parsing errors."""

    def __init__(self, message: str, position: Optional[int] = None):
        """Initialize parse error.

        Args:
            message: Error message
            position: Position in input
        """
        super().__init__(message)
        self.position = position


class TokenParser(BaseParser[List[Dict[str, Any]]]):
    """Base for token-based parsing.

    Common pattern for lexical analysis.
    """

    def __init__(self, strict: bool = False):
        """Initialize token parser."""
        super().__init__(strict)
        self.tokens = []
        self.position = 0

    @abstractmethod
    def tokenize(self, data: str) -> List[Dict[str, Any]]:
        """Convert input to tokens.

        Args:
            data: Input text

        Returns:
            List of tokens
        """
        pass

    def parse_impl(self, data: Union[str, bytes]) -> List[Dict[str, Any]]:
        """Parse by tokenizing first.

        Args:
            data: Input data

        Returns:
            Token list
        """
        if isinstance(data, bytes):
            data = data.decode("utf-8", errors="replace")

        self.tokens = self.tokenize(data)
        return self.tokens


class RecursiveDescentParser(BaseParser[Dict[str, Any]]):
    """Base for recursive descent parsing.

    Common pattern for grammar-based parsing.
    """

    def __init__(self, strict: bool = False):
        """Initialize recursive descent parser."""
        super().__init__(strict)
        self.input = ""
        self.position = 0
        self.length = 0

    def parse_impl(self, data: Union[str, bytes]) -> Dict[str, Any]:
        """Parse using recursive descent.

        Args:
            data: Input data

        Returns:
            Parse tree
        """
        if isinstance(data, bytes):
            data = data.decode("utf-8", errors="replace")

        self.input = data
        self.position = 0
        self.length = len(data)

        return self.parse_root()

    @abstractmethod
    def parse_root(self) -> Dict[str, Any]:
        """Parse from root rule.

        Returns:
            Parse tree
        """
        pass

    def peek(self, offset: int = 0) -> Optional[str]:
        """Peek at character without consuming.

        Args:
            offset: Offset from current position

        Returns:
            Character or None if at end
        """
        pos = self.position + offset
        if pos < self.length:
            return self.input[pos]
        return None

    def consume(self, count: int = 1) -> str:
        """Consume and return characters.

        Args:
            count: Number of characters

        Returns:
            Consumed string
        """
        result = self.input[self.position : self.position + count]
        self.position += len(result)
        return result

    def expect(self, expected: str) -> str:
        """Consume and verify expected string.

        Args:
            expected: Expected string

        Returns:
            Consumed string

        Raises:
            ParseError: If expectation not met
        """
        actual = self.consume(len(expected))
        if actual != expected:
            raise ParseError(
                f"Expected '{expected}' but got '{actual}'", self.position - len(actual)
            )
        return actual

    def skip_whitespace(self) -> None:
        """Skip whitespace characters."""
        while self.position < self.length and self.input[self.position].isspace():
            self.position += 1
