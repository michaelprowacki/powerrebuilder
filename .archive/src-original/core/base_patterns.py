"""Base Patterns - Abstract common repeated patterns across the PowerRebuilder codebase.

This module provides abstract base classes and mixins that capture the most frequently
repeated patterns identified across 150+ instances in the codebase. These patterns
include:

1. BaseCoordinator - Abstract base for all coordinators with common functionality
2. ErrorHandlingMixin - Unified error handling patterns
3. ValidationMixin - Common validation patterns
4. BinaryOperationsMixin - Binary file operations
5. ConfigurableMixin - Configuration management
6. ProgressReportingMixin - Progress tracking patterns
7. ResourceManagementMixin - Resource lifecycle management

These abstractions follow the DRY principle and make it easy for existing classes
to inherit common functionality without duplication.
"""

from __future__ import annotations

import logging
import struct
import traceback
from abc import ABC, abstractmethod
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import (
    Any,
    BinaryIO,
    Callable,
    Dict,
    Iterator,
    List,
    Optional,
    Protocol,
    TypeVar,
    Union,
    runtime_checkable,
)

# Type variables
T = TypeVar("T")
ConfigDict = Dict[str, Any]
PathLike = Union[str, Path]

# ============================================================================
# CORE INTERFACES
# ============================================================================


@runtime_checkable
class ILogger(Protocol):
    """Logger protocol for type safety."""

    def debug(self, msg: str, *args: Any) -> None: ...
    def info(self, msg: str, *args: Any) -> None: ...
    def warning(self, msg: str, *args: Any) -> None: ...
    def error(self, msg: str, *args: Any) -> None: ...
    def exception(self, msg: str, *args: Any) -> None: ...


@runtime_checkable
class IValidator(Protocol):
    """Validator protocol."""

    def validate(self, data: Any) -> bool: ...


@runtime_checkable
class IProgressReporter(Protocol):
    """Progress reporting protocol."""

    def start_task(
        self, task_id: str, description: str, total: Optional[int] = None
    ) -> None: ...
    def update_task(self, task_id: str, advance: int = 1, **kwargs: Any) -> None: ...
    def complete_task(self, task_id: str) -> None: ...
    def fail_task(self, task_id: str, error: str) -> None: ...


# ============================================================================
# CONFIGURATION STRUCTURES
# ============================================================================


@dataclass
class BaseConfig:
    """Base configuration class with common settings."""

    cache_enabled: bool = True
    parallel_enabled: bool = False
    recovery_enabled: bool = True
    validate_inputs: bool = True
    validate_outputs: bool = True
    max_retries: int = 3
    timeout_seconds: Optional[int] = None
    log_level: str = "INFO"

    def merge(self, other: Dict[str, Any]) -> BaseConfig:
        """Merge configuration with dictionary values."""
        for key, value in other.items():
            if hasattr(self, key):
                setattr(self, key, value)
        return self


@dataclass
class BinaryConfig:
    """Configuration for binary operations."""

    use_mmap: bool = True
    buffer_size: int = 8192
    endianness: str = "little"
    encoding: str = "utf-8"
    validate_checksum: bool = True


# ============================================================================
# MIXINS FOR COMMON FUNCTIONALITY
# ============================================================================


