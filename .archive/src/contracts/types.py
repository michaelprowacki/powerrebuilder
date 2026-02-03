"""Shared types and protocols to prevent circular dependencies.

This module contains shared types, protocols, and enums that are used
across multiple modules but shouldn't be imported from concrete implementations
to avoid circular dependencies.
"""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import (
    Any,
    Protocol,
    TypeAlias,
    TypeVar,
    Generic,
    TypedDict,
    Union,
    NotRequired,
)
from collections.abc import AsyncIterator, Iterator, Callable
from collections import defaultdict

# ========== Type Aliases ==========

TaskID: TypeAlias = str
ProgressCallback: TypeAlias = Callable[[int, int, str], None]
# ConfigDict will be defined with TypedDict below for better type safety

# Basic value types that can appear in configurations
ConfigValue: TypeAlias = Union[
    str, int, float, bool, list["ConfigValue"], dict[str, "ConfigValue"], None
]

# JSON serializable types
JSONValue: TypeAlias = Union[
    str, int, float, bool, list["JSONValue"], dict[str, "JSONValue"], None
]

# ========== Enums ==========


class ProcessingMode(Enum):
    """Processing modes for coordinators."""

    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    STREAMING = "streaming"


class PipelineStage(Enum):
    """Pipeline stages."""

    EXTRACT = "extract"
    DECOMPILE = "decompile"
    PARSE = "parse"
    MODEL = "model"
    GENERATE = "generate"


class ObjectType(Enum):
    """PowerBuilder object types."""

    APPLICATION = "application"
    WINDOW = "window"
    MENU = "menu"
    DATAWINDOW = "datawindow"
    FUNCTION = "function"
    USEROBJECT = "userobject"
    STRUCTURE = "structure"
    GLOBAL_VARIABLE = "global_variable"
    UNKNOWN = "unknown"


# ========== TypedDict Definitions ==========


class FileStatsDict(TypedDict):
    """Statistics for file processing."""

    total: int
    successful: int
    failed: int
    in_progress: str | None


class EntriesStatsDict(TypedDict):
    """Statistics for entry processing."""

    total: int
    successful: int
    failed: int


class EntryTypeStatsDict(TypedDict):
    """Statistics for specific entry types."""

    total: int
    successful: int
    failed: int


class SizeStatsDict(TypedDict):
    """Statistics for file sizes."""

    total_bytes: int
    extracted_bytes: int
    largest_entry: int
    largest_entry_name: str
    smallest_entry: int
    smallest_entry_name: str


class TimingStatsDict(TypedDict):
    """Timing statistics."""

    start_time: float | None
    end_time: float | None
    total_duration: float
    file_durations: dict[str, float]


class ErrorInfoDict(TypedDict):
    """Error information structure."""

    file: str
    entry: NotRequired[str]
    error_type: str
    message: str
    timestamp: float


class ErrorStatsDict(TypedDict):
    """Error statistics."""

    total: int
    by_type: defaultdict[str, int]
    entries: list[ErrorInfoDict]


class RecoveryStrategyStatsDict(TypedDict):
    """Recovery strategy statistics."""

    attempts: int
    successful: int
    recovered: int


class RecoveryAttemptDict(TypedDict):
    """Recovery attempt information."""

    file: str | None
    strategy: str
    success: bool
    recovered_count: int
    timestamp: str


class RecoveryStatsDict(TypedDict):
    """Recovery statistics."""

    attempts: int
    successful: int
    total_recovered: int
    by_strategy: defaultdict[str, RecoveryStrategyStatsDict]
    history: list[RecoveryAttemptDict]


class FileDetailDict(TypedDict):
    """File processing details."""

    path: str
    name: str
    size: int
    start_time: str
    entries: list[dict[str, Any]]
    duration: float
    success: bool
    end_time: NotRequired[str]


class ExtractionStatsDict(TypedDict):
    """Complete extraction statistics structure."""

    files: FileStatsDict
    entries: EntriesStatsDict
    entry_types: defaultdict[str, EntryTypeStatsDict]
    sizes: SizeStatsDict
    timing: TimingStatsDict
    errors: ErrorStatsDict
    recovery: RecoveryStatsDict
    file_details: dict[str, FileDetailDict]


