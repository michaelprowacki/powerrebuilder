"""PowerBuilder Adapter Implementation.

Adapts PowerBuilder-specific formats to generic modernization workflows.
"""

import struct
from typing import List, Dict, Any

from src_new._core.result import Result, Success, Failure
from src_new._core.language_adapter import (
    BaseLanguageAdapter,
    SupportedLanguage,
    LanguageSignature,
    AdapterCapabilities,
    CapabilityProvider,
)
from src_new._core.legacy_modernization_types import (
    CompiledArchive,
    Bytecode,
    SourceCode,
    ArchiveHeader,
    CompiledObject,
    LegacyObjectType,
    GenericAST,
    ASTNodeType,
    LegacyApplicationModel,
    UIContainer,
    DataPresentation,
    ArchiveExtractionError,
    DecompilationError,
    SourceParseError,
    ModelBuildError,
)


class PowerBuilderAdapter(BaseLanguageAdapter, CapabilityProvider):
    """PowerBuilder-specific language adapter.

    Handles PBL/PBD files and PowerScript language.
    """

    def __init__(self):
        super().__init__(
            SupportedLanguage.POWERBUILDER, [".pbl", ".pbd", ".pba", ".pbw"]
        )

    def get_signatures(self) -> List[LanguageSignature]:
        """PowerBuilder file signatures."""
        return [
            LanguageSignature(
                magic_bytes=b"HDR*",  # PBL header signature
                extensions=[".pbl", ".pbd"],
                language=SupportedLanguage.POWERBUILDER,
            ),
            LanguageSignature(
                magic_bytes=b"PBL\x06",  # Alternative PBL signature
                extensions=[".pbl"],
                language=SupportedLanguage.POWERBUILDER,
            ),
        ]

    def get_capabilities(self) -> AdapterCapabilities:
        """PowerBuilder adapter capabilities."""
        return AdapterCapabilities(
            can_extract=True,
            can_decompile=True,
            can_parse=True,
            has_ui_support=True,  # Windows, Menus
            has_data_support=True,  # DataWindows
            has_report_support=True,  # DataWindow reports
            supported_targets=[
                "flutter",
                "tauri",
                "react",
                "vue",
                "litestar",
                "fastapi",
                "django",
            ],
        )

    def parse_archive_header(
        self, archive: CompiledArchive
    ) -> Result[ArchiveHeader, ArchiveExtractionError]:
        """Parse PBL/PBD header."""
        data = bytes(archive)

        if len(data) < 512:  # PBL headers are 512 bytes
            return Failure(
                ArchiveExtractionError(
                    error_type="InvalidSize",
                    message="Archive too small for PBL header",
                    archive_name="unknown",
                    offset=0,
                )
            )

        # Check signature
        if not (data.startswith(b"HDR*") or data.startswith(b"PBL")):
            return Failure(
                ArchiveExtractionError(
                    error_type="InvalidSignature",
                    message="Not a PowerBuilder library",
                    archive_name="unknown",
                    offset=0,
                )
            )

        # Parse PowerBuilder version and object count
        try:
            # These offsets are specific to PBL format
            version_bytes = struct.unpack("<H", data[4:6])[0]
            object_count = struct.unpack("<I", data[8:12])[0]

            # Map version bytes to PowerBuilder version
            pb_version = self._map_pb_version(version_bytes)

            return Success(
                ArchiveHeader(
                    format_signature="PBL",
                    format_version="1.0",
                    compiler_version=pb_version,
                    object_count=object_count,
                    creation_timestamp=None,
                    metadata={
                        "library_format": "PBL" if data[0:3] != b"PBD" else "PBD",
                        "optimization_level": 0,
                    },
                )
            )
        except struct.error as e:
            return Failure(
                ArchiveExtractionError(
                    error_type="ParseError",
                    message=f"Failed to parse PBL header: {e}",
                    archive_name="unknown",
                    offset=0,
                )
            )

    def extract_objects(
        self, archive: CompiledArchive, header: ArchiveHeader
    ) -> Result[List[CompiledObject], ArchiveExtractionError]:
        """Extract PowerBuilder objects from PBL."""
        data = bytes(archive)
        objects = []

        # Start after header (512 bytes)
        offset = 512

        for i in range(header.object_count):
            if offset + 256 > len(data):  # Each entry header is 256 bytes
                break

            # Extract object entry
            entry_header = data[offset : offset + 256]

            # Get object name (null-terminated string)
            name_end = entry_header.find(b"\x00", 0, 64)
            if name_end == -1:
                object_name = (
                    entry_header[:64].decode("utf-8", errors="replace").strip()
                )
            else:
                object_name = entry_header[:name_end].decode("utf-8", errors="replace")

            # Get object type
            type_byte = entry_header[64]
            object_type = self._map_object_type(type_byte)

            # Get compiled size
            try:
                compiled_size = struct.unpack("<I", entry_header[68:72])[0]
            except struct.error:
                compiled_size = 0

            # Extract P-code data
            pcode_offset = offset + 256
            if pcode_offset + compiled_size <= len(data):
                pcode = data[pcode_offset : pcode_offset + compiled_size]
            else:
                pcode = b""

            # Create compiled object
            objects.append(
                CompiledObject(
                    object_name=object_name,
                    object_type=object_type,
                    bytecode=Bytecode(pcode) if pcode else None,
                    source=None,  # Will be decompiled
                    resources=[],
                    metadata={
                        "powerbuilder_type": self._get_pb_type_name(type_byte),
                        "compiled_size": compiled_size,
                    },
                )
            )

            # Move to next entry
            offset = pcode_offset + compiled_size
            # Align to 256-byte boundary
            if offset % 256 != 0:
                offset = ((offset // 256) + 1) * 256

        return Success(objects)

    def analyze_bytecode(
        self, bytecode: Bytecode
    ) -> Result[Dict[str, Any], DecompilationError]:
        """Analyze P-code structure."""
        data = bytes(bytecode)

        if len(data) < 16:
            return Failure(
                DecompilationError(
                    error_type="InvalidPCode",
                    message="P-code too small",
                    bytecode_offset=0,
                )
            )

        # Detect P-code version and structure
        analysis = {
            "format": "pcode",
            "version": self._detect_pcode_version(data),
            "size": len(data),
            "has_debug_info": self._has_debug_info(data),
            "entry_point": 0,
        }

        return Success(analysis)

    def decompile_bytecode(
        self, bytecode: Bytecode
    ) -> Result[SourceCode, DecompilationError]:
        """Decompile P-code to PowerScript."""
        # Simplified decompilation - real implementation would be complex
        data = bytes(bytecode)

        # For now, return a placeholder
        source = f"""// Decompiled PowerScript
// P-code size: {len(data)} bytes
// TODO: Implement full P-code decompilation

forward
global type [object_name] from [ancestor]
end type
end forward

global type [object_name] from [ancestor]
end type

// Events and functions would be decompiled here
"""
        return Success(SourceCode(source))

    def parse_source(self, source: SourceCode) -> Result[GenericAST, SourceParseError]:
        """Parse PowerScript to AST."""
        code = str(source)

        # Simplified parsing - real implementation would use proper parser
        # Check for basic PowerBuilder structures
        if "global type" in code or "window" in code:
            node_type = ASTNodeType.UI_CONTAINER_DEF
        elif "datawindow" in code:
            node_type = ASTNodeType.DATA_QUERY
        elif "function" in code:
            node_type = ASTNodeType.FUNCTION_DEF
        else:
            node_type = ASTNodeType.MODULE

        # Create simplified AST
        ast = GenericAST(
            node_type=node_type,
            name="parsed_object",
            children=(),
            attributes={"source": code},
            source_location=(1, 1),
        )

        return Success(ast)

    def extract_symbols(
        self, ast: GenericAST
    ) -> Result[Dict[str, Any], ModelBuildError]:
        """Extract symbols from PowerScript AST."""
        symbols = {}

        # Extract based on node type
        if ast.node_type == ASTNodeType.UI_CONTAINER_DEF:
            symbols[ast.name] = {"type": "window", "properties": ast.attributes}
        elif ast.node_type == ASTNodeType.DATA_QUERY:
            symbols[ast.name] = {"type": "datawindow", "properties": ast.attributes}
        elif ast.node_type == ASTNodeType.FUNCTION_DEF:
            symbols[ast.name] = {"type": "function", "properties": ast.attributes}

        return Success(symbols)

    def build_model(
        self, symbols: Dict[str, Any], asts: List[GenericAST]
    ) -> Result[LegacyApplicationModel, ModelBuildError]:
        """Build PowerBuilder application model."""
        # Categorize symbols
        ui_containers = {}
        data_presentations = {}
        code_modules = {}

        for name, symbol in symbols.items():
            if symbol["type"] == "window":
                ui_containers[name] = UIContainer(
                    name=name,
                    container_type="window",
                    title=name,
                    size=(800, 600),
                    controls=[],
                    event_handlers=[],
                    properties=symbol.get("properties", {}),
                )
            elif symbol["type"] == "datawindow":
                # Create data presentation
                data_presentations[name] = DataPresentation(
                    name=name,
                    presentation_type="grid",
                    data_source=None,
                    columns=[],
                    layout={},
                )

        # Build complete model
        model = LegacyApplicationModel(
            application_name="PowerBuilder Application",
            source_language="powerbuilder",
            ui_containers=ui_containers,
            menus={},
            data_presentations=data_presentations,
            data_sources={},
            data_models={},
            code_modules=code_modules,
            global_functions={},
            resources={},
            configurations={},
            external_libraries=[],
            database_connections=[],
        )

        return Success(model)

    # Private helper methods

    def _map_pb_version(self, version_bytes: int) -> str:
        """Map version bytes to PowerBuilder version string."""
        version_map = {
            0x0600: "PB 6.0",
            0x0700: "PB 7.0",
            0x0800: "PB 8.0",
            0x0900: "PB 9.0",
            0x0A00: "PB 10.0",
            0x0B00: "PB 11.0",
            0x0C00: "PB 12.0",
            0x0C05: "PB 12.5",
        }
        return version_map.get(version_bytes, f"PB Unknown ({version_bytes:#04x})")

    def _map_object_type(self, type_byte: int) -> LegacyObjectType:
        """Map PowerBuilder type byte to generic object type."""
        type_map = {
            0x01: LegacyObjectType.APPLICATION,
            0x02: LegacyObjectType.UI_CONTAINER,  # Window
            0x03: LegacyObjectType.CLASS,  # User Object
            0x04: LegacyObjectType.MENU,
            0x05: LegacyObjectType.FUNCTION,
            0x06: LegacyObjectType.DATA_PRESENTATION,  # DataWindow
            0x07: LegacyObjectType.DATA_MODEL,  # Structure
        }
        return type_map.get(type_byte, LegacyObjectType.MODULE)

    def _get_pb_type_name(self, type_byte: int) -> str:
        """Get PowerBuilder-specific type name."""
        names = {
            0x01: "application",
            0x02: "window",
            0x03: "userobject",
            0x04: "menu",
            0x05: "function",
            0x06: "datawindow",
            0x07: "structure",
        }
        return names.get(type_byte, "unknown")

    def _detect_pcode_version(self, data: bytes) -> str:
        """Detect P-code version from bytecode."""
        # Simplified detection
        if len(data) > 4:
            version_hint = struct.unpack("<H", data[2:4])[0]
            if version_hint in [0x0600, 0x0700, 0x0800]:
                return f"P-code {version_hint >> 8}.{version_hint & 0xFF}"
        return "P-code Unknown"

    def _has_debug_info(self, data: bytes) -> bool:
        """Check if P-code contains debug information."""
        # Look for debug markers
        return b"DEBUG" in data or b"LINE" in data
