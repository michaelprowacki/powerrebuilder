"""Core Contracts - All interfaces/protocols in one place.

This file contains ALL the interfaces (protocols) used throughout the pipeline.
Single source of truth for contracts between components.
"""

from abc import abstractmethod
from typing import Any, Dict, List, Optional, Protocol

from .models import (
    ApplicationModel,
    ASTNode,
    DecompiledSource,
    ExtractedObject,
    GeneratedProject,
    ParsedObject,
    SemanticObject,
)
from .types import PathLike


# ============================================================================
# EXTRACT STAGE INTERFACES
# ============================================================================


class IExtractor(Protocol):
    """Interface for extracting objects from PBL/PBD files."""

    @abstractmethod
    def extract(self, file_path: PathLike) -> List[ExtractedObject]:
        """Extract objects from a PowerBuilder library file.

        Args:
            file_path: Path to PBL/PBD file

        Returns:
            List of extracted objects
        """
        ...

    @abstractmethod
    def validate_library(self, file_path: PathLike) -> bool:
        """Validate if file is a valid PowerBuilder library.

        Args:
            file_path: Path to check

        Returns:
            True if valid PBL/PBD
        """
        ...


class IBinaryParser(Protocol):
    """Interface for parsing binary files."""

    @abstractmethod
    def parse_header(self, data: bytes) -> Dict[str, Any]:
        """Parse file header.

        Args:
            data: Binary data

        Returns:
            Parsed header information
        """
        ...

    @abstractmethod
    def parse_entries(self, data: bytes, offset: int) -> List[Dict[str, Any]]:
        """Parse file entries.

        Args:
            data: Binary data
            offset: Starting offset

        Returns:
            List of parsed entries
        """
        ...


# ============================================================================
# DECOMPILE STAGE INTERFACES
# ============================================================================


class IDecompiler(Protocol):
    """Interface for decompiling P-code to source."""

    @abstractmethod
    def decompile(self, bytecode: bytes) -> DecompiledSource:
        """Decompile P-code bytecode to PowerBuilder source.

        Args:
            bytecode: P-code bytes

        Returns:
            Decompiled source code
        """
        ...

    @abstractmethod
    def detect_version(self, bytecode: bytes) -> str:
        """Detect PowerBuilder version from bytecode.

        Args:
            bytecode: P-code bytes

        Returns:
            Version string (e.g., "PB12.5")
        """
        ...


class IOpcodeDecoder(Protocol):
    """Interface for decoding P-code opcodes."""

    @abstractmethod
    def decode_instruction(
        self, data: bytes, offset: int
    ) -> tuple[int, List[Any], int]:
        """Decode a single P-code instruction.

        Args:
            data: Bytecode data
            offset: Current offset

        Returns:
            Tuple of (opcode, operands, next_offset)
        """
        ...

    @abstractmethod
    def get_opcode_name(self, opcode: int) -> str:
        """Get human-readable name for opcode.

        Args:
            opcode: Opcode value

        Returns:
            Opcode name
        """
        ...


# ============================================================================
# PARSE STAGE INTERFACES
# ============================================================================


class IParser(Protocol):
    """Interface for parsing PowerBuilder source to AST."""

    @abstractmethod
    def parse(self, source: str) -> ParsedObject:
        """Parse PowerBuilder source code to AST.

        Args:
            source: Source code string

        Returns:
            Parsed object with AST
        """
        ...

    @abstractmethod
    def validate_syntax(self, source: str) -> List[str]:
        """Validate syntax without full parsing.

        Args:
            source: Source code

        Returns:
            List of syntax errors
        """
        ...


class IGrammarLoader(Protocol):
    """Interface for loading and managing grammars."""

    @abstractmethod
    def load_grammar(self, grammar_name: str) -> Any:
        """Load a grammar definition.

        Args:
            grammar_name: Name of grammar

        Returns:
            Grammar object
        """
        ...

    @abstractmethod
    def get_available_grammars(self) -> List[str]:
        """Get list of available grammars.

        Returns:
            List of grammar names
        """
        ...


# ============================================================================
# MODEL STAGE INTERFACES
# ============================================================================


class IModelBuilder(Protocol):
    """Interface for building semantic models from AST."""

    @abstractmethod
    def build_model(self, ast: ASTNode) -> SemanticObject:
        """Build semantic model from AST.

        Args:
            ast: Abstract syntax tree

        Returns:
            Semantic object model
        """
        ...

    @abstractmethod
    def resolve_dependencies(self, model: SemanticObject) -> List[str]:
        """Resolve dependencies for a model.

        Args:
            model: Semantic model

        Returns:
            List of dependency names
        """
        ...


class ITypeResolver(Protocol):
    """Interface for resolving types in the model."""

    @abstractmethod
    def resolve_type(self, type_name: str) -> str:
        """Resolve a type name to its full type.

        Args:
            type_name: Type to resolve

        Returns:
            Resolved type
        """
        ...

    @abstractmethod
    def is_primitive(self, type_name: str) -> bool:
        """Check if type is primitive.

        Args:
            type_name: Type to check

        Returns:
            True if primitive type
        """
        ...