class PerformanceMetadataDict(TypedDict):
    """Performance measurement metadata."""

    cpu_count: NotRequired[int]
    memory_mb: NotRequired[int]
    platform: NotRequired[str]
    python_version: NotRequired[str]


class PerformanceStatsDict(TypedDict):
    """Performance statistics structure."""

    duration_seconds: float
    cpu_percent: NotRequired[float]
    memory_peak_mb: NotRequired[float]
    metadata: PerformanceMetadataDict


class StageStatsDict(TypedDict):
    """Statistics for a pipeline stage."""

    processed: int
    successful: int
    failed: int


class PipelineErrorSummaryDict(TypedDict):
    """Pipeline error summary."""

    errors: dict[str, int]
    warnings: dict[str, int]


class CachePerformanceDict(TypedDict):
    """Cache performance statistics."""

    total_hits: int
    total_misses: int
    overall_hit_rate: float


class PipelineStatsDict(TypedDict):
    """Complete pipeline statistics structure."""

    start_time: float | None
    end_time: float | None
    total_files: int
    successful: int
    failed: int
    stages: dict[str, StageStatsDict]
    error_summary: PipelineErrorSummaryDict
    duration_seconds: NotRequired[float]
    cache_statistics: NotRequired[dict[str, Any]]
    cache_performance: NotRequired[CachePerformanceDict]


class GeneratedFilesDict(TypedDict):
    """Generated files by category."""

    models: list[str]
    services: list[str]
    flutter: list[str]
    python: list[str]


class GenerationErrorDict(TypedDict):
    """Generation error information."""

    file: str
    error: str


class GenerationSummaryDict(TypedDict):
    """Generation process summary."""

    total_models: int
    successful_models: int
    failed_models: int
    generated_files: GeneratedFilesDict
    errors: list[GenerationErrorDict]


class ConfigDict(TypedDict, total=False):
    """Generic configuration dictionary with common fields."""

    enabled: bool
    timeout: int | float
    max_retries: int
    debug: bool
    cache_enabled: bool
    cache_size: int
    parallel_workers: int
    batch_size: int
    buffer_size: int
    output_format: str


class ResourceExtractionResultDict(TypedDict):
    """Result of extracting a single resource."""

    entry_name: str
    entry_type: str
    success: bool
    extracted_path: str | None
    error: str | None


class ResourceEntryDict(TypedDict):
    """Dictionary structure for resource entry data."""

    name: str
    type: str
    data: bytes | None
    size: NotRequired[int]
    offset: NotRequired[int]


class ParseStatsDict(TypedDict):
    """Parse operation statistics."""

    total_files: int
    successful: int
    failed: int
    errors: list[str]
    warnings: list[str]


class OrchestrationResultDict(TypedDict):
    """Result of extraction orchestration."""

    files: list[str]
    errors: list[str]
    statistics: ExtractionStatsDict


# ========== Generic Types ==========

T = TypeVar("T", contravariant=True)
TResult = TypeVar("TResult", covariant=True)
T_co = TypeVar("T_co", covariant=True)
T_contra = TypeVar("T_contra", contravariant=True)


# ========== Coordinator Protocols ==========


class ICoordinator(Protocol):
    """Base protocol for all coordinators."""

    @property
    def input_dir(self) -> Path | None:
        """Input directory."""
        ...

    @property
    def output_dir(self) -> Path | None:
        """Output directory."""
        ...

    def run(self) -> bool:
        """Execute the coordination process."""
        ...


class IAsyncCoordinator(Protocol):
    """Base protocol for async coordinators."""

    @property
    def input_dir(self) -> Path | None:
        """Input directory."""
        ...

    @property
    def output_dir(self) -> Path | None:
        """Output directory."""
        ...

    async def run_async(self) -> bool:
        """Execute the coordination process asynchronously."""
        ...


# ========== Processing Protocols ==========


class IProcessor(Protocol, Generic[T, TResult]):
    """Generic processor protocol."""

    def process(self, item: T) -> TResult:
        """Process an item."""
        ...


class IAsyncProcessor(Protocol, Generic[T, TResult]):
    """Generic async processor protocol."""

    async def process(self, item: T) -> TResult:
        """Process an item asynchronously."""
        ...


class IBatchProcessor(Protocol, Generic[T_contra, TResult]):
    """Protocol for batch processing."""

    def process_batch(self, items: list[T_contra]) -> list[TResult]:
        """Process a batch of items."""
        ...