class ErrorHandlingMixin:
    """Mixin providing standardized error handling patterns.

    This captures the most common error handling patterns found across
    the codebase including try/except/logging, recovery mechanisms,
    and error context management.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._error_count = 0
        self._max_errors = 10

    def handle_error(
        self,
        error: Exception,
        context: str = "",
        recoverable: bool = True,
        reraise: bool = True,
    ) -> bool:
        """Handle error with standard logging and recovery logic.

        Args:
            error: The exception that occurred
            context: Additional context information
            recoverable: Whether this error allows recovery
            reraise: Whether to re-raise the exception

        Returns:
            True if handled successfully, False otherwise
        """
        self._error_count += 1

        # Get logger from self if available
        logger = getattr(self, "logger", None) or logging.getLogger(__name__)

        error_msg = f"Error in {context}: {error}"
        logger.error(error_msg)

        # Log stack trace for debugging
        if hasattr(logger, "debug"):
            logger.debug(f"Stack trace: {traceback.format_exc()}")

        # Check if we've exceeded max errors
        if self._error_count >= self._max_errors:
            logger.critical(f"Maximum error count ({self._max_errors}) exceeded")
            if reraise:
                raise RuntimeError("Too many errors encountered") from error
            return False

        # Call recovery hook if available
        if recoverable and hasattr(self, "_attempt_recovery"):
            try:
                if self._attempt_recovery(error, context):
                    logger.info(f"Successfully recovered from error in {context}")
                    return True
            except Exception as recovery_error:
                logger.error(f"Recovery failed: {recovery_error}")

        if reraise:
            raise error
        return False

    @contextmanager
    def error_context(self, context: str, recoverable: bool = True):
        """Context manager for handling errors in a specific context.

        Args:
            context: Description of the operation context
            recoverable: Whether errors in this context are recoverable

        Example:
            with self.error_context("processing file"):
                # risky operations here
                process_file()
        """
        try:
            yield
        except Exception as e:
            self.handle_error(e, context, recoverable)

    def reset_error_count(self) -> None:
        """Reset the error counter."""
        self._error_count = 0


class ValidationMixin:
    """Mixin providing common validation patterns.

    Captures validation patterns for paths, inputs, outputs,
    and provides a framework for custom validation rules.
    """

    def validate_path(
        self, path: PathLike, must_exist: bool = True, must_be_file: bool = False
    ) -> bool:
        """Validate a filesystem path.

        Args:
            path: Path to validate
            must_exist: Whether path must exist
            must_be_file: Whether path must be a file (vs directory)

        Returns:
            True if valid

        Raises:
            ValueError: If validation fails
        """
        path_obj = Path(path) if isinstance(path, str) else path

        if must_exist and not path_obj.exists():
            raise ValueError(f"Path does not exist: {path_obj}")

        if must_exist and must_be_file and not path_obj.is_file():
            raise ValueError(f"Path is not a file: {path_obj}")

        if must_exist and not must_be_file and not path_obj.is_dir():
            raise ValueError(f"Path is not a directory: {path_obj}")

        return True

    def validate_input(
        self, data: Any, rules: Optional[List[Callable[[Any], bool]]] = None
    ) -> bool:
        """Validate input data against rules.

        Args:
            data: Data to validate
            rules: List of validation functions

        Returns:
            True if valid

        Raises:
            ValueError: If validation fails
        """
        if rules is None:
            rules = []

        # Basic non-None check
        if data is None:
            raise ValueError("Input data cannot be None")

        # Apply custom rules
        for rule in rules:
            if not rule(data):
                raise ValueError(f"Validation rule failed for data: {data}")

        return True

    def validate_output(self, data: Any, expected_type: Optional[type] = None) -> bool:
        """Validate output data.

        Args:
            data: Output data to validate
            expected_type: Expected data type

        Returns:
            True if valid

        Raises:
            ValueError: If validation fails
        """
        if expected_type and not isinstance(data, expected_type):
            raise ValueError(
                f"Output data has wrong type. Expected {expected_type}, got {type(data)}"
            )

        return True


class BinaryOperationsMixin:
    """Mixin for common binary file operations.

    Provides safe binary reading, parsing helpers, endianness handling,
    and other common binary operations found throughout the codebase.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._binary_config = BinaryConfig()

    def read_binary_file(self, path: PathLike) -> bytes:
        """Safely read binary file with error handling.

        Args:
            path: Path to binary file

        Returns:
            File contents as bytes
        """
        with self.error_context(f"reading binary file {path}"):
            path_obj = Path(path)
            self.validate_path(path_obj, must_exist=True, must_be_file=True)

            return path_obj.read_bytes()

    def read_struct_from_bytes(
        self, data: bytes, offset: int, format_str: str
    ) -> tuple:
        """Read structured data from bytes with endianness handling.

        Args:
            data: Byte data
            offset: Starting offset
            format_str: Struct format string

        Returns:
            Unpacked struct data
        """
        endian = "<" if self._binary_config.endianness == "little" else ">"
        full_format = endian + format_str
        size = struct.calcsize(full_format)

        if offset + size > len(data):
            raise ValueError(f"Not enough data to read struct at offset {offset}")

        chunk = data[offset : offset + size]
        return struct.unpack(full_format, chunk)

    def write_binary_file(
        self, path: PathLike, data: bytes, create_dirs: bool = True
    ) -> None:
        """Safely write binary file.

        Args:
            path: Output file path
            data: Data to write
            create_dirs: Whether to create parent directories
        """
        with self.error_context(f"writing binary file {path}"):
            path_obj = Path(path)

            if create_dirs:
                path_obj.parent.mkdir(parents=True, exist_ok=True)

            path_obj.write_bytes(data)

    def calculate_checksum(self, data: bytes, algorithm: str = "crc32") -> int:
        """Calculate checksum for binary data.

        Args:
            data: Binary data
            algorithm: Checksum algorithm (crc32, etc)

        Returns:
            Checksum value
        """
        if algorithm == "crc32":
            import zlib

            return zlib.crc32(data) & 0xFFFFFFFF
        else:
            raise ValueError(f"Unsupported checksum algorithm: {algorithm}")