# ============================================================================
# GENERATE STAGE INTERFACES
# ============================================================================


class ICodeGenerator(Protocol):
    """Interface for generating target language code."""

    @abstractmethod
    def generate(self, model: ApplicationModel) -> GeneratedProject:
        """Generate target language project from model.

        Args:
            model: Application model

        Returns:
            Generated project
        """
        ...

    @abstractmethod
    def generate_file(self, model: SemanticObject) -> str:
        """Generate code for a single object.

        Args:
            model: Semantic object

        Returns:
            Generated code
        """
        ...


class ITemplateEngine(Protocol):
    """Interface for template-based code generation."""

    @abstractmethod
    def render(self, template_name: str, context: Dict[str, Any]) -> str:
        """Render a template with context.

        Args:
            template_name: Template to use
            context: Template variables

        Returns:
            Rendered output
        """
        ...

    @abstractmethod
    def load_template(self, template_path: str) -> Any:
        """Load a template file.

        Args:
            template_path: Path to template

        Returns:
            Template object
        """
        ...


# ============================================================================
# SHARED INTERFACES
# ============================================================================


class IFileHandler(Protocol):
    """Interface for file operations."""

    @abstractmethod
    def read_text(self, path: PathLike) -> str:
        """Read text file."""
        ...

    @abstractmethod
    def write_text(self, path: PathLike, content: str) -> None:
        """Write text file."""
        ...

    @abstractmethod
    def read_binary(self, path: PathLike) -> bytes:
        """Read binary file."""
        ...

    @abstractmethod
    def write_binary(self, path: PathLike, content: bytes) -> None:
        """Write binary file."""
        ...


class IProgressReporter(Protocol):
    """Interface for progress reporting."""

    @abstractmethod
    def start_task(
        self, task_id: str, description: str, total: Optional[int] = None
    ) -> None:
        """Start a new task."""
        ...

    @abstractmethod
    def update_task(self, task_id: str, advance: int = 1) -> None:
        """Update task progress."""
        ...

    @abstractmethod
    def complete_task(self, task_id: str) -> None:
        """Mark task as complete."""
        ...

    @abstractmethod
    def fail_task(self, task_id: str, error: str) -> None:
        """Mark task as failed."""
        ...


class ICache(Protocol):
    """Interface for caching operations."""

    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        ...

    @abstractmethod
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache."""
        ...

    @abstractmethod
    def delete(self, key: str) -> None:
        """Delete from cache."""
        ...

    @abstractmethod
    def clear(self) -> None:
        """Clear all cache entries."""
        ...


class IValidator(Protocol):
    """Interface for validation operations."""

    @abstractmethod
    def validate(self, data: Any) -> tuple[bool, List[str]]:
        """Validate data.

        Args:
            data: Data to validate

        Returns:
            Tuple of (is_valid, error_messages)
        """
        ...


class ILogger(Protocol):
    """Interface for logging operations."""

    @abstractmethod
    def debug(self, message: str, **kwargs) -> None:
        """Log debug message."""
        ...

    @abstractmethod
    def info(self, message: str, **kwargs) -> None:
        """Log info message."""
        ...

    @abstractmethod
    def warning(self, message: str, **kwargs) -> None:
        """Log warning message."""
        ...

    @abstractmethod
    def error(self, message: str, **kwargs) -> None:
        """Log error message."""
        ...


# ============================================================================
# PIPELINE INTERFACES
# ============================================================================


class IPipelineStage(Protocol):
    """Interface for a pipeline stage."""

    @property
    @abstractmethod
    def stage_name(self) -> str:
        """Get stage name."""
        ...

    @abstractmethod
    def process(self, input_path: PathLike, output_path: PathLike) -> Dict[str, Any]:
        """Process this stage.

        Args:
            input_path: Input directory
            output_path: Output directory

        Returns:
            Stage result
        """
        ...


class IPipelineOrchestrator(Protocol):
    """Interface for pipeline orchestration."""

    @abstractmethod
    def execute_pipeline(self, stages: List[IPipelineStage]) -> Dict[str, Any]:
        """Execute complete pipeline.

        Args:
            stages: List of stages to execute

        Returns:
            Pipeline result
        """
        ...


# ============================================================================
# RECOVERY INTERFACES
# ============================================================================


class IRecoveryStrategy(Protocol):
    """Interface for error recovery strategies."""

    @abstractmethod
    def can_recover(self, error: Exception) -> bool:
        """Check if error is recoverable.

        Args:
            error: Exception that occurred

        Returns:
            True if recoverable
        """
        ...

    @abstractmethod
    def recover(self, error: Exception, context: Dict[str, Any]) -> Any:
        """Attempt to recover from error.

        Args:
            error: Exception that occurred
            context: Error context

        Returns:
            Recovery result
        """
        ...