# ========== Factory Protocols ==========


class IFactory(Protocol, Generic[T_co]):
    """Generic factory protocol."""

    def create(self, **kwargs: Any) -> T_co:
        """Create an instance."""
        ...


class ICoordinatorFactory(Protocol, Generic[T_co]):
    """Protocol for coordinator factories."""

    def create_simple(self, **kwargs: Any) -> T_co:
        """Create a simple coordinator instance."""
        ...

    def create_advanced(self, components: ConfigDict, **kwargs: Any) -> T_co:
        """Create an advanced coordinator with custom components."""
        ...

    def create_for_testing(self, mock_components: ConfigDict | None = None) -> T_co:
        """Create a coordinator for testing."""
        ...


# ========== Progress Tracking ==========


class IProgressTracker(Protocol):
    """Protocol for progress tracking."""

    def start_task(self, task_id: TaskID, description: str, total: int = 1) -> None:
        """Start tracking a task."""
        ...

    def update_task(self, task_id: TaskID, progress: int, message: str = "") -> None:
        """Update task progress."""
        ...

    def complete_task(self, task_id: TaskID, message: str = "") -> None:
        """Mark task as completed."""
        ...

    def fail_task(self, task_id: TaskID, error: str) -> None:
        """Mark task as failed."""
        ...


# ========== Content Processing ==========


class IContentExtractor(Protocol):
    """Protocol for content extraction."""

    def extract(self, file_path: Path) -> Any:
        """Extract content from a file."""
        ...


class IContentTransformer(Protocol, Generic[T_contra, TResult]):
    """Protocol for content transformation."""

    def transform(self, content: T_contra) -> TResult:
        """Transform content."""
        ...


class IContentValidator(Protocol, Generic[T_contra]):
    """Protocol for content validation."""

    def validate(self, content: T_contra) -> bool:
        """Validate content."""
        ...

    def get_errors(self) -> list[str]:
        """Get validation errors."""
        ...


# ========== Streaming Protocols ==========


class IStreamProcessor(Protocol, Generic[T_contra, TResult]):
    """Protocol for stream processing."""

    def process_stream(self, items: Iterator[T_contra]) -> Iterator[TResult]:
        """Process a stream of items."""
        ...


class IAsyncStreamProcessor(Protocol, Generic[T_contra, TResult]):
    """Protocol for async stream processing."""

    async def process_stream(
        self, items: AsyncIterator[T_contra]
    ) -> AsyncIterator[TResult]:
        """Process an async stream of items."""
        ...


# ========== Configuration ==========


class IConfigurable(Protocol):
    """Protocol for configurable components."""

    def configure(self, config: ConfigDict) -> None:
        """Configure the component."""
        ...

    def get_config(self) -> ConfigDict:
        """Get current configuration."""
        ...


# ========== Caching ==========


class ICacheable(Protocol):
    """Protocol for cacheable operations."""

    def get_cache_key(self, *args: Any, **kwargs: Any) -> str:
        """Generate cache key for operation."""
        ...

    def is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached result is still valid."""
        ...


# ========== Error Handling ==========


class IErrorHandler(Protocol):
    """Protocol for error handling."""

    def handle_error(self, error: Exception, context: ConfigDict | None = None) -> bool:
        """Handle an error. Return True if error was handled."""
        ...

    def can_recover(self, error: Exception) -> bool:
        """Check if error is recoverable."""
        ...


# ========== Resource Management ==========


class IResourceManager(Protocol):
    """Protocol for resource management."""

    def acquire_resource(self, resource_type: str, **kwargs: Any) -> Any:
        """Acquire a resource."""
        ...

    def release_resource(self, resource: Any) -> None:
        """Release a resource."""
        ...

    def cleanup_resources(self) -> None:
        """Cleanup all resources."""
        ...


# ========== Dependency Injection ==========


class IDependencyContainer(Protocol):
    """Protocol for dependency injection container."""

    def register(
        self, interface: type, implementation: type | object, singleton: bool = False
    ) -> None:
        """Register a dependency."""
        ...

    def resolve(self, interface: type) -> Any:
        """Resolve a dependency."""
        ...

    def is_registered(self, interface: type) -> bool:
        """Check if interface is registered."""
        ...
