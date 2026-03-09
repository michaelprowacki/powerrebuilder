"""PowerBuilder P-code Domain Types.

Pure data types representing P-code bytecode structures.
These are the WHAT - no operations, just data models.
Events are colocated with their aggregates following Scott Wlaschin's FDM principles.
"""

from dataclasses import dataclass
from typing import List, Optional, Union
from enum import Enum
from datetime import datetime


# ============================================================================
# P-CODE INSTRUCTIONS
# ============================================================================


class OpCode(int, Enum):
    """P-code operation codes."""

    NOP = 0x00
    PUSH = 0x01
    POP = 0x02
    DUP = 0x03
    LOAD = 0x10
    STORE = 0x11
    LOADCONST = 0x12
    CALL = 0x20
    RETURN = 0x21
    JUMP = 0x30
    JUMPIF = 0x31
    JUMPIFNOT = 0x32
    ADD = 0x40
    SUB = 0x41
    MUL = 0x42
    DIV = 0x43
    MOD = 0x44
    EQ = 0x50
    NE = 0x51
    LT = 0x52
    LE = 0x53
    GT = 0x54
    GE = 0x55
    AND = 0x60
    OR = 0x61
    NOT = 0x62


@dataclass(frozen=True)
class PCodeInstruction:
    """A single P-code instruction."""

    offset: int
    opcode: OpCode
    operands: List[Union[int, str, float]]
    size: int  # Bytes consumed
    comment: Optional[str] = None


@dataclass(frozen=True)
class PCodeFunction:
    """A compiled function in P-code."""

    name: str
    signature: str
    instructions: List[PCodeInstruction]
    local_count: int
    parameter_count: int
    return_type: Optional[str]
    entry_offset: int
    code_size: int


@dataclass(frozen=True)
class PCodeModule:
    """A module containing P-code functions."""

    name: str
    functions: List[PCodeFunction]
    globals: List[str]
    constants: List[any]
    string_pool: List[str]
    version: int


# ============================================================================
# P-CODE METADATA
# ============================================================================


@dataclass(frozen=True)
class SymbolInfo:
    """Symbol table entry."""

    name: str
    type: str
    scope: str  # local, global, parameter
    offset: int
    size: int


@dataclass(frozen=True)
class DebugInfo:
    """Debug information for P-code."""

    source_file: str
    line_numbers: List[int]  # Maps instruction offset to line number
    variable_names: List[str]
    breakpoints: List[int]


@dataclass(frozen=True)
class PCodeHeader:
    """P-code file header."""

    magic: bytes
    version: int
    flags: int
    entry_point: int
    code_size: int
    data_size: int
    symbol_count: int
    string_count: int


# ============================================================================
# VERSION-SPECIFIC STRUCTURES
# ============================================================================


@dataclass(frozen=True)
class PB6PCode:
    """PowerBuilder 6.x P-code format."""

    header: PCodeHeader
    code_section: bytes
    data_section: bytes
    symbol_table: List[SymbolInfo]
    string_table: List[str]


@dataclass(frozen=True)
class PB10PCode:
    """PowerBuilder 10.x P-code format (Unicode support)."""

    header: PCodeHeader
    code_section: bytes
    data_section: bytes
    unicode_strings: List[str]
    symbol_table: List[SymbolInfo]
    metadata: dict


@dataclass(frozen=True)
class PB12PCode:
    """PowerBuilder 12.x P-code format (.NET integration)."""

    header: PCodeHeader
    code_section: bytes
    data_section: bytes
    dotnet_metadata: bytes
    symbol_table: List[SymbolInfo]
    string_table: List[str]
    assembly_refs: List[str]


# ============================================================================
# DECOMPILATION MARKERS
# ============================================================================


@dataclass(frozen=True)
class DecompilationHint:
    """Hints for P-code decompilation."""

    pattern: bytes
    meaning: str
    confidence: float  # 0.0 to 1.0
    version_specific: bool


@dataclass(frozen=True)
class ControlFlow:
    """Control flow information."""

    entry_points: List[int]
    exit_points: List[int]
    loops: List[tuple[int, int]]  # (start, end) offsets
    conditionals: List[tuple[int, int, int]]  # (condition, true_branch, false_branch)


# ============================================================================
# DOMAIN EVENTS (Colocated with P-code aggregate)
# ============================================================================


@dataclass(frozen=True)
class PCodeAnalyzed:
    """Event: P-code bytecode was analyzed."""

    module: PCodeModule
    instruction_count: int
    complexity: int
    timestamp: datetime


@dataclass(frozen=True)
class FunctionDecompiled:
    """Event: A P-code function was decompiled."""

    function: PCodeFunction
    source_code: str
    confidence: float  # 0.0 to 1.0
    timestamp: datetime


@dataclass(frozen=True)
class VersionDetected:
    """Event: PowerBuilder version detected from P-code."""

    version: int  # 6, 10, 12, etc.
    format_type: str  # PB6PCode, PB10PCode, PB12PCode
    features: List[str]
    timestamp: datetime


@dataclass(frozen=True)
class DecompilationFailed:
    """Event: P-code decompilation failed."""

    function_name: str
    offset: int
    reason: str
    partial_result: Optional[str]
    timestamp: datetime
