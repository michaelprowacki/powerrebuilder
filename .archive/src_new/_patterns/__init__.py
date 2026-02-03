"""Reusable patterns and abstractions for DRY code.

This package contains all the common patterns extracted from the codebase
to eliminate duplication and ensure consistency.
"""

from .base_coordinator import BaseCoordinator, CoordinatorResult
from .base_parser import BaseParser, ParseError, ParseResult
from .base_transformer import (
    BaseTransformer,
    CachingTransformer,
    ChainedTransformer,
    ConditionalTransformer,
)
from .binary_reader import BinaryHeader, BinaryReader
from .file_handler import FileHandler
from .mixins import (
    BaseConfig,
    ConfigurableMixin,
    ErrorHandlingMixin,
    ProgressReportingMixin,
    ValidationMixin,
)
from .pipeline import Pipeline, PipelineResult, StageConnector, StageResult

# Import new patterns conditionally
try:
    from .cache import Cache, MemoryCache, DiskCache, HybridCache
    from .parallel import ParallelExecutor, ExecutorType, BatchResult
    from .progress import RichProgress, ProgressTracker, RichLogger
    from .observability import (
        ObservabilityManager,
        PipelineTracer,
        MetricsCollector,
        initialize_observability,
    )
    from .incremental import (
        IncrementalTracker,
        IncrementalProcessor,
        ChangeSet,
        FileState,
    )

    _new_patterns = True
except ImportError:
    _new_patterns = False

__all__ = [
    # Coordinators
    "BaseCoordinator",
    "CoordinatorResult",
    # Parsers
    "BaseParser",
    "ParseError",
    "ParseResult",
    # Transformers
    "BaseTransformer",
    "ChainedTransformer",
    "ConditionalTransformer",
    "CachingTransformer",
    # Binary operations
    "BinaryReader",
    "BinaryHeader",
    # File operations
    "FileHandler",
    # Mixins
    "ErrorHandlingMixin",
    "ValidationMixin",
    "ConfigurableMixin",
    "ProgressReportingMixin",
    "BaseConfig",
    # Pipeline
    "Pipeline",
    "PipelineResult",
    "StageResult",
    "StageConnector",
]

if _new_patterns:
    __all__.extend(
        [
            # Caching
            "Cache",
            "MemoryCache",
            "DiskCache",
            "HybridCache",
            # Parallel processing
            "ParallelExecutor",
            "ExecutorType",
            "BatchResult",
            # Progress tracking
            "RichProgress",
            "ProgressTracker",
            "RichLogger",
            # Observability
            "ObservabilityManager",
            "PipelineTracer",
            "MetricsCollector",
            "initialize_observability",
            # Incremental processing
            "IncrementalTracker",
            "IncrementalProcessor",
            "ChangeSet",
            "FileState",
        ]
    )
