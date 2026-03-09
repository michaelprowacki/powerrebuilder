"""Core Domain Models - All data structures for the pipeline.

This is the single source of truth for all domain models used throughout
the PowerRebuilder pipeline. These are pure data structures with no I/O
or external dependencies.
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

# ============================================================================
# ENUMS
# ============================================================================


class PipelineStage(str, Enum):
    """Pipeline processing stages."""

    EXTRACT = "extract"
    DECOMPILE = "decompile"
    PARSE = "parse"
    MODEL = "model"
    GENERATE = "generate"
    ALL = "all"


class ObjectType(str, Enum):
    """PowerBuilder object types."""

    APPLICATION = "application"
    WINDOW = "window"
    USER_OBJECT = "user_object"
    MENU = "menu"
    FUNCTION = "function"
    DATAWINDOW = "datawindow"
    STRUCTURE = "structure"
    GLOBAL = "global"
    QUERY = "query"


class TargetLanguage(str, Enum):
    """Target generation languages."""

    FLUTTER = "flutter"
    PYTHON = "python"
    TYPESCRIPT = "typescript"
    REACT = "react"
    RUST = "rust"
    TAURI = "tauri"
    DIOXUS = "dioxus"
    VUE = "vue"
    SVELTE = "svelte"
    JAVASCRIPT = "javascript"


# ============================================================================
# EXTRACT STAGE MODELS
# ============================================================================


@dataclass
class PBLEntry:
    """Entry in a PowerBuilder Library file."""

    name: str
    type: ObjectType
    size: int
    offset: int
    timestamp: Optional[int] = None
    data: Optional[bytes] = None


@dataclass
class PBLFile:
    """PowerBuilder Library file representation."""

    path: Path
    version: str
    entries: List[PBLEntry] = field(default_factory=list)
    size: int = 0
    checksum: Optional[int] = None


@dataclass
class ExtractedObject:
    """Object extracted from PBL/PBD."""

    name: str
    type: ObjectType
    data: bytes
    source_file: str
    metadata: Dict[str, Any] = field(default_factory=dict)


# ============================================================================
# DECOMPILE STAGE MODELS
# ============================================================================


@dataclass
class PCodeInstruction:
    """P-code bytecode instruction."""

    opcode: int
    operands: List[Any] = field(default_factory=list)
    offset: int = 0
    size: int = 0


@dataclass
class PCodeFunction:
    """Decompiled P-code function."""

    name: str
    instructions: List[PCodeInstruction] = field(default_factory=list)
    locals: List[str] = field(default_factory=list)
    parameters: List[str] = field(default_factory=list)
    return_type: Optional[str] = None


@dataclass
class DecompiledSource:
    """Decompiled PowerBuilder source code."""

    object_name: str
    object_type: ObjectType
    source: str
    functions: List[PCodeFunction] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)
    line_count: int = 0

    def __post_init__(self):
        if self.line_count == 0 and self.source:
            self.line_count = len(self.source.splitlines())


# ============================================================================
# PARSE STAGE MODELS
# ============================================================================


@dataclass
class ASTNode:
    """Abstract Syntax Tree node."""

    node_type: str
    value: Any = None
    children: List["ASTNode"] = field(default_factory=list)
    attributes: Dict[str, Any] = field(default_factory=dict)
    line: Optional[int] = None
    column: Optional[int] = None

    def get_child(self, node_type: str) -> Optional["ASTNode"]:
        """Get first child of specific type."""
        for child in self.children:
            if child.node_type == node_type:
                return child
        return None

    def find_all(self, node_type: str) -> List["ASTNode"]:
        """Find all descendants of specific type."""
        results = []
        if self.node_type == node_type:
            results.append(self)
        for child in self.children:
            results.extend(child.find_all(node_type))
        return results


@dataclass
class ParsedObject:
    """Parsed PowerBuilder object with AST."""

    object_name: str
    object_type: ObjectType
    ast: ASTNode
    dependencies: List[str] = field(default_factory=list)
    parse_errors: List[str] = field(default_factory=list)


# ============================================================================
# MODEL STAGE MODELS (Semantic)
# ============================================================================


@dataclass
class Property:
    """Object property definition."""

    name: str
    type: str
    access: str = "public"
    default_value: Any = None
    is_required: bool = False
    is_array: bool = False
    documentation: Optional[str] = None


@dataclass
class Parameter:
    """Method/Event parameter."""

    name: str
    type: str
    is_optional: bool = False
    default_value: Any = None
    is_ref: bool = False
    is_array: bool = False


@dataclass
class Method:
    """Object method definition."""

    name: str
    return_type: Optional[str] = None
    parameters: List[Parameter] = field(default_factory=list)
    access: str = "public"
    body: Optional[str] = None
    is_abstract: bool = False
    is_static: bool = False
    documentation: Optional[str] = None


@dataclass
class Event:
    """Object event definition."""

    name: str
    parameters: List[Parameter] = field(default_factory=list)
    body: Optional[str] = None
    triggers: List[str] = field(default_factory=list)


@dataclass
class SemanticObject:
    """High-level semantic model of a PowerBuilder object."""

    name: str
    type: ObjectType
    parent: Optional[str] = None
    properties: List[Property] = field(default_factory=list)
    methods: List[Method] = field(default_factory=list)
    events: List[Event] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)

    def get_property(self, name: str) -> Optional[Property]:
        """Get property by name."""
        for prop in self.properties:
            if prop.name == name:
                return prop
        return None

    def get_method(self, name: str) -> Optional[Method]:
        """Get method by name."""
        for method in self.methods:
            if method.name == name:
                return method
        return None


# ============================================================================
# POWERBUILDER-SPECIFIC MODELS
# ============================================================================


@dataclass
class PBControl:
    """PowerBuilder UI control."""

    name: str
    control_type: str  # button, datawindow, textbox, etc.
    x: int = 0
    y: int = 0
    width: int = 0
    height: int = 0
    properties: Dict[str, Any] = field(default_factory=dict)
    events: Dict[str, str] = field(default_factory=dict)
    children: List["PBControl"] = field(default_factory=list)


@dataclass
class PBWindow:
    """PowerBuilder window definition."""

    name: str
    title: str = ""
    width: int = 0
    height: int = 0
    controls: List[PBControl] = field(default_factory=list)
    events: Dict[str, str] = field(default_factory=dict)
    inherits_from: Optional[str] = None


@dataclass
class DataWindowColumn:
    """DataWindow column definition."""

    name: str
    db_name: str
    data_type: str
    length: Optional[int] = None
    nullable: bool = True
    default_value: Any = None
    is_key: bool = False
    is_computed: bool = False
    expression: Optional[str] = None


@dataclass
class DataWindowDefinition:
    """Complete DataWindow definition."""

    name: str
    sql_query: Optional[str] = None
    columns: List[DataWindowColumn] = field(default_factory=list)
    presentation_style: str = "grid"  # grid, tabular, freeform, etc.
    properties: Dict[str, Any] = field(default_factory=dict)


# ============================================================================
# GENERATE STAGE MODELS
# ============================================================================


@dataclass
class GeneratedFile:
    """Generated source file."""

    path: str
    content: str
    language: TargetLanguage
    file_type: str = "source"  # source, config, asset, test


@dataclass
class GeneratedProject:
    """Complete generated project."""

    name: str
    target: TargetLanguage
    files: List[GeneratedFile] = field(default_factory=list)
    dependencies: Dict[str, str] = field(default_factory=dict)
    build_config: Dict[str, Any] = field(default_factory=dict)
    commands: Dict[str, str] = field(default_factory=dict)

    def get_source_files(self) -> List[GeneratedFile]:
        """Get all source files."""
        return [f for f in self.files if f.file_type == "source"]

    def add_file(self, path: str, content: str, file_type: str = "source") -> None:
        """Add a file to the project."""
        self.files.append(
            GeneratedFile(
                path=path, content=content, language=self.target, file_type=file_type
            )
        )


# ============================================================================
# APPLICATION MODEL
# ============================================================================


@dataclass
class ApplicationModel:
    """Complete application model."""

    name: str
    version: str = "1.0.0"
    objects: Dict[str, SemanticObject] = field(default_factory=dict)
    entry_point: Optional[str] = None
    global_functions: List[Method] = field(default_factory=list)
    global_variables: List[Property] = field(default_factory=list)

    def get_object(self, name: str) -> Optional[SemanticObject]:
        """Get object by name."""
        return self.objects.get(name)

    def get_windows(self) -> List[SemanticObject]:
        """Get all window objects."""
        return [obj for obj in self.objects.values() if obj.type == ObjectType.WINDOW]

    def get_datawindows(self) -> List[SemanticObject]:
        """Get all datawindow objects."""
        return [
            obj for obj in self.objects.values() if obj.type == ObjectType.DATAWINDOW
        ]


# ============================================================================
# OPERATION RESULT MODELS
# ============================================================================


@dataclass
class ExtractResult:
    """Extraction operation result."""

    success: bool
    extracted_count: int
    errors: List[str]
    warnings: List[str]


@dataclass
class DecompileResult:
    """Decompilation operation result."""

    success: bool
    source: str
    instructions: List[str]
    errors: List[str]
