"""PowerBuilder Library Domain Types.

Pure data types representing PowerBuilder library structures.
These are the WHAT - no operations, just data models.
Events are colocated with their aggregates following Scott Wlaschin's FDM principles.
"""

from dataclasses import dataclass
from typing import Optional, List
from enum import Enum
from datetime import datetime


# ============================================================================
# LIBRARY FILE FORMATS
# ============================================================================


@dataclass(frozen=True)
class PBLHeader:
    """PowerBuilder Library header structure."""

    signature: bytes  # 'PBL' or 'HDR*'
    version: int
    entry_count: int
    format: str  # 'PBL' or 'PBD'
    comment: Optional[str] = None


@dataclass(frozen=True)
class PBLEntry:
    """A single entry in a PowerBuilder library."""

    name: str
    object_type: str
    size: int
    offset: int
    data: bytes
    timestamp: Optional[int] = None
    comment: Optional[str] = None


@dataclass(frozen=True)
class PBDBlock:
    """A block in modern PBD format (HDR* files)."""

    signature: bytes  # HDR*, ENT*, DAT*, NOD*, FRE*
    offset: int
    length: int
    data: bytes


@dataclass(frozen=True)
class ENTEntry:
    """Entry in the ENT* (Entry Table) block."""

    index: int
    name: str
    object_type: str
    node_offset: int  # Points to NOD* block
    data_offset: int  # Points to DAT* block


@dataclass(frozen=True)
class NODBlock:
    """Node block containing tree structure."""

    signature: bytes  # NOD*
    entry_index: int
    parent_index: Optional[int]
    name: str
    metadata: bytes


# ============================================================================
# OBJECT TYPES
# ============================================================================


class PBObjectType(str, Enum):
    """PowerBuilder object types."""

    APPLICATION = "application"
    DATAWINDOW = "datawindow"
    FUNCTION = "function"
    GLOBAL = "global"
    MENU = "menu"
    PIPELINE = "pipeline"
    PROJECT = "project"
    PROXY = "proxy"
    QUERY = "query"
    STRUCTURE = "structure"
    USEROBJECT = "userobject"
    WINDOW = "window"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class LibraryObject:
    """A PowerBuilder object extracted from a library."""

    name: str
    type: PBObjectType
    source_code: Optional[str] = None  # If decompiled
    p_code: Optional[bytes] = None  # If still compiled
    metadata: dict = None


@dataclass(frozen=True)
class LibraryDirectory:
    """Directory listing of a PowerBuilder library."""

    path: str
    format: str  # PBL or PBD
    header: PBLHeader
    entries: List[PBLEntry]
    total_size: int


# ============================================================================
# COMPILATION UNITS
# ============================================================================


@dataclass(frozen=True)
class CompiledObject:
    """A compiled PowerBuilder object (P-code)."""

    name: str
    type: PBObjectType
    bytecode: bytes
    entry_point: int
    symbol_table: List[str]
    constants: List[any]
    version: int


@dataclass(frozen=True)
class SourceObject:
    """A decompiled PowerBuilder source object."""

    name: str
    type: PBObjectType
    source: str
    encoding: str
    line_count: int
    dependencies: List[str]


# ============================================================================
# DOMAIN EVENTS (Colocated with Library aggregate)
# ============================================================================


@dataclass(frozen=True)
class LibraryOpened:
    """Event: A PowerBuilder library was opened."""

    library_path: str
    format: str  # PBL or PBD
    entry_count: int
    timestamp: datetime


@dataclass(frozen=True)
class EntryExtracted:
    """Event: An entry was extracted from a library."""

    entry: PBLEntry
    library_path: str
    timestamp: datetime


@dataclass(frozen=True)
class LibraryCorrupted:
    """Event: A library file is corrupted."""

    library_path: str
    error_message: str
    offset: Optional[int]
    timestamp: datetime


@dataclass(frozen=True)
class ObjectCompiled:
    """Event: A source object was compiled to P-code."""

    object_name: str
    object_type: PBObjectType
    bytecode_size: int
    timestamp: datetime


@dataclass(frozen=True)
class ObjectDecompiled:
    """Event: P-code was decompiled to source."""

    compiled_object: CompiledObject
    source_object: SourceObject
    timestamp: datetime
