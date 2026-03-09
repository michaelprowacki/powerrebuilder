"""Java Adapter Implementation.

Adapts Java/JVM formats to generic modernization workflows.
Handles JAR files, class files, and JVM bytecode.
"""

import struct
import zipfile
from typing import List, Dict, Any
from io import BytesIO

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
    CodeModule,
    ArchiveExtractionError,
    DecompilationError,
    SourceParseError,
    ModelBuildError,
)


class JavaAdapter(BaseLanguageAdapter, CapabilityProvider):
    """Java/JVM language adapter.

    Handles JAR/WAR/EAR files and Java class files.
    """

    def __init__(self):
        super().__init__(SupportedLanguage.JAVA, [".jar", ".war", ".ear", ".class"])

    def get_signatures(self) -> List[LanguageSignature]:
        """Java file signatures."""
        return [
            LanguageSignature(
                magic_bytes=b"PK\x03\x04",  # ZIP/JAR signature
                extensions=[".jar", ".war", ".ear"],
                language=SupportedLanguage.JAVA,
            ),
            LanguageSignature(
                magic_bytes=b"\xca\xfe\xba\xbe",  # Java class file magic
                extensions=[".class"],
                language=SupportedLanguage.JAVA,
            ),
        ]

    def get_capabilities(self) -> AdapterCapabilities:
        """Java adapter capabilities."""
        return AdapterCapabilities(
            can_extract=True,
            can_decompile=True,
            can_parse=True,
            has_ui_support=True,  # Swing, AWT, JavaFX
            has_data_support=True,  # JDBC, JPA
            has_report_support=False,  # Limited report support
            supported_targets=[
                "flutter",
                "react",
                "vue",
                "angular",
                "spring-boot",
                "quarkus",
                "micronaut",
            ],
        )

    def parse_archive_header(
        self, archive: CompiledArchive
    ) -> Result[ArchiveHeader, ArchiveExtractionError]:
        """Parse JAR/WAR/EAR header (ZIP-based format)."""
        data = bytes(archive)

        # Check if it's a ZIP file
        if not data.startswith(b"PK"):
            # Maybe it's a raw class file
            if data.startswith(b"\xca\xfe\xba\xbe"):
                return Success(
                    ArchiveHeader(
                        format_signature="CLASS",
                        format_version="1.0",
                        compiler_version=self._get_class_version(data),
                        object_count=1,  # Single class file
                        creation_timestamp=None,
                        metadata={"type": "class_file"},
                    )
                )
            else:
                return Failure(
                    ArchiveExtractionError(
                        error_type="InvalidFormat",
                        message="Not a Java archive or class file",
                        archive_name="unknown",
                        offset=0,
                    )
                )

        # Parse as JAR (ZIP format)
        try:
            with zipfile.ZipFile(BytesIO(data), "r") as jar:
                # Count class files
                class_files = [f for f in jar.namelist() if f.endswith(".class")]

                # Check for manifest
                manifest_data = {}
                if "META-INF/MANIFEST.MF" in jar.namelist():
                    manifest = jar.read("META-INF/MANIFEST.MF").decode("utf-8")
                    # Parse manifest (simplified)
                    for line in manifest.split("\n"):
                        if ":" in line:
                            key, value = line.split(":", 1)
                            manifest_data[key.strip()] = value.strip()

                return Success(
                    ArchiveHeader(
                        format_signature="JAR",
                        format_version="1.0",
                        compiler_version=manifest_data.get("Build-Jdk", "Unknown"),
                        object_count=len(class_files),
                        creation_timestamp=manifest_data.get("Build-Date"),
                        metadata={
                            "main_class": manifest_data.get("Main-Class"),
                            "total_entries": len(jar.namelist()),
                            "manifest": manifest_data,
                        },
                    )
                )
        except zipfile.BadZipFile as e:
            return Failure(
                ArchiveExtractionError(
                    error_type="InvalidFormat",
                    message=f"Invalid JAR format: {e}",
                    archive_name="unknown",
                    offset=0,
                )
            )

    def extract_objects(
        self, archive: CompiledArchive, header: ArchiveHeader
    ) -> Result[List[CompiledObject], ArchiveExtractionError]:
        """Extract Java class files from JAR."""
        data = bytes(archive)
        objects = []

        if header.format_signature == "CLASS":
            # Single class file
            class_name = self._extract_class_name(data)
            objects.append(
                CompiledObject(
                    object_name=class_name,
                    object_type=LegacyObjectType.CLASS,
                    bytecode=Bytecode(data),
                    source=None,
                    resources=[],
                    metadata={"java_version": header.compiler_version},
                )
            )
        else:
            # JAR file
            try:
                with zipfile.ZipFile(BytesIO(data), "r") as jar:
                    for filename in jar.namelist():
                        if filename.endswith(".class"):
                            class_data = jar.read(filename)
                            class_name = filename.replace("/", ".").replace(
                                ".class", ""
                            )

                            # Determine object type
                            if "Swing" in class_name or "AWT" in class_name:
                                obj_type = LegacyObjectType.UI_CONTAINER
                            elif "DAO" in class_name or "Repository" in class_name:
                                obj_type = LegacyObjectType.DATA_MODEL
                            else:
                                obj_type = LegacyObjectType.CLASS

                            objects.append(
                                CompiledObject(
                                    object_name=class_name,
                                    object_type=obj_type,
                                    bytecode=Bytecode(class_data),
                                    source=None,
                                    resources=[],
                                    metadata={"path": filename},
                                )
                            )
            except Exception as e:
                return Failure(
                    ArchiveExtractionError(
                        error_type="ExtractError",
                        message=f"Failed to extract from JAR: {e}",
                        archive_name="unknown",
                        offset=0,
                    )
                )

        return Success(objects)

    def analyze_bytecode(
        self, bytecode: Bytecode
    ) -> Result[Dict[str, Any], DecompilationError]:
        """Analyze JVM bytecode structure."""
        data = bytes(bytecode)

        if not data.startswith(b"\xca\xfe\xba\xbe"):
            return Failure(
                DecompilationError(
                    error_type="InvalidBytecode",
                    message="Not a valid Java class file",
                    bytecode_offset=0,
                )
            )

        # Get class file version
        major = struct.unpack(">H", data[6:8])[0]
        minor = struct.unpack(">H", data[4:6])[0]

        analysis = {
            "format": "jvm_bytecode",
            "version": f"{major}.{minor}",
            "java_version": self._major_to_java_version(major),
            "size": len(data),
            "constant_pool_offset": 10,  # After magic, minor, major
        }

        return Success(analysis)

    def decompile_bytecode(
        self, bytecode: Bytecode
    ) -> Result[SourceCode, DecompilationError]:
        """Decompile JVM bytecode to Java source."""
        # In a real implementation, this would use a Java decompiler
        # like Procyon, CFR, or FernFlower
        data = bytes(bytecode)

        # Extract basic class structure (simplified)
        class_name = self._extract_class_name(data)

        # Generate placeholder Java code
        source = f"""// Decompiled Java source
// Class file size: {len(data)} bytes
// TODO: Integrate real Java decompiler

public class {class_name} {{

    // Methods and fields would be decompiled here

    public static void main(String[] args) {{
        // Main method if present
    }}
}}
"""
        return Success(SourceCode(source))

    def parse_source(self, source: SourceCode) -> Result[GenericAST, SourceParseError]:
        """Parse Java source to AST."""
        code = str(source)

        # Simplified parsing - real implementation would use JavaParser
        if "extends JFrame" in code or "extends JPanel" in code:
            node_type = ASTNodeType.UI_CONTAINER_DEF
        elif "interface" in code:
            node_type = ASTNodeType.CLASS_DEF
        elif "class" in code:
            node_type = ASTNodeType.CLASS_DEF
        else:
            node_type = ASTNodeType.MODULE

        # Extract class name (simplified)
        class_name = "UnknownClass"
        if "class " in code:
            start = code.index("class ") + 6
            end = code.find(" ", start)
            if end > start:
                class_name = code[start:end]

        ast = GenericAST(
            node_type=node_type,
            name=class_name,
            children=(),
            attributes={"source": code},
            source_location=(1, 1),
        )

        return Success(ast)

    def extract_symbols(
        self, ast: GenericAST
    ) -> Result[Dict[str, Any], ModelBuildError]:
        """Extract symbols from Java AST."""
        symbols = {}

        if ast.node_type == ASTNodeType.CLASS_DEF:
            symbols[ast.name] = {"type": "class", "properties": ast.attributes}
        elif ast.node_type == ASTNodeType.UI_CONTAINER_DEF:
            symbols[ast.name] = {"type": "ui_class", "properties": ast.attributes}

        return Success(symbols)

    def build_model(
        self, symbols: Dict[str, Any], asts: List[GenericAST]
    ) -> Result[LegacyApplicationModel, ModelBuildError]:
        """Build Java application model."""
        ui_containers = {}
        code_modules = {}

        for name, symbol in symbols.items():
            if symbol["type"] == "ui_class":
                # Swing/AWT UI class
                ui_containers[name] = UIContainer(
                    name=name,
                    container_type="jframe",
                    title=name,
                    size=(800, 600),
                    controls=[],
                    event_handlers=[],
                    properties={},
                )
            elif symbol["type"] == "class":
                # Regular Java class
                code_modules[name] = CodeModule(
                    name=name,
                    module_type="class",
                    functions=[],
                    variables=[],
                    dependencies=[],
                )

        model = LegacyApplicationModel(
            application_name="Java Application",
            source_language="java",
            ui_containers=ui_containers,
            menus={},
            data_presentations={},
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

    def _get_class_version(self, data: bytes) -> str:
        """Get Java version from class file."""
        if len(data) > 7:
            major = struct.unpack(">H", data[6:8])[0]
            return self._major_to_java_version(major)
        return "Unknown"

    def _major_to_java_version(self, major: int) -> str:
        """Convert major version number to Java version."""
        versions = {
            45: "Java 1.1",
            46: "Java 1.2",
            47: "Java 1.3",
            48: "Java 1.4",
            49: "Java 5",
            50: "Java 6",
            51: "Java 7",
            52: "Java 8",
            53: "Java 9",
            54: "Java 10",
            55: "Java 11",
            56: "Java 12",
            57: "Java 13",
            58: "Java 14",
            59: "Java 15",
            60: "Java 16",
            61: "Java 17",
            62: "Java 18",
            63: "Java 19",
            64: "Java 20",
            65: "Java 21",
        }
        return versions.get(major, f"Java Unknown (major={major})")

    def _extract_class_name(self, class_data: bytes) -> str:
        """Extract class name from class file bytecode."""
        # This is a simplified extraction
        # Real implementation would parse constant pool
        try:
            # Look for common patterns
            if b"java/lang/Object" in class_data:
                # Try to find class name before Object reference
                idx = class_data.find(b"java/lang/Object")
                # Search backward for potential class name
                for i in range(idx - 1, max(0, idx - 100), -1):
                    if class_data[i] == 0:  # String terminator
                        potential_name = class_data[i + 1 : idx].decode(
                            "utf-8", errors="ignore"
                        )
                        if "/" in potential_name:
                            return potential_name.split("/")[-1]
        except:
            pass

        return "UnknownClass"
