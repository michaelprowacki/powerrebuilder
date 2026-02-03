"""Core Type Definitions - Type aliases and common types.

This module contains all type definitions and aliases used throughout
the PowerRebuilder pipeline, providing a single source of truth for types.
"""

from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, TypeAlias, Union

# ============================================================================
# BASIC TYPE ALIASES
# ============================================================================

# Path types
PathLike: TypeAlias = Union[str, Path]
FilePath: TypeAlias = Path
DirectoryPath: TypeAlias = Path

# Data types
Byte: TypeAlias = int  # 0-255
ByteArray: TypeAlias = bytes
HexString: TypeAlias = str
Offset: TypeAlias = int
Size: TypeAlias = int

# Collections
ConfigDict: TypeAlias = Dict[str, Any]
MetadataDict: TypeAlias = Dict[str, Any]
PropertiesDict: TypeAlias = Dict[str, Any]
AttributesDict: TypeAlias = Dict[str, Any]

# Results
ResultTuple: TypeAlias = Tuple[bool, Optional[str]]  # (success, error_message)
ValidationResult: TypeAlias = Tuple[bool, List[str]]  # (is_valid, errors)

# ============================================================================
# POWERBUILDER SPECIFIC TYPES
# ============================================================================

# Object identifiers
ObjectName: TypeAlias = str
ObjectPath: TypeAlias = str  # e.g., "window.control.subcontrol"
LibraryPath: TypeAlias = str  # Path to PBL/PBD

# Source code types
SourceCode: TypeAlias = str
SQLQuery: TypeAlias = str
Expression: TypeAlias = str

# P-code types
Opcode: TypeAlias = int
Operand: TypeAlias = Union[int, str, float, bool]
InstructionPointer: TypeAlias = int

# ============================================================================
# STAGE-SPECIFIC TYPES
# ============================================================================

# Extract stage
ExtractedData: TypeAlias = Dict[str, bytes]
LibrarySignature: TypeAlias = bytes
EntryMap: TypeAlias = Dict[str, Offset]

# Decompile stage
BytecodeChunk: TypeAlias = bytes
InstructionList: TypeAlias = List[Tuple[Opcode, List[Operand]]]
SymbolTable: TypeAlias = Dict[str, Any]

# Parse stage
TokenType: TypeAlias = str
TokenValue: TypeAlias = Union[str, int, float, bool]
TokenList: TypeAlias = List[Tuple[TokenType, TokenValue]]
ParseTree: TypeAlias = Dict[str, Any]

# Model stage
DependencyGraph: TypeAlias = Dict[str, List[str]]
TypeMap: TypeAlias = Dict[str, str]
ReferenceMap: TypeAlias = Dict[str, List[str]]

# Generate stage
Template: TypeAlias = str
TemplateContext: TypeAlias = Dict[str, Any]
GeneratedCode: TypeAlias = str

# ============================================================================
# FUNCTION SIGNATURES
# ============================================================================

# Common function types
Validator: TypeAlias = Callable[[Any], bool]
Transformer: TypeAlias = Callable[[Any], Any]
Filter: TypeAlias = Callable[[Any], bool]
Mapper: TypeAlias = Callable[[Any], Any]
Reducer: TypeAlias = Callable[[Any, Any], Any]

# Stage processors
ExtractProcessor: TypeAlias = Callable[[PathLike], ExtractedData]
DecompileProcessor: TypeAlias = Callable[[bytes], SourceCode]
ParseProcessor: TypeAlias = Callable[[SourceCode], ParseTree]
ModelProcessor: TypeAlias = Callable[[ParseTree], Any]
GenerateProcessor: TypeAlias = Callable[[Any], GeneratedCode]

# ============================================================================
# ERROR TYPES
# ============================================================================

ErrorCode: TypeAlias = str
ErrorMessage: TypeAlias = str
ErrorContext: TypeAlias = Dict[str, Any]
ErrorList: TypeAlias = List[Tuple[ErrorCode, ErrorMessage]]

# ============================================================================
# PROGRESS AND METRICS
# ============================================================================

TaskID: TypeAlias = str
ProgressValue: TypeAlias = float  # 0.0 to 1.0
MetricName: TypeAlias = str
MetricValue: TypeAlias = Union[int, float, str]
MetricsDict: TypeAlias = Dict[MetricName, MetricValue]

# ============================================================================
# VERSION INFORMATION
# ============================================================================

Version: TypeAlias = str  # e.g., "1.0.0"
PowerBuilderVersion: TypeAlias = str  # e.g., "PB12.5"
TargetVersion: TypeAlias = str  # e.g., "Flutter 3.0"

# ============================================================================
# BINARY FORMATS
# ============================================================================

# Binary structure types
StructFormat: TypeAlias = str  # struct format string
Endianness: TypeAlias = str  # "little" or "big"
Encoding: TypeAlias = str  # e.g., "utf-8", "utf-16-le"

# Checksums
Checksum: TypeAlias = int
ChecksumAlgorithm: TypeAlias = str  # "crc32", "md5", etc.

# ============================================================================
# CACHE TYPES
# ============================================================================

CacheKey: TypeAlias = str
CacheValue: TypeAlias = Any
CacheTTL: TypeAlias = int  # Time to live in seconds
CacheSize: TypeAlias = int  # Max number of entries

# ============================================================================
# CONSTANTS
# ============================================================================

# File extensions
PBL_EXTENSION = ".pbl"
PBD_EXTENSION = ".pbd"
PCODE_EXTENSION = ".fun"
SOURCE_EXTENSIONS = {".sru", ".srw", ".srm", ".srd", ".srs", ".sra"}

# Magic numbers/signatures
PBL_SIGNATURE = b"PBL\x06"
PBD_SIGNATURE = b"PBD\x06"

# Size limits
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
MAX_STRING_LENGTH = 65535
MAX_ARRAY_SIZE = 10000

# Default values
DEFAULT_ENCODING = "utf-8"
DEFAULT_ENDIAN = "little"
DEFAULT_BUFFER_SIZE = 8192
