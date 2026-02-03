"""Consolidated interfaces for all PowerRebuilder components.

This module combines all interfaces and protocols from the contracts module
to provide a single source of truth for dependency injection and testability.
"""

from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Protocol

from lark import Tree

# Import shared types to avoid circular dependencies
from .types import (
    ExtractionStatsDict,
    PipelineStage as SharedPipelineStage,
)

# ========== Logger Interfaces ==========


class ILogger(ABC):
    """Interface for logging operations."""

    @abstractmethod
    def debug(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """Log a debug message."""

    @abstractmethod
    def info(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """Log an info message."""

    @abstractmethod
    def warning(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """Log a warning message."""

    @abstractmethod
    def error(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """Log an error message."""

    @abstractmethod
    def critical(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """Log a critical message."""

    @abstractmethod
    def exception(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """Log an exception with traceback."""

    @abstractmethod
    def set_context(self, **kwargs: Any) -> None:
        """Set persistent context fields for all subsequent logs."""

    @abstractmethod
    def clear_context(self) -> None:
        """Clear all context fields."""


# ========== Event Interfaces ==========


class EventType(Enum):
    """Event types."""

    STAGE_STARTED = "stage_started"
    STAGE_COMPLETED = "stage_completed"
    STAGE_FAILED = "stage_failed"
    FILE_PROCESSED = "file_processed"
    ERROR_OCCURRED = "error_occurred"
    WARNING_RAISED = "warning_raised"
    PROGRESS_UPDATE = "progress_update"


@dataclass
class Event:
    """Base event class."""

    type: EventType
    source: str
    timestamp: datetime = field(default_factory=datetime.now)
    data: dict[str, Any] = field(default_factory=dict)


class IEventHandler(Protocol):
    """Interface for event handlers."""

    def handle(self, event: Event) -> None:
        """Handle an event."""
        ...

    def can_handle(self, event_type: EventType) -> bool:
        """Check if handler can handle event type."""
        ...


class IEventBus(Protocol):
    """Interface for event bus."""

    def publish(self, event: Event) -> None:
        """Publish an event."""
        ...

    def subscribe(self, event_type: EventType, handler: IEventHandler) -> None:
        """Subscribe to an event type."""
        ...

    def unsubscribe(self, event_type: EventType, handler: IEventHandler) -> None:
        """Unsubscribe from an event type."""
        ...

    def get_handlers(self, event_type: EventType) -> list[IEventHandler]:
        """Get all handlers for an event type."""
        ...


# ========== Pipeline Interfaces ==========

# Use shared pipeline stage enum
PipelineStage = SharedPipelineStage


class StageStatus(Enum):
    """Stage execution status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class IPipelineStage(Protocol):
    """Interface for pipeline stages."""

    @abstractmethod
    def execute(
        self, input_dir: Path, output_dir: Path, context: dict[str, Any]
    ) -> dict[str, Any]:
        """Execute the pipeline stage."""
        ...

    @abstractmethod
    def get_name(self) -> str:
        """Get stage name."""
        ...

    @abstractmethod
    def get_dependencies(self) -> list[str]:
        """Get stage dependencies."""
        ...


class IPipelineCoordinator(Protocol):
    """Interface for pipeline coordinator."""

    @abstractmethod
    def run(
        self, input_dir: Path, output_dir: Path, stages: list[str] | None = None
    ) -> dict[str, Any]:
        """Run the pipeline."""
        ...

    @abstractmethod
    def register_stage(self, stage: IPipelineStage) -> None:
        """Register a pipeline stage."""
        ...

    @abstractmethod
    def get_stages(self) -> dict[str, IPipelineStage]:
        """Get registered stages."""
        ...

    @abstractmethod
    def get_stage(self, name: str) -> IPipelineStage | None:
        """Get a specific stage by name."""
        ...

    @abstractmethod
    def validate_pipeline(self) -> bool:
        """Validate pipeline configuration."""
        ...


class IPipelineState(Protocol):
    """Interface for pipeline state."""

    @abstractmethod
    def get_stage_status(self, stage: str) -> StageStatus:
        """Get status of a stage."""
        ...

    @abstractmethod
    def set_stage_status(self, stage: str, status: StageStatus) -> None:
        """Set status of a stage."""
        ...

    @abstractmethod
    def get_stage_result(self, stage: str) -> dict[str, Any] | None:
        """Get result of a stage."""
        ...

    @abstractmethod
    def set_stage_result(self, stage: str, result: dict[str, Any]) -> None:
        """Set result of a stage."""
        ...

    @abstractmethod
    def get_context(self) -> dict[str, Any]:
        """Get pipeline context."""
        ...

    @abstractmethod
    def update_context(self, updates: dict[str, Any]) -> None:
        """Update pipeline context."""
        ...

    @abstractmethod
    def get_start_time(self) -> datetime | None:
        """Get pipeline start time."""
        ...

    @abstractmethod
    def get_end_time(self) -> datetime | None:
        """Get pipeline end time."""
        ...


class IStateManager(Protocol):
    """Interface for state management."""

    @abstractmethod
    def create_state(self) -> IPipelineState:
        """Create a new pipeline state."""
        ...

    @abstractmethod
    def save_state(self, state: IPipelineState, path: Path) -> None:
        """Save state to disk."""
        ...

    @abstractmethod
    def load_state(self, path: Path) -> IPipelineState:
        """Load state from disk."""
        ...

    @abstractmethod
    def create_checkpoint(self, state: IPipelineState, stage: str) -> str:
        """Create a checkpoint for rollback."""
        ...

    @abstractmethod
    def rollback(self, state: IPipelineState, checkpoint_id: str) -> IPipelineState:
        """Rollback to a checkpoint."""
        ...


# ========== Decompiler Interfaces ==========


class IObjectTypeDetector(Protocol):
    """Interface for object type detection."""

    @staticmethod
    def get_object_info(object_name: str) -> tuple[str, bool]:
        """Get object type and whether it's a standard object.

        Args:
            object_name: Name of the object

        Returns:
            Tuple of (object_type, is_standard_object)
        """
        ...

    @staticmethod
    def get_object_type(object_name: str) -> str:
        """Get the type of the object from its name.

        Args:
            object_name: Name of the object

        Returns:
            Object type string
        """
        ...


class IPCodeDecoder(Protocol):
    """Interface for P-code decoding."""

    def decode_pcode_section(
        self, data: bytes, object_name: str, pcode_info: dict[str, Any] | None = None
    ) -> Any:
        """Decode P-code section.

        Args:
            data: P-code binary data
            object_name: Name of the object being decoded
            pcode_info: Optional P-code metadata

        Returns:
            Decoded P-code structure
        """
        ...

    def get_version(self) -> str:
        """Get decoder version."""
        ...


class IControlFlowAnalyzer(Protocol):
    """Interface for control flow analysis."""

    def analyze(self, instructions: list[Any]) -> dict[str, Any]:
        """Analyze control flow of instructions.

        Args:
            instructions: List of decoded instructions

        Returns:
            Control flow analysis results
        """
        ...

    def build_cfg(self, instructions: list[Any]) -> Any:
        """Build control flow graph.

        Args:
            instructions: List of decoded instructions

        Returns:
            Control flow graph
        """
        ...


class IExpressionReconstructor(Protocol):
    """Interface for expression reconstruction."""

    def reconstruct(self, instructions: list[Any]) -> str:
        """Reconstruct expressions from instructions.

        Args:
            instructions: List of decoded instructions

        Returns:
            Reconstructed PowerBuilder source code
        """
        ...

    def reconstruct_expression(self, expr_instructions: list[Any]) -> str:
        """Reconstruct a single expression.

        Args:
            expr_instructions: Instructions for one expression

        Returns:
            Reconstructed expression string
        """
        ...


class IOutputFormatter(Protocol):
    """Interface for output formatting."""

    def format_source(
        self, object_type: str, object_name: str, decompiled_content: str
    ) -> str:
        """Format decompiled source code.

        Args:
            object_type: Type of the object
            object_name: Name of the object
            decompiled_content: Decompiled content

        Returns:
            Formatted PowerBuilder source code
        """
        ...


class IOutputValidator(Protocol):
    """Interface for output validation."""

    def validate(self, content: str, object_type: str) -> bool:
        """Validate decompiled output.

        Args:
            content: Decompiled content
            object_type: Type of the object

        Returns:
            True if valid, False otherwise
        """
        ...

    def get_validation_errors(self) -> list[str]:
        """Get validation errors from last validation.

        Returns:
            List of validation error messages
        """
        ...


class IVersionDetector(Protocol):
    """Interface for PowerBuilder version detection."""

    def detect_version(self, data: bytes) -> str:
        """Detect PowerBuilder version from data.

        Args:
            data: Binary data to analyze

        Returns:
            Version string
        """
        ...


# Keep existing interfaces for compatibility
class IDecompiler(Protocol):
    """Interface for all decompilers."""

    @abstractmethod
    def decompile(self, bytecode: bytes, context: dict[str, Any] | None = None) -> str:
        """Decompile bytecode to source code."""
        ...

    @abstractmethod
    def supports(self, bytecode: bytes) -> bool:
        """Check if this decompiler supports the given bytecode."""
        ...


class IDecompilerCoordinator(Protocol):
    """Interface for decompile coordinator."""

    @abstractmethod
    def decompile(self, input_dir: Path, output_dir: Path) -> dict[str, Any]:
        """Coordinate decompilation process."""
        ...

    @abstractmethod
    def decompile_file(self, file_path: Path) -> str:
        """Decompile a single file."""
        ...

    @abstractmethod
    def register_decompiler(self, decompiler: IDecompiler) -> None:
        """Register a new decompiler."""
        ...

    @abstractmethod
    def get_decompilers(self) -> list[IDecompiler]:
        """Get all registered decompilers."""
        ...


# ========== Extractor Interfaces ==========


class IExtractOrchestrator(ABC):
    """Interface for high-level extraction orchestration."""

    @abstractmethod
    def orchestrate_extraction(
        self,
        input_path: Path,
        output_dir: Path,
        enable_byte_recovery: bool = False,
        extract_resources: bool = True,
        show_progress: bool = True,
    ) -> dict[str, Any]:
        """Orchestrate the complete extraction process.

        Args:
            input_path: Input PBL/PBD file or directory
            output_dir: Output directory for extracted files
            enable_byte_recovery: Enable byte-level recovery for corrupted files
            extract_resources: Extract embedded resources
            show_progress: Show progress information

        Returns:
            Dictionary with extraction statistics
        """

    @abstractmethod
    def process_single_file(self, file_path: Path, output_dir: Path) -> bool:
        """Process a single PBL/PBD file.

        Args:
            file_path: Path to PBL/PBD file
            output_dir: Output directory

        Returns:
            True if successful, False otherwise
        """


class IBinaryFileParser(ABC):
    """Interface for parsing PowerBuilder binary files."""

    @abstractmethod
    def parse_header(self, file_path: Path) -> dict[str, Any]:
        """Parse file header to determine format and metadata.

        Args:
            file_path: Path to binary file

        Returns:
            Dictionary with header information
        """

    @abstractmethod
    def parse_structure(self, file_path: Path) -> list[dict[str, Any]]:
        """Parse the complete file structure.

        Args:
            file_path: Path to binary file

        Returns:
            List of file entries with metadata
        """

    @abstractmethod
    def extract_entry(
        self, file_path: Path, entry_info: dict[str, Any], output_path: Path
    ) -> bool:
        """Extract a single entry from the binary file.

        Args:
            file_path: Path to binary file
            entry_info: Entry metadata from parse_structure
            output_path: Output file path

        Returns:
            True if successful, False otherwise
        """


class IResourceExtractor(ABC):
    """Interface for extracting resources from PowerBuilder files."""

    @abstractmethod
    def extract_resources(
        self,
        file_path: Path,
        output_dir: Path,
        resource_types: list[str] | None = None,
    ) -> dict[str, list[Path]]:
        """Extract resources from a PowerBuilder file.

        Args:
            file_path: Path to PBL/PBD file
            output_dir: Output directory for resources
            resource_types: Optional list of resource types to extract

        Returns:
            Dictionary mapping resource type to list of extracted file paths
        """

    @abstractmethod
    def identify_resource_type(self, data: bytes) -> str | None:
        """Identify the type of a resource from its data.

        Args:
            data: Resource data bytes

        Returns:
            Resource type string or None if unknown
        """

    @abstractmethod
    def extract_resource(
        self, entry: dict[str, Any], output_dir: Path
    ) -> dict[str, Any]:
        """Extract a single resource from an entry.

        Args:
            entry: Entry dictionary with metadata
            output_dir: Output directory for the resource

        Returns:
            Dictionary with extraction result
        """


class IRecoveryEngine(ABC):
    """Interface for recovery strategies for corrupted files."""

    @abstractmethod
    def attempt_recovery(
        self, file_path: Path, output_dir: Path, strategies: list[str] | None = None
    ) -> dict[str, Any]:
        """Attempt to recover data from a corrupted file.

        Args:
            file_path: Path to corrupted file
            output_dir: Output directory for recovered data
            strategies: Optional list of recovery strategies to try

        Returns:
            Dictionary with recovery results and statistics
        """

    @abstractmethod
    def scan_for_signatures(
        self, data: bytes, signatures: dict[str, bytes] | None = None
    ) -> list[dict[str, Any]]:
        """Scan data for known block signatures.

        Args:
            data: File data to scan
            signatures: Optional custom signatures to search for

        Returns:
            List of found blocks with offset and type information
        """

    @abstractmethod
    def attempt_entry_recovery(
        self, entry: dict[str, Any], output_dir: Path
    ) -> dict[str, Any] | None:
        """Attempt to recover data from a corrupted entry.

        Args:
            entry: Entry dictionary with metadata
            output_dir: Output directory for recovered data

        Returns:
            Recovery result dictionary or None if recovery failed
        """


class IExtractionValidator(ABC):
    """Interface for validating extraction inputs and outputs."""

    @abstractmethod
    def validate_input_file(self, file_path: Path) -> bool:
        """Validate that input file is a valid PBL/PBD file.

        Args:
            file_path: Path to file to validate

        Returns:
            True if valid, False otherwise
        """

    @abstractmethod
    def validate_extraction_result(
        self, output_dir: Path, expected_entries: list[str]
    ) -> dict[str, Any]:
        """Validate extraction results.

        Args:
            output_dir: Directory containing extracted files
            expected_entries: List of expected entry names

        Returns:
            Validation results with missing/extra entries
        """

    @abstractmethod
    def validate_file_integrity(
        self, file_path: Path, expected_checksum: str | None = None
    ) -> bool:
        """Validate file integrity.

        Args:
            file_path: Path to file to validate
            expected_checksum: Optional expected checksum

        Returns:
            True if file integrity is valid
        """

    @abstractmethod
    def validate_entry(self, entry: dict[str, Any]) -> bool:
        """Validate an individual entry from the binary file.

        Args:
            entry: Entry dictionary with metadata

        Returns:
            True if entry is valid, False otherwise
        """


class IExtractionStatistics(ABC):
    """Interface for tracking extraction metrics and statistics."""

    @abstractmethod
    def start_extraction(self, file_path: Path) -> None:
        """Start tracking extraction for a file.

        Args:
            file_path: File being extracted
        """

    @abstractmethod
    def record_entry_extracted(
        self, entry_name: str, entry_type: str, size: int, success: bool
    ) -> None:
        """Record extraction of a single entry.

        Args:
            entry_name: Name of the entry
            entry_type: Type of the entry
            size: Size in bytes
            success: Whether extraction was successful
        """

    @abstractmethod
    def record_recovery_attempt(
        self, strategy: str, success: bool, recovered_count: int = 0
    ) -> None:
        """Record a recovery attempt.

        Args:
            strategy: Recovery strategy used
            success: Whether recovery was successful
            recovered_count: Number of entries recovered
        """

    @abstractmethod
    def get_statistics(self) -> "ExtractionStatsDict":
        """Get current extraction statistics.

        Returns:
            Dictionary with all statistics
        """

    @abstractmethod
    def reset_statistics(self) -> None:
        """Reset all statistics to initial state."""

    @abstractmethod
    def end_file_extraction(self, success: bool) -> None:
        """End tracking for current file extraction.

        Args:
            success: Whether the file extraction was successful
        """


# Progress callback type
ProgressCallback = Callable[[str, float], None]


class IProgressReporter(ABC):
    """Interface for progress reporting during extraction."""

    @abstractmethod
    def start_file(self, file_path: Path, total_entries: int) -> None:
        """Start processing a new file.

        Args:
            file_path: File being processed
            total_entries: Total number of entries to extract
        """

    @abstractmethod
    def update_progress(
        self, current_entry: int, entry_name: str, message: str | None = None
    ) -> None:
        """Update extraction progress.

        Args:
            current_entry: Current entry number
            entry_name: Name of current entry
            message: Optional status message
        """

    @abstractmethod
    def complete_file(self, success: bool, message: str | None = None) -> None:
        """Mark file processing as complete.

        Args:
            success: Whether processing was successful
            message: Optional completion message
        """

    @abstractmethod
    def report_file_start(self, file_path: str) -> None:
        """Start processing a file (string path variant).

        Args:
            file_path: String path to the file being processed
        """

    @abstractmethod
    def report_file_complete(self, file_path: str) -> None:
        """Complete processing a file (string path variant).

        Args:
            file_path: String path to the completed file
        """


class IPathValidator(Protocol):
    """Interface for path validation service."""

    def validate_path(self, path: Path, base_path: Path) -> None:
        """Validate a path is safe and within bounds.

        Args:
            path: Path to validate
            base_path: Base directory for boundary checking

        Raises:
            ValueError: If path is invalid or outside boundaries
        """
        ...

    def sanitize_filename(self, filename: str) -> str:
        """Sanitize a filename for safe filesystem operations.

        Args:
            filename: Raw filename to sanitize

        Returns:
            Sanitized filename safe for filesystem
        """
        ...


class IResourceMonitor(Protocol):
    """Interface for resource monitoring service."""

    def start_monitoring(self) -> None:
        """Start monitoring system resources."""
        ...

    def stop_monitoring(self) -> None:
        """Stop monitoring and clean up."""
        ...

    def check_memory_usage(self) -> None:
        """Check current memory usage against limits.

        Raises:
            MemoryError: If memory limit exceeded
        """
        ...

    def check_file_size(self, size: int, path: str) -> None:
        """Check if file size is within limits.

        Args:
            size: File size in bytes
            path: File path for error reporting

        Raises:
            ValueError: If file size exceeds limit
        """
        ...

    def check_file_count(self) -> None:
        """Check if file count is within limits.

        Raises:
            RuntimeError: If file count exceeds limit
        """
        ...


class IProgressTracker(Protocol):
    """Interface for progress tracking.

    This interface supports both incremental and absolute progress updates
    to accommodate different usage patterns across the codebase.
    """

    def set_total(self, total: int) -> None:
        """Set total number of items to process."""
        ...

    def update(self, n: int = 1, description: str | None = None) -> None:
        """Update progress incrementally by n items.

        Args:
            n: Number of items to increment progress by (default: 1)
            description: Optional description/item name for this update
        """
        ...

    def set_progress(self, value: int, description: str | None = None) -> None:
        """Set progress to an absolute value.

        Args:
            value: Absolute progress value
            description: Optional description/item name for this update
        """
        ...

    def set_description(self, desc: str) -> None:
        """Set progress description."""
        ...

    def close(self) -> None:
        """Close and clean up progress tracker."""
        ...


class IPBDReader(Protocol):
    """Interface for PBD/PBL file reading."""

    def extract_all(
        self, output_dir: Path, progress_callback: Callable | None = None
    ) -> int:
        """Extract all entries from PBD/PBL file.

        Args:
            output_dir: Directory to extract to
            progress_callback: Optional callback for progress updates

        Returns:
            Number of files extracted
        """
        ...

    def get_entry_count(self) -> int:
        """Get total number of entries in file."""
        ...

    def close(self) -> None:
        """Close file and clean up resources."""
        ...


class IBinaryExtractor(Protocol):
    """Interface for binary data extraction."""

    def extract(self, entry: Any, output_path: Path) -> Path | None:
        """Extract binary data from entry.

        Args:
            entry: Entry to extract from
            output_path: Output directory

        Returns:
            Path to extracted file or None if failed
        """
        ...


# Keep existing interfaces for compatibility
class IExtractor(Protocol):
    """Interface for all extractors."""

    @abstractmethod
    def extract(self, input_path: Path, output_path: Path) -> dict[str, Any]:
        """Extract content from input to output."""
        ...

    @abstractmethod
    def supports(self, file_path: Path) -> bool:
        """Check if this extractor supports the given file."""
        ...


class IExtractorCoordinator(Protocol):
    """Interface for extract coordinator."""

    @abstractmethod
    def extract(self, input_dir: Path, output_dir: Path) -> dict[str, Any]:
        """Coordinate extraction process."""
        ...

    @abstractmethod
    def register_extractor(self, extractor: IExtractor) -> None:
        """Register a new extractor."""
        ...

    @abstractmethod
    def get_extractors(self) -> list[IExtractor]:
        """Get all registered extractors."""
        ...


# ========== Generator Interfaces ==========


class IASTExtractor(Protocol):
    """Interface for AST extraction."""

    def extract_datawindow_from_ast(self, ast: dict[str, Any]) -> dict[str, Any]:
        """Extract DataWindow from AST.

        Args:
            ast: Abstract syntax tree

        Returns:
            DataWindow structure
        """
        ...

    def extract_methods_from_ast(self, ast: dict[str, Any]) -> list[dict[str, Any]]:
        """Extract methods from AST.

        Args:
            ast: Abstract syntax tree

        Returns:
            List of methods
        """
        ...

    def extract_window_from_ast(self, ast: dict[str, Any]) -> dict[str, Any]:
        """Extract window from AST.

        Args:
            ast: Abstract syntax tree

        Returns:
            Window structure
        """
        ...


class IGeneratorFactory(Protocol):
    """Interface for generator factory."""

    def create_model_generator(self, config: dict[str, Any]) -> Any:
        """Create model generator.

        Args:
            config: Generator configuration

        Returns:
            Model generator instance
        """
        ...

    def create_service_generator(self, config: dict[str, Any]) -> Any:
        """Create service generator.

        Args:
            config: Generator configuration

        Returns:
            Service generator instance
        """
        ...

    def create_ui_generator(self, framework: str, config: dict[str, Any]) -> Any:
        """Create UI generator.

        Args:
            framework: Target UI framework
            config: Generator configuration

        Returns:
            UI generator instance
        """
        ...


class ITypeConverter(Protocol):
    """Interface for type conversion."""

    def convert_type(self, pb_type: str, target_language: str) -> str:
        """Convert PowerBuilder type to target language.

        Args:
            pb_type: PowerBuilder type
            target_language: Target language

        Returns:
            Converted type
        """
        ...

    def get_initial_value(self, pb_type: str, target_language: str) -> str:
        """Get initial value for type.

        Args:
            pb_type: PowerBuilder type
            target_language: Target language

        Returns:
            Initial value string
        """
        ...


class IUIProcessor(Protocol):
    """Interface for UI processing."""

    def process_controls(self, controls: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Process UI controls.

        Args:
            controls: List of controls

        Returns:
            Processed controls
        """
        ...

    def generate_layout(self, controls: list[dict[str, Any]]) -> dict[str, Any]:
        """Generate layout from controls.

        Args:
            controls: List of controls

        Returns:
            Layout structure
        """
        ...

    def extract_menus(self, window: dict[str, Any]) -> list[dict[str, Any]]:
        """Extract menus from window.

        Args:
            window: Window structure

        Returns:
            List of menus
        """
        ...


class IEventProcessor(Protocol):
    """Interface for event processing."""

    def process_events(self, events: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Process event definitions.

        Args:
            events: List of event definitions

        Returns:
            Processed events with handlers and metadata
        """
        ...

    def extract_event_handlers(self, ast: dict[str, Any]) -> dict[str, list[str]]:
        """Extract event handlers from AST.

        Args:
            ast: Abstract syntax tree

        Returns:
            Dictionary mapping control names to their event handlers
        """
        ...

    def wire_events(
        self, controls: list[dict[str, Any]], event_handlers: dict[str, list[str]]
    ) -> dict[str, Any]:
        """Wire events to controls.

        Args:
            controls: List of controls
            event_handlers: Event handlers by control name

        Returns:
            Event wiring configuration
        """
        ...


class IProjectScaffolder(Protocol):
    """Interface for project scaffolding."""

    def create_project_structure(
        self, project_name: str, framework: str, output_dir: Path
    ) -> dict[str, Any]:
        """Create project directory structure.

        Args:
            project_name: Name of the project
            framework: Target framework
            output_dir: Output directory path

        Returns:
            Dictionary with created paths and metadata
        """
        ...

    def generate_config_files(
        self, project_root: Path, config: dict[str, Any]
    ) -> list[str]:
        """Generate configuration files.

        Args:
            project_root: Project root directory
            config: Configuration options

        Returns:
            List of generated file paths
        """
        ...

    def create_boilerplate_files(
        self, project_root: Path, modules: list[str]
    ) -> dict[str, str]:
        """Create boilerplate code files.

        Args:
            project_root: Project root directory
            modules: List of module names

        Returns:
            Dictionary mapping file paths to their content
        """
        ...


class ITemplateEngine(Protocol):
    """Interface for template engine."""

    def render(self, template_name: str, context: dict[str, Any]) -> str:
        """Render template with context.

        Args:
            template_name: Template name
            context: Template context

        Returns:
            Rendered content
        """
        ...

    def register_filter(self, name: str, filter_func: callable) -> None:
        """Register template filter.

        Args:
            name: Filter name
            filter_func: Filter function
        """
        ...


# Keep existing interfaces for compatibility
class IGenerator(Protocol):
    """Interface for all generators."""

    @abstractmethod
    def generate(self, ast: Any, output_dir: Path) -> dict[str, Any]:
        """Generate output from AST."""
        ...

    @abstractmethod
    def supports(self, target: str) -> bool:
        """Check if this generator supports the given target."""
        ...

    @abstractmethod
    def get_target_name(self) -> str:
        """Get the target name for this generator."""
        ...


class IGeneratorCoordinator(Protocol):
    """Interface for generate coordinator."""

    @abstractmethod
    def generate(
        self, input_dir: Path, output_dir: Path, target: str = "flutter"
    ) -> dict[str, Any]:
        """Coordinate generation process."""
        ...

    @abstractmethod
    def register_generator(self, generator: IGenerator) -> None:
        """Register a new generator."""
        ...

    @abstractmethod
    def get_generators(self) -> list[IGenerator]:
        """Get all registered generators."""
        ...

    @abstractmethod
    def get_generator(self, target: str) -> IGenerator | None:
        """Get a specific generator by target."""
        ...


# ========== Parser Interfaces ==========


class ITypeParser(Protocol):
    """Interface for type parsers."""

    def parse_type_declaration(self, tree: Tree) -> Any:
        """Parse a type declaration."""
        ...

    def get_type(self, name: str) -> Any | None:
        """Get a parsed type by name."""
        ...


class IEnumeratedType(Protocol):
    """Interface for enumerated types."""

    @property
    def name(self) -> str:
        """Type name."""
        ...

    @property
    def values(self) -> dict[str, int]:
        """Enum values."""
        ...

    def get_value(self, name: str) -> int | None:
        """Get numeric value for enum name."""
        ...


class IStructureType(Protocol):
    """Interface for structure types."""

    @property
    def name(self) -> str:
        """Type name."""
        ...

    @property
    def fields(self) -> list[Any]:
        """Structure fields."""
        ...

    def get_field(self, name: str) -> Any | None:
        """Get field by name."""
        ...


class IGrammarManager(Protocol):
    """Interface for grammar management."""

    def load_grammar(self, name: str, **kwargs: Any) -> Any:
        """Load a grammar by name.

        Args:
            name: Grammar name
            **kwargs: Additional grammar options

        Returns:
            Loaded grammar
        """
        ...

    def get_grammar_path(self, name: str) -> Path:
        """Get path to grammar file.

        Args:
            name: Grammar name

        Returns:
            Path to grammar file
        """
        ...


class ILibraryManager(Protocol):
    """Interface for library management."""

    def resolve_import(self, library_name: str) -> Path | None:
        """Resolve library import to file path.

        Args:
            library_name: Name of the library

        Returns:
            Path to library file or None if not found
        """
        ...

    def add_library_path(self, path: Path) -> None:
        """Add path to search for libraries.

        Args:
            path: Directory to search
        """
        ...

    def get_library_dependencies(self, library_name: str) -> list[str]:
        """Get dependencies of a library.

        Args:
            library_name: Name of the library

        Returns:
            List of dependency names
        """
        ...


class ITypeResolver(Protocol):
    """Interface for type resolution."""

    def resolve_type(self, type_name: str) -> dict[str, Any] | None:
        """Resolve a custom type.

        Args:
            type_name: Name of the type

        Returns:
            Type definition or None if not found
        """
        ...

    def register_type(self, type_name: str, type_def: dict[str, Any]) -> None:
        """Register a custom type.

        Args:
            type_name: Name of the type
            type_def: Type definition
        """
        ...

    def get_all_types(self) -> dict[str, dict[str, Any]]:
        """Get all registered types.

        Returns:
            Dictionary of type definitions
        """
        ...


class IImportResolver(Protocol):
    """Interface for import resolution."""

    def resolve_imports(self, source: str) -> str:
        """Resolve implicit imports in source.

        Args:
            source: PowerBuilder source code

        Returns:
            Source with explicit imports
        """
        ...

    def get_implicit_imports(self) -> list[str]:
        """Get list of implicit imports.

        Returns:
            List of implicit import statements
        """
        ...


class ITransformer(Protocol):
    """Interface for AST transformation."""

    def transform(self, tree: Tree) -> dict[str, Any]:
        """Transform parse tree to AST.

        Args:
            tree: Parse tree

        Returns:
            Abstract syntax tree
        """
        ...

    def get_position_info(self) -> dict[str, Any]:
        """Get position tracking information.

        Returns:
            Position information from last transform
        """
        ...


class IPreprocessor(Protocol):
    """Interface for source preprocessing."""

    def preprocess(self, source: str) -> str:
        """Preprocess source code.

        Args:
            source: Raw source code

        Returns:
            Preprocessed source code
        """
        ...

    def get_includes(self) -> list[str]:
        """Get list of included files.

        Returns:
            List of included file paths
        """
        ...


# Keep existing interfaces for compatibility
class IParser(Protocol):
    """Interface for all parsers."""

    @abstractmethod
    def parse(self, source: str, file_path: Path | None = None) -> Any:
        """Parse source code into AST."""
        ...

    @abstractmethod
    def supports(self, file_path: Path) -> bool:
        """Check if this parser supports the given file."""
        ...


class IParserCoordinator(Protocol):
    """Interface for parse coordinator."""

    @abstractmethod
    def parse(self, input_dir: Path, output_dir: Path) -> dict[str, Any]:
        """Coordinate parsing process."""
        ...

    @abstractmethod
    def parse_file(self, file_path: Path) -> Any:
        """Parse a single file."""
        ...

    @abstractmethod
    def register_parser(self, parser: IParser) -> None:
        """Register a new parser."""
        ...

    @abstractmethod
    def get_parsers(self) -> list[IParser]:
        """Get all registered parsers."""
        ...


# ========== Model Interfaces ==========


class IASTProcessor(Protocol):
    """Interface for AST processing."""

    @abstractmethod
    def process_ast_file(self, file_path: Path) -> dict[str, Any]:
        """Process an AST file."""
        ...

    @abstractmethod
    def extract_metadata(self, ast: dict[str, Any]) -> dict[str, Any]:
        """Extract metadata from AST."""
        ...

    @abstractmethod
    def get_statistics(self) -> dict[str, Any]:
        """Get processing statistics."""
        ...


class IEntityFactory(Protocol):
    """Interface for entity creation."""

    @abstractmethod
    def create_application(self, name: str, **kwargs: Any) -> Any:
        """Create application entity."""
        ...

    @abstractmethod
    def create_window(self, name: str, **kwargs: Any) -> Any:
        """Create window entity."""
        ...

    @abstractmethod
    def create_function(self, name: str, **kwargs: Any) -> Any:
        """Create function entity."""
        ...

    @abstractmethod
    def create_datawindow(self, name: str, **kwargs: Any) -> Any:
        """Create datawindow entity."""
        ...

    @abstractmethod
    def create_library(self, name: str, **kwargs: Any) -> Any:
        """Create library entity."""
        ...

    @abstractmethod
    def create_entity(self, entity_type: str, name: str, **kwargs: Any) -> Any:
        """Create entity by type."""
        ...

    @abstractmethod
    def get_entity(self, entity_type: str, name: str) -> Any:
        """Get entity by type and name."""
        ...

    @abstractmethod
    def register_custom_type(self, type_name: str, factory_func: Any) -> None:
        """Register custom entity type."""
        ...

    @abstractmethod
    def clear_cache(self) -> None:
        """Clear entity cache."""
        ...

    @abstractmethod
    def get_all_entities(self) -> list[Any]:
        """Get all entities."""
        ...


class IEntityValidator(Protocol):
    """Interface for entity validation."""

    @abstractmethod
    def validate_entity(self, entity: Any) -> list[str]:
        """Validate an entity."""
        ...

    @abstractmethod
    def validate_name(self, name: str, entity_type: str) -> bool:
        """Validate entity name."""
        ...


class IExpressionEvaluator(Protocol):
    """Interface for expression evaluation."""

    @abstractmethod
    def evaluate(self, expression: Any, context: dict[str, Any]) -> Any:
        """Evaluate an expression in context."""
        ...

    @abstractmethod
    def can_evaluate(self, expression: Any) -> bool:
        """Check if expression can be evaluated."""
        ...


class IModelExtractor(Protocol):
    """Interface for model extraction."""

    @abstractmethod
    def extract_window_model(self, ast: dict[str, Any]) -> dict[str, Any]:
        """Extract window model from AST."""
        ...

    @abstractmethod
    def extract_datawindow_model(self, ast: dict[str, Any]) -> dict[str, Any]:
        """Extract datawindow model from AST."""
        ...

    @abstractmethod
    def extract_function_model(self, ast: dict[str, Any]) -> dict[str, Any]:
        """Extract function model from AST."""
        ...

    @abstractmethod
    def set_current_object(self, obj: Any) -> None:
        """Set current object for extraction context."""
        ...

    @abstractmethod
    def extract_generic_model(self, ast: dict[str, Any]) -> dict[str, Any]:
        """Extract generic model from AST."""
        ...


class IModelPersistence(Protocol):
    """Interface for model persistence."""

    @abstractmethod
    def save_model(self, model: dict[str, Any], file_path: Path) -> None:
        """Save model to file."""
        ...

    @abstractmethod
    def load_model(self, file_path: Path) -> dict[str, Any]:
        """Load model from file."""
        ...

    @abstractmethod
    def save_model_by_type(
        self, model_type: str, model: dict[str, Any], file_path: Path
    ) -> None:
        """Save model by type to file."""
        ...

    @abstractmethod
    def create_model_summary(self, models: list[dict[str, Any]]) -> dict[str, Any]:
        """Create summary of models."""
        ...

    @abstractmethod
    def get_statistics(self) -> dict[str, Any]:
        """Get persistence statistics."""
        ...


class IRelationshipManager(Protocol):
    """Interface for relationship management."""

    @abstractmethod
    def add_relationship(
        self, source: Any, target: Any, relationship_type: str
    ) -> None:
        """Add a relationship between entities."""
        ...

    @abstractmethod
    def get_relationship_graph(self) -> dict[str, Any]:
        """Get relationship graph."""
        ...