class ConfigurableMixin:
    """Mixin for configuration management patterns.

    Provides config loading, validation, default values,
    and configuration merging capabilities.
    """

    def __init__(
        self, *args, config: Optional[Union[ConfigDict, BaseConfig]] = None, **kwargs
    ):
        super().__init__(*args, **kwargs)
        self._config = self._load_config(config)

    def _load_config(
        self, config: Optional[Union[ConfigDict, BaseConfig]]
    ) -> BaseConfig:
        """Load and validate configuration.

        Args:
            config: Configuration data

        Returns:
            Validated configuration object
        """
        if config is None:
            return BaseConfig()
        elif isinstance(config, dict):
            return BaseConfig().merge(config)
        elif isinstance(config, BaseConfig):
            return config
        else:
            raise ValueError(f"Invalid config type: {type(config)}")

    def get_config_value(self, key: str, default: Any = None) -> Any:
        """Get configuration value with default.

        Args:
            key: Configuration key
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        return getattr(self._config, key, default)

    def update_config(self, updates: ConfigDict) -> None:
        """Update configuration with new values.

        Args:
            updates: Dictionary of updates to apply
        """
        self._config.merge(updates)


class ProgressReportingMixin:
    """Mixin for progress reporting patterns.

    Provides standardized progress tracking, task management,
    and reporting capabilities.
    """

    def __init__(
        self, *args, progress_reporter: Optional[IProgressReporter] = None, **kwargs
    ):
        super().__init__(*args, **kwargs)
        self._progress_reporter = progress_reporter
        self._active_tasks: Dict[str, bool] = {}

    def start_progress(
        self, task_id: str, description: str, total: Optional[int] = None
    ) -> None:
        """Start progress tracking for a task.

        Args:
            task_id: Unique task identifier
            description: Human-readable description
            total: Total steps (None for indeterminate)
        """
        if self._progress_reporter:
            self._progress_reporter.start_task(task_id, description, total)
        self._active_tasks[task_id] = True

        # Log start if we have a logger
        logger = getattr(self, "logger", None)
        if logger:
            logger.info(f"Started task: {description}")

    def update_progress(self, task_id: str, advance: int = 1, **kwargs) -> None:
        """Update progress for a task.

        Args:
            task_id: Task identifier
            advance: Steps to advance
            **kwargs: Additional progress data
        """
        if task_id in self._active_tasks and self._progress_reporter:
            self._progress_reporter.update_task(task_id, advance, **kwargs)

    def complete_progress(self, task_id: str) -> None:
        """Complete progress tracking for a task.

        Args:
            task_id: Task identifier
        """
        if task_id in self._active_tasks:
            if self._progress_reporter:
                self._progress_reporter.complete_task(task_id)
            del self._active_tasks[task_id]

            # Log completion
            logger = getattr(self, "logger", None)
            if logger:
                logger.info(f"Completed task: {task_id}")

    def fail_progress(self, task_id: str, error: str) -> None:
        """Mark task progress as failed.

        Args:
            task_id: Task identifier
            error: Error description
        """
        if task_id in self._active_tasks:
            if self._progress_reporter:
                self._progress_reporter.fail_task(task_id, error)
            del self._active_tasks[task_id]

            # Log failure
            logger = getattr(self, "logger", None)
            if logger:
                logger.error(f"Failed task {task_id}: {error}")

    @contextmanager
    def progress_context(
        self, task_id: str, description: str, total: Optional[int] = None
    ):
        """Context manager for progress tracking.

        Args:
            task_id: Task identifier
            description: Task description
            total: Total steps

        Yields:
            Update function
        """
        self.start_progress(task_id, description, total)

        def update_func(advance: int = 1, **kwargs):
            self.update_progress(task_id, advance, **kwargs)

        try:
            yield update_func
            self.complete_progress(task_id)
        except Exception as e:
            self.fail_progress(task_id, str(e))
            raise


class ResourceManagementMixin:
    """Mixin for resource lifecycle management patterns.

    Provides context managers for resource cleanup, file handle management,
    and other resource lifecycle patterns.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._managed_resources: List[Any] = []

    def add_managed_resource(self, resource: Any) -> None:
        """Add a resource to be managed.

        Args:
            resource: Resource to manage (must have close() method)
        """
        self._managed_resources.append(resource)

    def cleanup_resources(self) -> None:
        """Clean up all managed resources."""
        for resource in self._managed_resources:
            try:
                if hasattr(resource, "close"):
                    resource.close()
                elif hasattr(resource, "__exit__"):
                    resource.__exit__(None, None, None)
            except Exception as e:
                # Log but don't raise - cleanup should be best effort
                logger = getattr(self, "logger", None)
                if logger:
                    logger.warning(f"Failed to cleanup resource: {e}")

        self._managed_resources.clear()

    @contextmanager
    def managed_file(self, path: PathLike, mode: str = "rb") -> Iterator[BinaryIO]:
        """Context manager for file operations with automatic cleanup.

        Args:
            path: File path
            mode: File open mode

        Yields:
            File handle
        """
        file_handle = None
        try:
            file_handle = open(path, mode)
            self.add_managed_resource(file_handle)
            yield file_handle
        finally:
            if file_handle:
                try:
                    file_handle.close()
                except Exception:
                    pass  # Best effort cleanup

    def __del__(self):
        """Destructor to ensure resource cleanup."""
        self.cleanup_resources()


