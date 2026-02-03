"""Core Package - Shared models, types, and contracts.

This package contains the core domain models and contracts that are
shared across all pipeline stages. No external dependencies or I/O operations.
"""

from .contracts import (
    # Extract interfaces
    IBinaryParser,
    IExtractor,
    # Decompile interfaces
    IDecompiler,
    IOpcodeDecoder,
    # Parse interfaces
    IGrammarLoader,
    IParser,
    # Model interfaces
    IModelBuilder,
    ITypeResolver,
    # Generate interfaces
    ICodeGenerator,
    ITemplateEngine,
    # Shared interfaces
    ICache,
    IFileHandler,
    ILogger,
    IPipelineOrchestrator,
    IPipelineStage,
    IProgressReporter,
    IRecoveryStrategy,
    IValidator,
)
from .models import (
    # Enums
    ObjectType,
    PipelineStage,
    TargetLanguage,
    # Extract models
    ExtractedObject,
    PBLEntry,
    PBLFile,
    # Decompile models
    DecompiledSource,
    PCodeFunction,
    PCodeInstruction,
    # Parse models
    ASTNode,
    ParsedObject,
    # Model stage models
    Event,
    Method,
    Parameter,
    Property,
    SemanticObject,
    # PowerBuilder models
    DataWindowColumn,
    DataWindowDefinition,
    PBControl,
    PBWindow,
    # Generate models
    GeneratedFile,
    GeneratedProject,
    # Application model
    ApplicationModel,
    # Result models
    DecompileResult,
    ExtractResult,
)
from .types import (
    # Basic types
    ByteArray,
    ConfigDict,
    MetadataDict,
    PathLike,
    # PowerBuilder types
    ObjectName,
    Opcode,
    SourceCode,
    # Stage types
    ExtractedData,
    ParseTree,
    # Constants
    DEFAULT_BUFFER_SIZE,
    DEFAULT_ENCODING,
    MAX_FILE_SIZE,
    PBD_EXTENSION,
    PBL_EXTENSION,
    SOURCE_EXTENSIONS,
)

__all__ = [
    # Models
    "ObjectType",
    "PipelineStage",
    "TargetLanguage",
    "ExtractedObject",
    "PBLEntry",
    "PBLFile",
    "DecompiledSource",
    "PCodeFunction",
    "PCodeInstruction",
    "ASTNode",
    "ParsedObject",
    "Event",
    "Method",
    "Parameter",
    "Property",
    "SemanticObject",
    "DataWindowColumn",
    "DataWindowDefinition",
    "PBControl",
    "PBWindow",
    "GeneratedFile",
    "GeneratedProject",
    "ApplicationModel",
    # Contracts
    "IExtractor",
    "IBinaryParser",
    "IDecompiler",
    "IOpcodeDecoder",
    "IParser",
    "IGrammarLoader",
    "IModelBuilder",
    "ITypeResolver",
    "ICodeGenerator",
    "ITemplateEngine",
    "IFileHandler",
    "IProgressReporter",
    "ICache",
    "IValidator",
    "ILogger",
    "IPipelineStage",
    "IPipelineOrchestrator",
    "IRecoveryStrategy",
    # Types
    "PathLike",
    "ConfigDict",
    "MetadataDict",
    "ByteArray",
    "ObjectName",
    "Opcode",
    "SourceCode",
    "ExtractedData",
    "ParseTree",
    # Constants
    "PBL_EXTENSION",
    "PBD_EXTENSION",
    "SOURCE_EXTENSIONS",
    "DEFAULT_ENCODING",
    "DEFAULT_BUFFER_SIZE",
    "MAX_FILE_SIZE",
]
