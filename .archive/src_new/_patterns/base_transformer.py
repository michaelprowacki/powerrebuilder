"""Base Transformer Pattern - Abstract base for data transformation.

Common pattern for transforming data between formats, used extensively in:
- Decompile: P-code bytes → PowerBuilder source
- Parse: Source text → AST
- Model: AST → Semantic models
- Generate: Models → Target language code
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

# Type variables for input and output types
TInput = TypeVar("TInput")
TOutput = TypeVar("TOutput")


class BaseTransformer(ABC, Generic[TInput, TOutput]):
    """Abstract base for all data transformers.

    This pattern is found throughout the pipeline where data
    needs to be converted from one format to another.
    """

    @abstractmethod
    def transform(self, input_data: TInput) -> TOutput:
        """Transform input data to output format.

        Args:
            input_data: Data to transform

        Returns:
            Transformed data
        """
        pass

    def validate_input(self, input_data: TInput) -> bool:
        """Validate input before transformation.

        Args:
            input_data: Data to validate

        Returns:
            True if valid

        Raises:
            ValueError: If validation fails
        """
        if input_data is None:
            raise ValueError("Input data cannot be None")
        return True

    def validate_output(self, output_data: TOutput) -> bool:
        """Validate output after transformation.

        Args:
            output_data: Data to validate

        Returns:
            True if valid

        Raises:
            ValueError: If validation fails
        """
        if output_data is None:
            raise ValueError("Output data cannot be None")
        return True

    def process(self, input_data: TInput) -> TOutput:
        """Process with validation.

        Args:
            input_data: Data to transform

        Returns:
            Transformed data
        """
        self.validate_input(input_data)
        output_data = self.transform(input_data)
        self.validate_output(output_data)
        return output_data


class ChainedTransformer(BaseTransformer[TInput, TOutput]):
    """Chains multiple transformers together.

    Useful for multi-step transformations found in complex stages.
    """

    def __init__(self, transformers: list[BaseTransformer]):
        """Initialize with list of transformers.

        Args:
            transformers: Ordered list of transformers to apply
        """
        self.transformers = transformers

    def transform(self, input_data: TInput) -> TOutput:
        """Apply all transformers in sequence.

        Args:
            input_data: Initial input

        Returns:
            Final transformed output
        """
        result = input_data
        for transformer in self.transformers:
            result = transformer.transform(result)
        return result


class ConditionalTransformer(BaseTransformer[TInput, TOutput]):
    """Transformer that applies different logic based on conditions.

    Common pattern for handling different file types or versions.
    """

    def __init__(self, default_transformer: BaseTransformer):
        """Initialize with default transformer.

        Args:
            default_transformer: Transformer to use by default
        """
        self.default_transformer = default_transformer
        self.conditions = []

    def add_condition(self, condition: callable, transformer: BaseTransformer) -> None:
        """Add a conditional transformer.

        Args:
            condition: Function that returns True when this transformer should be used
            transformer: Transformer to use when condition is met
        """
        self.conditions.append((condition, transformer))

    def transform(self, input_data: TInput) -> TOutput:
        """Apply appropriate transformer based on conditions.

        Args:
            input_data: Data to transform

        Returns:
            Transformed data
        """
        for condition, transformer in self.conditions:
            if condition(input_data):
                return transformer.transform(input_data)

        return self.default_transformer.transform(input_data)


class CachingTransformer(BaseTransformer[TInput, TOutput]):
    """Transformer that caches results for repeated inputs.

    Useful for expensive transformations that may be repeated.
    """

    def __init__(self, transformer: BaseTransformer, cache_size: int = 100):
        """Initialize with base transformer and cache.

        Args:
            transformer: Base transformer to wrap
            cache_size: Maximum cache entries
        """
        self.transformer = transformer
        self.cache_size = cache_size
        self._cache = {}

    def transform(self, input_data: TInput) -> TOutput:
        """Transform with caching.

        Args:
            input_data: Data to transform

        Returns:
            Transformed data (from cache if available)
        """
        # Create cache key (assumes input is hashable)
        cache_key = self._make_cache_key(input_data)

        if cache_key in self._cache:
            return self._cache[cache_key]

        # Transform and cache
        result = self.transformer.transform(input_data)

        # Limit cache size
        if len(self._cache) >= self.cache_size:
            # Remove oldest entry (simple FIFO)
            self._cache.pop(next(iter(self._cache)))

        self._cache[cache_key] = result
        return result

    def _make_cache_key(self, input_data: TInput) -> str:
        """Create cache key from input data.

        Args:
            input_data: Input to create key from

        Returns:
            Cache key string
        """
        # Simple string representation
        # Override for complex types
        return str(input_data)

    def clear_cache(self) -> None:
        """Clear the cache."""
        self._cache.clear()