# ============================================================================
# ABSTRACT BASE COORDINATOR
# ============================================================================


class BaseCoordinator(
    ABC,
    ErrorHandlingMixin,
    ValidationMixin,
    ConfigurableMixin,
    ProgressReportingMixin,
    ResourceManagementMixin,
):
    """Abstract base class for all coordinators in the PowerRebuilder pipeline.

    This class provides the common functionality that all coordinators need:
    - Configuration management
    - Logger initialization
    - Error handling with recovery
    - Progress reporting
    - File I/O operations
    - Resource management
    - Input/output validation

    Subclasses must implement the abstract methods to define their specific
    processing logic while inheriting all the common functionality.
    """

    def __init__(
        self,
        input_path: PathLike,
        output_path: PathLike,
        logger: Optional[ILogger] = None,
        config: Optional[Union[ConfigDict, BaseConfig]] = None,
        progress_reporter: Optional[IProgressReporter] = None,
        **kwargs,
    ):
        """Initialize base coordinator.

        Args:
            input_path: Input file or directory path
            output_path: Output file or directory path
            logger: Logger instance
            config: Configuration object or dict
            progress_reporter: Progress reporter instance
            **kwargs: Additional configuration
        """
        # Initialize all mixins
        super().__init__(config=config, progress_reporter=progress_reporter, **kwargs)

        # Core coordinator properties
        self.input_path = Path(input_path)
        self.output_path = Path(output_path)
        self.logger = logger or logging.getLogger(self.__class__.__name__)

        # Validate paths
        self.validate_path(self.input_path, must_exist=True)

        # Ensure output directory exists
        if self.output_path.suffix:  # It's a file
            self.output_path.parent.mkdir(parents=True, exist_ok=True)
        else:  # It's a directory
            self.output_path.mkdir(parents=True, exist_ok=True)

        # Initialize state
        self._initialized = False
        self._processing = False
        self._completed = False

        self.logger.info(f"Initialized {self.__class__.__name__}")
        self.logger.debug(f"Input: {self.input_path}")
        self.logger.debug(f"Output: {self.output_path}")

    @abstractmethod
    def process(self) -> Any:
        """Process the input and produce output.

        This is the main method that subclasses must implement to define
        their specific processing logic.

        Returns:
            Processing result
        """
        pass

    @abstractmethod
    def validate_inputs(self) -> bool:
        """Validate input data/files.

        Returns:
            True if inputs are valid

        Raises:
            ValueError: If validation fails
        """
        pass

    @abstractmethod
    def validate_outputs(self, result: Any) -> bool:
        """Validate output data/files.

        Args:
            result: Processing result to validate

        Returns:
            True if outputs are valid

        Raises:
            ValueError: If validation fails
        """
        pass

    def initialize(self) -> None:
        """Initialize the coordinator (hook for subclasses)."""
        if not self._initialized:
            self._initialized = True
            self.logger.debug("Coordinator initialized")

    def execute(self) -> Any:
        """Execute the complete processing pipeline with error handling.

        This method orchestrates the full pipeline:
        1. Initialize
        2. Validate inputs
        3. Process
        4. Validate outputs
        5. Cleanup

        Returns:
            Processing result
        """
        task_id = f"{self.__class__.__name__}_execute"

        with self.progress_context(task_id, f"Executing {self.__class__.__name__}"):
            try:
                # Initialize
                self.initialize()

                # Validate inputs
                if self.get_config_value("validate_inputs", True):
                    with self.error_context("input validation"):
                        self.validate_inputs()

                # Set processing flag
                self._processing = True

                # Main processing
                with self.error_context("main processing"):
                    result = self.process()

                # Validate outputs
                if self.get_config_value("validate_outputs", True):
                    with self.error_context("output validation"):
                        self.validate_outputs(result)

                # Mark as completed
                self._completed = True
                self.logger.info(f"Successfully completed {self.__class__.__name__}")

                return result

            except Exception as e:
                self.logger.error(f"Failed to execute {self.__class__.__name__}: {e}")
                raise
            finally:
                # Cleanup resources
                self._processing = False
                self.cleanup_resources()

    def _attempt_recovery(self, error: Exception, context: str) -> bool:
        """Attempt recovery from an error (hook for subclasses).

        Args:
            error: The exception that occurred
            context: Error context

        Returns:
            True if recovery was successful
        """
        # Base implementation does no recovery
        return False

    @property
    def is_initialized(self) -> bool:
        """Check if coordinator is initialized."""
        return self._initialized

    @property
    def is_processing(self) -> bool:
        """Check if coordinator is currently processing."""
        return self._processing

    @property
    def is_completed(self) -> bool:
        """Check if processing is completed."""
        return self._completed


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    # Interfaces
    "ILogger",
    "IValidator",
    "IProgressReporter",
    # Configuration
    "BaseConfig",
    "BinaryConfig",
    "ConfigDict",
    "PathLike",
    # Mixins
    "ErrorHandlingMixin",
    "ValidationMixin",
    "BinaryOperationsMixin",
    "ConfigurableMixin",
    "ProgressReportingMixin",
    "ResourceManagementMixin",
    # Base Classes
    "BaseCoordinator",
]
