"""Main PowerBuilder P-CODE decompiler orchestrator.

This module orchestrates the decompilation of PowerBuilder P-code files (.fun)
into PowerBuilder source code (.sru). It processes P-code files extracted from
PBL/PBD archives and MUST run BEFORE the Parse stage.

IMPORTANT: This module runs BEFORE the Parse module in the sequential pipeline:
- Extract: Produces .fun (P-code) files
- Decompile: Converts .fun → .sru (PowerBuilder source) files
- Parse: Processes .sru files → produces AST JSON

The decompilation process reconstructs readable PowerBuilder source code from
bytecode, enabling the Parse stage to process it with the grammar-based parser.

Input: P-code files (.fun) from the Extract stage
Output: PowerBuilder source files (.sru) for the Parse stage

This coordinator supports two usage patterns:
1. Simple constructor for backward compatibility (used by pipeline)
2. Dependency injection for testability and flexibility
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Any, Literal, TYPE_CHECKING

if TYPE_CHECKING:
    pass

# Import at runtime since IPostProcessor is used in class definitions
from src.decompile.core.processor import PostProcessor as IPostProcessor

# Import interfaces for dependency injection
from src.contracts.interfaces import (
    IControlFlowAnalyzer,
    IDecompilerCoordinator,
    IExpressionReconstructor,
    IObjectTypeDetector,
    IOutputFormatter,
    IOutputValidator,
    IPCodeDecoder,
    IVersionDetector,
)
from src.decompile.core.output import OutputFormatter
from src.decompile.core.processor import DecompiledOutputFilter
from src.decompile.core.validator import OutputValidator
from src.decompile.pcode.decoder import PCodeDecoderV2
from src.decompile.reconstruction.expression import ExpressionReconstructor
from src.extract.pbd.constants import BLOCK_SIZE as DEFAULT_BLOCK_SIZE
from src.extract.pbd.structures import extract_nods, extract_pbl_header
from src.extract.pbd.type_detection import ObjectTypeDetector
from src.extract.pbd.version_detection import PBVersionDetector as VersionDetector
from src.extract.pbd.version_detection import PowerBuilderVersion

from .analysis.control import ControlFlowAnalyzer
from .analyzers.parser import ObjectParser
from .analyzers.schema_generator import generate_schema_documentation
from .extractors.datawindow import extraction_manager
from .extractors.logic import BusinessLogicMapper

logger = logging.getLogger(__name__)

# Supported output formats
OutputFormat = Literal["pb", "txt", "md"]
SUPPORTED_OUTPUT_FORMATS = ["pb", "txt", "md"]
OUTPUT_FORMAT_EXTENSIONS = {
    "pb": ".pb",  # PowerBuilder source format (default)
    "txt": ".txt",  # Plain text format
    "md": ".md",  # Markdown format with syntax highlighting
}


class ExtractedFileDecompiler:
    """Decompiler for extracted P-code files (.fun, .str, .men).

    This class supports two usage patterns:
    1. Simple: ExtractedFileDecompiler(output_dir, enable_filtering, output_format)
    2. DI: ExtractedFileDecompiler(object_type_detector=..., pcode_decoder=..., etc.)
    """

    def __init__(
        self,
        output_dir: Path | IObjectTypeDetector | None = None,
        enable_filtering: bool | IPCodeDecoder = True,
        output_format: OutputFormat | IControlFlowAnalyzer = "pb",
        # DI-specific parameters
        object_type_detector: IObjectTypeDetector | None = None,
        pcode_decoder: IPCodeDecoder | None = None,
        control_flow_analyzer: IControlFlowAnalyzer | None = None,
        expression_reconstructor: IExpressionReconstructor | None = None,
        output_formatter: IOutputFormatter | None = None,
        output_validator: IOutputValidator | None = None,
        post_processor: IPostProcessor | None = None,
    ) -> None:
        """Initialize the decompiler.

        Supports two usage patterns:
        1. Simple: ExtractedFileDecompiler(output_dir, enable_filtering, output_format)
        2. DI: ExtractedFileDecompiler(object_type_detector, pcode_decoder, ...)

        Args:
            output_dir: Directory to write decompiled files (simple) or IObjectTypeDetector (DI)
        enable_filtering: Whether to apply post-processing (simple) or IPCodeDecoder (DI)
        output_format: Output format (simple) or IControlFlowAnalyzer (DI)
        object_type_detector: Object type detector service (DI only)
        pcode_decoder: P-code decoder service (DI only)
        control_flow_analyzer: Control flow analyzer service (DI only)
        expression_reconstructor: Expression reconstructor service (DI only)
        output_formatter: Output formatter service (DI only)
        output_validator: Output validator service (DI only)
        post_processor: Post processor service (DI only)
        """
        # Detect which constructor pattern is being used
        if object_type_detector is not None:
            # Dependency injection pattern
            self._init_with_services(
                object_type_detector=object_type_detector,
                pcode_decoder=pcode_decoder,
                control_flow_analyzer=control_flow_analyzer,
                expression_reconstructor=expression_reconstructor,
                output_formatter=output_formatter,
                output_validator=output_validator,
                post_processor=post_processor,
            )
        else:
            # Simple pattern for backward compatibility
            self._init_simple(output_dir, enable_filtering, output_format)

    def _init_simple(
        self,
        output_dir: Path | None,
        enable_filtering: bool,
        output_format: OutputFormat,
    ) -> None:
        """Initialize with simple constructor pattern."""
        self.output_dir = output_dir
        if output_dir:
            output_dir.mkdir(parents=True, exist_ok=True)
        self.enable_filtering = enable_filtering
        self.output_filter = DecompiledOutputFilter() if enable_filtering else None
        self.output_format = self._validate_output_format(output_format)

        # Services are None in simple mode
        self.object_type_detector = None
        self.pcode_decoder = None
        self.control_flow_analyzer = None
        self.expression_reconstructor = None
        self.output_formatter = None
        self.output_validator = None
        self.post_processor = None

    def _init_with_services(
        self,
        object_type_detector: IObjectTypeDetector,
        pcode_decoder: IPCodeDecoder | None,
        control_flow_analyzer: IControlFlowAnalyzer | None,
        expression_reconstructor: IExpressionReconstructor | None,
        output_formatter: IOutputFormatter | None,
        output_validator: IOutputValidator | None,
        post_processor: IPostProcessor | None,
    ) -> None:
        """Initialize with dependency injection pattern."""
        self.object_type_detector = object_type_detector
        self.pcode_decoder = pcode_decoder
        self.control_flow_analyzer = control_flow_analyzer
        self.expression_reconstructor = expression_reconstructor
        self.output_formatter = output_formatter
        self.output_validator = output_validator
        self.post_processor = post_processor

        # Default values for compatibility
        self.output_dir = None
        self.enable_filtering = True
        self.output_filter = None
        self.output_format = "pb"

    def _validate_output_format(self, format: str) -> OutputFormat:
        """Validate and return the output format.

        Args:
            format: The requested output format

        Returns:
            The validated output format

        Raises:
            ValueError: If the format is not supported
        """
        if format not in SUPPORTED_OUTPUT_FORMATS:
            raise ValueError(
                f"Unsupported output format: {format}. "
                f"Supported formats: {', '.join(SUPPORTED_OUTPUT_FORMATS)}",
            )
        return format

    def _format_output(self, content: str, object_name: str, file_ext: str) -> str:
        """Format the output content based on the selected output format.

        Args:
            content: The decompiled content
        object_name: Name of the object
        file_ext: Original file extension

        Returns:
            Formatted content
        """
        if self.output_format == "pb":
            # PowerBuilder format - return as-is
            return content
        if self.output_format == "txt":
            # Plain text format - add header
            object_type = {
                ".fun": "Function/User Object",
                ".str": "Structure",
                ".men": "Menu",
                ".udo": "User Object",
                ".win": "Window",
                ".apl": "Application",
                ".apf": "Application Function",
                ".mef": "Menu Function",
            }.get(
                file_ext,
                "Object",
            )

            header = f"{'=' * 60}\n"
            header += f"{object_type}: {object_name}\n"
            header += f"{'=' * 60}\n\n"
            return header + content
        if self.output_format == "md":
            # Markdown format with syntax highlighting
            object_type = {
                ".fun": "Function/User Object",
                ".str": "Structure",
                ".men": "Menu",
                ".udo": "User Object",
                ".win": "Window",
                ".apl": "Application",
                ".apf": "Application Function",
                ".mef": "Menu Function",
            }.get(
                file_ext,
                "Object",
            )

            markdown = f"# {object_type}: {object_name}\n\n"
            markdown += "```powerbuilder\n"
            markdown += content
            markdown += "\n```\n"
            return markdown
        # Always return content as fallback instead of None
        return content

    def decompile_extracted_file(self, file_path: Path) -> bool:
        """Decompile an extracted P-code file.

        Args:
            file_path: Path to the extracted file (.fun, .str, .men)

        Returns:
            True if successful, False otherwise
        """
        logger.info(
            "Decompiling extracted file: %s (output_dir: %s)",
            file_path,
            self.output_dir,
        )

        try:
            # Read the file
            with file_path.open("rb") as f:
                data = f.read()

            if len(data) == 0:
                logger.warning("Empty file: %s", file_path)
                return False

            # Get object name from filename
            object_name = file_path.stem
            file_ext = file_path.suffix.lower()
            # Pass full filename with extension for proper type detection
            full_object_name = file_path.name

            # Parse the PowerBuilder object to extract P-code
            pb_object = ObjectParser.parse_object(data, object_name)

            if not pb_object:
                logger.warning("Failed to parse object structure in %s", file_path)
                return self._generate_stub(
                    file_path,
                    "Failed to parse object structure",
                )

            if pb_object.pcode_offset < 0 or not pb_object.pcode_data:
                logger.warning(
                    "No P-code found in object %s (offset: %s, data_len: %s)",
                    file_path,
                    pb_object.pcode_offset,
                    len(pb_object.pcode_data) if pb_object.pcode_data else 0,
                )
                return self._generate_stub(file_path, "No P-code found in object")

            # Ensure pcode_offset is an integer for logging
            try:
                pcode_offset = int(pb_object.pcode_offset)
                pcode_length = int(pb_object.pcode_length)
            except (ValueError, TypeError):
                logger.error(
                    "Invalid P-code offset/length types in %s: offset=%r (type=%s), length=%r (type=%s)",
                    file_path,
                    pb_object.pcode_offset,
                    type(pb_object.pcode_offset).__name__,
                    pb_object.pcode_length,
                    type(pb_object.pcode_length).__name__,
                )
                return self._generate_stub(file_path, "Invalid P-code offset/length")

            logger.info(
                "Found P-code at offset 0x%04x, length %d bytes",
                pcode_offset,
                pcode_length,
            )

            # Detect PowerBuilder version from file structure and metadata
            version = self._detect_version_from_file(file_path, pb_object, data)
            logger.info("Using PowerBuilder version: %s", version)

            # Create P-code info object to pass section information
            pcode_info = None
            if hasattr(pb_object, "pcode_sections") and pb_object.pcode_sections:
                # Create a simple object to hold section info

                class PCodeInfo:
                    def __init__(self, sections) -> None:
                        self.sections = sections

                pcode_info = PCodeInfo(pb_object.pcode_sections)
                logger.info(
                    "Passing %d P-code sections to decoder",
                    len(pb_object.pcode_sections),
                )

            # Decode P-code with proper version detection
            if self.pcode_decoder:
                decoded_obj = self.pcode_decoder.decode_pcode_section(
                    pb_object.pcode_data,
                    full_object_name,  # Use full name with extension for type detection
                    pcode_info,  # Pass the P-code section information
                )
            else:
                decoder = PCodeDecoderV2(version)
                decoded_obj = decoder.decode_pcode_section(
                    pb_object.pcode_data,
                    full_object_name,  # Use full name with extension for type detection
                    pcode_info,  # Pass the P-code section information
                )

            if not decoded_obj.instructions:
                logger.warning("No instructions decoded from %s", file_path)
                return self._generate_stub(file_path, "No instructions decoded")

            logger.debug(
                "Decoded %d instructions from %s",
                len(decoded_obj.instructions),
                file_path,
            )

            # Step 5: Analyze control flow
            if self.control_flow_analyzer:
                if hasattr(self.control_flow_analyzer, "analyze_legacy"):
                    # Use legacy method for backward compatibility
                    control_blocks = self.control_flow_analyzer.analyze_legacy(
                        decoded_obj.instructions
                    )
                else:
                    # Fallback for interface compliance - extract blocks from dict result
                    result = self.control_flow_analyzer.analyze(
                        decoded_obj.instructions
                    )
                    if isinstance(result, dict) and "blocks" in result:
                        # Convert dict blocks back to ControlBlock objects
                        control_blocks = self._convert_dict_blocks_to_objects(
                            result["blocks"]
                        )
                    else:
                        control_blocks = []
            else:
                cf_analyzer = ControlFlowAnalyzer()
                control_blocks = cf_analyzer.analyze_legacy(decoded_obj.instructions)

            # Step 6: Reconstruct expressions using stack emulation
            if self.expression_reconstructor:
                for block in control_blocks:
                    try:
                        self.expression_reconstructor.emulate_block(block)
                    except (ValueError, KeyError, AttributeError) as e:
                        logger.warning(
                            "Expression reconstruction failed for block in %s: %s",
                            file_path,
                            e,
                        )
                        # Continue with other blocks
            else:
                emulator = ExpressionReconstructor()
                for block in control_blocks:
                    try:
                        emulator.emulate_block(block)
                    except (ValueError, KeyError, AttributeError) as e:
                        logger.warning(
                            "Expression reconstruction failed for block in %s: %s",
                            file_path,
                            e,
                        )
                        # Continue with other blocks

            # Step 7: Generate output using advanced formatter
            if self.output_formatter:
                # Use injected formatter
                output_lines = self.output_formatter.format_object(
                    decoded_obj, control_blocks, str(file_path)
                )
            else:
                # Use OutputFormatter which supports control blocks with reconstructed expressions
                formatter = OutputFormatter()
                output_lines = formatter.format_object(
                    decoded_obj, control_blocks, str(file_path)
                )

            # Validate that we got output
            if not output_lines:
                logger.warning("OutputFormatter produced no output for %s", file_path)
                return self._generate_stub(
                    file_path, "Output formatter produced no output"
                )

            logger.debug(
                "Generated %d lines of output for %s", len(output_lines), file_path
            )

            # Step 8: Validate the output format
            validator = None
            if self.output_validator:
                validator = self.output_validator
                is_valid, validation_errors = validator.validate(output_lines)
            else:
                validator = OutputValidator()
                is_valid, validation_errors = validator.validate(output_lines)

            if not is_valid:
                logger.warning("Output validation failed for %s:", file_path)
                logger.warning(validator.format_errors(validation_errors))
                # Continue anyway - validation is advisory
            elif validation_errors:
                # Just warnings
                logger.debug("Output validation warnings for %s:", file_path)
                logger.debug(validator.format_errors(validation_errors))

            # Determine output file extension based on format
            if self.output_format == "pb":
                # PowerBuilder source format - use appropriate extension
                output_ext = {
                    ".fun": ".sru",  # Functions -> user objects
                    ".udo": ".sru",  # User Defined Objects
                    ".str": ".srs",  # Structures
                    ".men": ".srm",  # Menus
                    ".win": ".srw",  # Windows
                    ".apl": ".sra",  # Applications
                    ".apf": ".sra",  # Application functions
                    ".dwo": ".srd",  # DataWindows
                    ".mef": ".srf",  # Menu functions
                }.get(
                    file_ext,
                    ".sru",  # Default to user object for unknown types
                )
            else:
                # Other formats use their standard extension
                output_ext = OUTPUT_FORMAT_EXTENSIONS[self.output_format]

            # Write output
            if self.output_dir:
                # Preserve directory structure by creating parallel structure
                # Extract structure is typically:
                # data/output/current/extracted/pbd_name/pbd_name/file.fun
                # We want: data/output/current/decompiled/pbd_name/pbd_name/file.sru
                try:
                    # Find the 'extracted' directory in the path
                    parts = file_path.parts
                    extracted_idx = -1
                    for i, part in enumerate(parts):
                        if part == "extracted":
                            extracted_idx = i
                            break

                    if extracted_idx >= 0:
                        # Get the relative path after 'extracted'
                        relative_parts = parts[extracted_idx + 1 :]
                        relative_path = (
                            Path(*relative_parts) if relative_parts else Path()
                        )
                        output_path = (
                            self.output_dir
                            / relative_path.parent
                            / f"{object_name}{output_ext}"
                        )
                    else:
                        # Fallback: just use the filename
                        output_path = self.output_dir / f"{object_name}{output_ext}"
                except (ValueError, IndexError) as e:
                    logger.warning("Could not preserve directory structure: %s", e)
                    output_path = self.output_dir / f"{object_name}{output_ext}"

                output_path.parent.mkdir(parents=True, exist_ok=True)

                # Apply filtering if enabled
                content = "\n".join(output_lines)
                if self.enable_filtering and self.output_filter:
                    content = self.output_filter.filter_output(content)

                # Format content based on output format
                content = self._format_output(content, object_name, file_ext)

                # Validate content before writing
                if content is None:
                    logger.error(
                        "_format_output returned None for %s (format: %s, ext: %s)",
                        object_name,
                        self.output_format,
                        file_ext,
                    )
                    content = "\n".join(output_lines)  # Fallback to unformatted content

                logger.debug("Writing %d characters to %s", len(content), output_path)
                with output_path.open("w", encoding="utf-8") as f:
                    f.write(content)

                # Verify file was written successfully
                if output_path.exists() and output_path.stat().st_size > 0:
                    logger.info(
                        "Wrote decompiled source to %s (%d bytes)",
                        output_path,
                        output_path.stat().st_size,
                    )
                else:
                    logger.error(
                        "Failed to write output file %s or file is empty", output_path
                    )
                    return False
            else:
                # Output to stdout
                try:
                    print(formatted_output)
                    logger.info(
                        "Printed decompiled source to stdout (%d characters)",
                        len(formatted_output),
                    )
                except Exception as e:
                    logger.error("Failed to print to stdout: %s", e)
                    return False

            return True

        except Exception as e:
            logger.exception("Failed to decompile %s: %s", file_path, e, exc_info=True)
            return False

    def _detect_version_from_file(
        self, file_path: Path, pb_object: Any, raw_data: bytes
    ) -> PowerBuilderVersion:
        """Detect PowerBuilder version from file content and metadata.

        Args:
            file_path: Path to the file being processed
            pb_object: Parsed PowerBuilder object
            raw_data: Raw file data for analysis

        Returns:
            Detected PowerBuilder version with fallback to sensible default
        """
        try:
            # First try to detect from P-code patterns if available
            if pb_object and hasattr(pb_object, "pcode_data") and pb_object.pcode_data:
                version = VersionDetector.detect_from_opcode_patterns(
                    pb_object.pcode_data
                )
                if version:
                    logger.info("Detected version %s from P-code patterns", version)
                    return version

            # Try detecting from file header if it contains PBD-like structure
            if len(raw_data) >= 8:
                version = VersionDetector.detect_from_header(raw_data[:8])
                if version:
                    logger.info("Detected version %s from file header", version)
                    return version

            # Check for version-specific signatures in the data
            version_hints = self._analyze_version_hints(raw_data, file_path)
            if version_hints:
                logger.info("Detected version %s from content analysis", version_hints)
                return version_hints

        except Exception as e:
            logger.debug("Version detection failed: %s", e)

        # Fallback: Use intelligent default based on file characteristics
        default_version = self._get_default_version_for_file(file_path, raw_data)
        logger.info("Using default version %s for %s", default_version, file_path.name)
        return default_version

    def _analyze_version_hints(
        self, raw_data: bytes, file_path: Path
    ) -> PowerBuilderVersion | None:
        """Analyze file content for version hints.

        Args:
            raw_data: Raw file data
            file_path: File path for context

        Returns:
            Detected version or None
        """
        try:
            # Look for Unicode patterns (suggests PB 10+)
            unicode_indicators = [
                b"\x00H\x00D\x00R",  # Unicode HDR
                b"\x00N\x00O\x00D",  # Unicode NOD
                b"\x00E\x00N\x00T",  # Unicode ENT
            ]

            has_unicode = any(indicator in raw_data for indicator in unicode_indicators)

            # Look for extended opcodes (suggests PB 8+)
            extended_opcodes = [0xEB, 0xF0, 0xFA]  # Extended instruction set
            has_extended = any(opcode in raw_data for opcode in extended_opcodes)

            # Check file size patterns (larger files often from newer versions)
            file_size = len(raw_data)

            if has_unicode and file_size > 1024 * 1024:  # Large Unicode file
                return PowerBuilderVersion(12, 0, True)
            if has_unicode:
                return PowerBuilderVersion(10, 5, True)
            if has_extended:
                return PowerBuilderVersion(8, 0, False)
            if file_size > 512 * 1024:  # Larger files suggest newer versions
                return PowerBuilderVersion(7, 0, False)

        except Exception as e:
            logger.debug("Version hint analysis failed: %s", e)

        return None

    def _get_default_version_for_file(
        self, file_path: Path, raw_data: bytes
    ) -> PowerBuilderVersion:
        """Get intelligent default version based on file characteristics.

        Args:
            file_path: File path for context
            raw_data: Raw file data

        Returns:
            Appropriate default version
        """
        file_size = len(raw_data)

        # Very large files are likely from modern PowerBuilder
        if file_size > 2 * 1024 * 1024:  # > 2MB
            return PowerBuilderVersion(11, 5, True)

        # Medium files could be PB 10.x
        if file_size > 512 * 1024:  # > 512KB
            return PowerBuilderVersion(10, 5, True)

        # Smaller files might be from older versions, but default to Unicode-capable
        return PowerBuilderVersion(10, 0, True)

    def _generate_stub(self, file_path: Path, reason: str) -> bool:
        """Generate a stub file for objects that couldn't be decompiled.

        Args:
            file_path: Path to the original file
        reason: Reason for failure

        Returns:
            True (always succeeds)
        """
        object_name = file_path.stem
        file_ext = file_path.suffix.lower()

        # Generate appropriate stub based on file type
        if file_ext == ".fun":
            stub_content = f"""// Function: {object_name}
// Generated stub - {reason}
// Original file: {file_path}

function {object_name}()
    // TODO: Implementation not available
    // This function's P-code could not be decompiled
end function
"""
        elif file_ext == ".str":
            stub_content = f"""// Structure: {object_name}
// Generated stub - {reason}
// Original file: {file_path}

global type {object_name} from structure
    // TODO: Structure definition not available
end type
"""
        elif file_ext == ".men":
            stub_content = f"""// Menu: {object_name}
// Generated stub - {reason}
// Original file: {file_path}

global type {object_name} from menu
end type
global {object_name} {object_name}

on {object_name}.create
    // TODO: Menu implementation not available
end on

on {object_name}.destroy
    // TODO: Cleanup code not available
end on
"""
        else:
            stub_content = f"""// Object: {object_name}
// Generated stub - {reason}
// Original file: {file_path}
// Type: {file_ext}

// TODO: Implementation not available
"""

        # Determine output extension
        output_ext = {
            ".fun": ".sru",
            ".str": ".srs",
            ".men": ".srm",
        }.get(
            file_ext,
            ".pb",
        )

        if self.output_dir:
            # Use same path logic as main decompile method
            try:
                parts = file_path.parts
                extracted_idx = -1
                for i, part in enumerate(parts):
                    if part == "extracted":
                        extracted_idx = i
                        break

                if extracted_idx >= 0:
                    relative_parts = parts[extracted_idx + 1 :]
                    relative_path = Path(*relative_parts) if relative_parts else Path()
                    output_path = (
                        self.output_dir
                        / relative_path.parent
                        / f"{object_name}{output_ext}"
                    )
                else:
                    output_path = self.output_dir / f"{object_name}{output_ext}"
            except (ValueError, IndexError) as e:
                logger.warning("Could not preserve directory structure: %s", e)
                output_path = self.output_dir / f"{object_name}{output_ext}"

            output_path.parent.mkdir(parents=True, exist_ok=True)

            with output_path.open("w", encoding="utf-8") as f:
                f.write(stub_content)
            logger.info("Wrote stub file to %s", output_path)
        else:
            # Output stub to stdout
            try:
                print(stub_content)
                logger.info(
                    "Printed stub content to stdout (%d characters)", len(stub_content)
                )
            except Exception as e:
                logger.error("Failed to print stub to stdout: %s", e)
                return False

        return True


class PowerBuilderDecompiler:
    """Main orchestrator for PowerBuilder decompilation."""

    def __init__(
        self, output_dir: Path | None = None, output_format: OutputFormat = "pb"
    ) -> None:
        """Initialize the decompiler.

        Args:
            output_dir: Directory to write decompiled files (None for stdout only)
            output_format: Output format ("pb", "txt", or "md")
        """
        self.output_dir = output_dir
        if output_dir:
            output_dir.mkdir(parents=True, exist_ok=True)
        self.output_format = self._validate_output_format(output_format)

    def _validate_output_format(self, format: str) -> str:
        """Validate and return the output format.

        Args:
            format: The requested output format

        Returns:
            The validated output format

        Raises:
            ValueError: If the format is not supported
        """
        if format not in SUPPORTED_OUTPUT_FORMATS:
            raise ValueError(
                f"Unsupported output format: {format}. "
                f"Supported formats: {', '.join(SUPPORTED_OUTPUT_FORMATS)}",
            )
        return format

    def decompile_pbd(self, pbd_path: Path) -> bool:
        """Decompile a complete PBD file.

        Args:
            pbd_path: Path to the PBD file

        Returns:
            True if successful, False otherwise
        """
        logger.info("Starting decompilation of %s", pbd_path)

        try:
            with Path(pbd_path).open("rb") as pbd_file:
                # Step 1: Parse header and detect version
                logger.info("Parsing PBD header...")
                header = extract_pbl_header(
                    pbd_file,
                    block_size=DEFAULT_BLOCK_SIZE,
                    file_path_for_error_log=str(pbd_path),
                )

                # Detect PowerBuilder version
                version = VersionDetector.detect_from_file(pbd_file)
                if version is None:
                    version = VersionDetector.get_default_version(header.is_unicode)
                    logger.warning(
                        "Could not detect version, using default: %s", version
                    )
                else:
                    logger.info("Detected PowerBuilder version: %s", version)

                # Step 2: Parse object directory
                logger.info("Parsing object directory...")
                nodes = extract_nods(
                    pbd_file,
                    header.is_unicode,
                    header.first_nod_offset,
                    DEFAULT_BLOCK_SIZE,
                )

                # Count total objects
                total_objects = sum(
                    len(node.entry_defs) if node and hasattr(node, "entry_defs") else 0
                    for node in nodes
                )
                logger.info("Found %s objects in PBD", total_objects)

                # Step 3: Process each object
                decompiled_count = 0
                for node in nodes:
                    if node and hasattr(node, "entry_defs") and node.entry_defs:
                        for entry in node.entry_defs:
                            if entry:
                                success = self._decompile_object(
                                    pbd_file,
                                    entry,
                                    version,
                                    pbd_path.name,
                                )
                                if success:
                                    decompiled_count += 1

                logger.info(
                    "Successfully decompiled %d/%d objects",
                    decompiled_count,
                    total_objects,
                )
                return decompiled_count > 0

        except Exception as e:
            logger.exception("Failed to decompile %s: %s", pbd_path, e, exc_info=True)
            return False

    def _decompile_object(
        self,
        pbd_file,
        entry,
        version: PowerBuilderVersion,
        pbd_name: str,
    ) -> bool:
        """Decompile a single object from the PBD.

        Args:
            pbd_file: Open PBD file handle
            entry: Entry definition for the object
            version: PowerBuilder version
            pbd_name: Name of the PBD file

        Returns:
            True if successful, False otherwise
        """
        try:
            object_name = entry.objectname
            logger.debug("Decompiling %s", object_name)

            # Use object type detector to classify the object
            if self.object_type_detector:
                obj_type_name, contains_pcode = (
                    self.object_type_detector.get_object_info(
                        object_name,
                    )
                )
            else:
                obj_type_name, contains_pcode = (
                    ObjectTypeDetector.get_object_info_extended(
                        object_name,
                    )
                )

            # Check if it's a DataWindow (special handling)
            if ObjectTypeDetector.is_datawindow(object_name):
                logger.debug(
                    "Skipping DataWindow %s - handled during extraction", object_name
                )
                return False

            # Check if it's a Structure (special handling)
            if ObjectTypeDetector.is_structure(object_name):
                logger.debug(
                    "Skipping Structure %s - no P-code to decompile", object_name
                )
                return False

            # Skip objects that don't contain P-code
            if not contains_pcode:
                logger.debug(
                    "Skipping %s %s - no P-code expected", obj_type_name, object_name
                )
                return False

            # Step 4: Extract and decode P-code
            decoder = PCodeDecoderV2(version)
            decoded_obj = decoder.decode_pbd_object(
                pbd_file,
                entry.offset,
                entry.objectsize,
                object_name,
            )

            if not decoded_obj.instructions:
                logger.warning("No P-code found in %s", object_name)
                return False

            # Step 5: Analyze control flow
            cf_analyzer = ControlFlowAnalyzer()
            control_blocks = cf_analyzer.analyze_legacy(decoded_obj.instructions)

            # Step 6: Reconstruct expressions using stack emulation
            emulator = ExpressionReconstructor()
            for block in control_blocks:
                emulator.emulate_block(block)

            # Step 7: Generate output
            formatter = OutputFormatter()
            output_lines = formatter.format_object(
                decoded_obj, control_blocks, pbd_name
            )

            # Write or print output
            if self.output_dir:
                output_path = self.output_dir / f"{object_name}.pb"
                with output_path.open("w", encoding="utf-8") as f:
                    f.write("\n".join(output_lines))
                logger.debug("Wrote %s", output_path)
            else:
                # Print to stdout
                try:
                    output_content = "\n".join(output_lines)
                    print(output_content)
                    logger.debug(
                        "Printed object %s to stdout (%d lines)",
                        object_name,
                        len(output_lines),
                    )
                except Exception as e:
                    logger.error(
                        "Failed to print object %s to stdout: %s", object_name, e
                    )
                    return False

            return True

        except Exception as e:
            logger.exception("Failed to decompile %s: %s", entry.objectname, e)
            return False

    def _extract_datawindow(self, pbd_file, entry, pbd_name: str) -> bool:
        """Extract DataWindow syntax directly.

        Args:
            pbd_file: Open PBD file handle
        entry: Entry definition for the DataWindow
        pbd_name: Name of the PBD file

        Returns:
            True if successful, False otherwise
        """
        try:
            # Seek to DataWindow data
            pbd_file.seek(entry.offset)
            dw_data = pbd_file.read(entry.objectsize)

            # Use the enhanced DataWindow extraction manager for better success rate
            syntax, success = extraction_manager.extract_from_pbd_object(
                dw_data, entry.objectname
            )

            if success and syntax:
                # Successfully extracted syntax
                output_text = f"""// DataWindow: {entry.objectname}
// From: {pbd_name}
// Type: DataWindow
// Successfully extracted DataWindow syntax

{syntax}
"""

                if self.output_dir:
                    # Save as .sql to indicate it's DataWindow SQL/syntax
                    output_path = self.output_dir / f"{entry.objectname}.sql"
                    with output_path.open("w", encoding="utf-8") as f:
                        f.write(output_text)
                    logger.debug("Wrote DataWindow syntax to %s", output_path)
                else:
                    # Print to stdout
                    try:
                        print(output_text)
                        logger.debug(
                            "Printed DataWindow %s syntax to stdout", entry.objectname
                        )
                    except Exception as e:
                        logger.error(
                            "Failed to print DataWindow %s to stdout: %s",
                            entry.objectname,
                            e,
                        )
                        return False

                return True
            # Could not extract syntax - check if it's a binary DataWindow
            if dw_data.startswith(b"DAT*"):
                # Extract version info
                pdw_version = "Unknown"
                if b"PDW" in dw_data[:50]:
                    pdw_pos = dw_data.find(b"PDW")
                    pdw_version = (
                        dw_data[pdw_pos : pdw_pos + 8]
                        .decode(
                            "ascii",
                            errors="ignore",
                        )
                        .strip("\x00")
                    )

                output_text = f"""// DataWindow: {entry.objectname}
// Format: Binary/Compiled DataWindow ({pdw_version})
//
// Unable to extract DataWindow syntax from this binary format.
// This could be due to:
// 1. The DataWindow is compiled without embedded source
// 2. The syntax is in an unknown format or location
// 3. The syntax data is compressed or encrypted
//
// Binary format details:
// - Magic: DAT*
// - Size: {entry.objectsize} bytes
// - PowerBuilder Version: {pdw_version}
"""

                if self.output_dir:
                    output_path = self.output_dir / f"{entry.objectname}.txt"
                    with output_path.open("w", encoding="utf-8") as f:
                        f.write(output_text)
                    logger.debug("Wrote DataWindow metadata to %s", output_path)
                else:
                    # Print to stdout
                    try:
                        print(output_text)
                        logger.debug(
                            "Printed DataWindow %s metadata to stdout", entry.objectname
                        )
                    except Exception as e:
                        logger.error(
                            "Failed to print DataWindow %s metadata to stdout: %s",
                            entry.objectname,
                            e,
                        )
                        return False

                return True
            logger.warning("Unknown DataWindow format for %s", entry.objectname)
            return False

        except Exception as e:
            logger.exception("Failed to extract DataWindow %s: %s", entry.objectname, e)
            return False


def extract_database_schema(
    project_dir: str | Path,
    output_dir: str | Path,
    output_format: str = "markdown",
    progress=None,
) -> None:
    """Extract and document database schema from a PowerBuilder project.

    Args:
        project_dir: Directory containing PowerBuilder source files
    output_dir: Directory to write documentation
    output_format: Documentation format ("markdown", "html", "json")
    progress: Progress callback (optional)
    """
    project_path = Path(project_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    logger.info("Extracting database schema from: %s", project_path)

    try:
        # Create the mapper (which includes schema extractor)
        mapper = BusinessLogicMapper()

        # Map the entire project
        if progress:
            with progress.operation_context("Analyzing database schema", total=100):
                progress.update_operation(10, "Scanning for SQL statements...")
                mapping_data = mapper.map_project(project_path)

                progress.update_operation(80, "Generating documentation...")
                # Generate documentation
                doc_filename = f"database_schema_documentation.{output_format}"
                if output_format == "html":
                    doc_filename = "database_schema_documentation.html"
                elif output_format == "json":
                    doc_filename = "database_schema_documentation.json"

                doc_path = output_path / doc_filename
                generate_schema_documentation(
                    mapping_data,
                    output_format=output_format,
                    output_path=doc_path,
                )

                progress.update_operation(100, "Schema extraction complete")
        else:
            mapping_data = mapper.map_project(project_path)

            # Generate documentation
            doc_filename = f"database_schema_documentation.{output_format}"
            if output_format == "html":
                doc_filename = "database_schema_documentation.html"
            elif output_format == "json":
                doc_filename = "database_schema_documentation.json"

            doc_path = output_path / doc_filename
            generate_schema_documentation(
                mapping_data,
                output_format=output_format,
                output_path=doc_path,
            )

        # Also save the raw mapping data as JSON for further processing
        raw_data_path = output_path / "database_schema_raw.json"
        import json

        with Path(raw_data_path).open("w", encoding="utf-8") as f:
            json.dump(mapping_data, f, indent=2, default=str)

        logger.info("Database schema documentation saved to: %s", doc_path)
        logger.info("Raw schema data saved to: %s", raw_data_path)

        # Print summary statistics
        db_stats = mapping_data.get("database_schema", {}).get("statistics", {})
        logic_stats = mapping_data.get("statistics", {})

        logger.info("Schema Extraction Summary:")
        logger.info("  - Total tables: %d", db_stats.get("total_tables", 0))
        logger.info("  - Total columns: %d", db_stats.get("total_columns", 0))
        logger.info(
            "  - Total relationships: %d", db_stats.get("total_relationships", 0)
        )
        logger.info(
            "  - Total business functions: %d", logic_stats.get("total_functions", 0)
        )
        logger.info(
            "  - Total UI elements: %d", logic_stats.get("total_ui_elements", 0)
        )
        logger.info("  - Total data flows: %d", logic_stats.get("total_data_flows", 0))

    except Exception as e:
        logger.exception("Failed to extract database schema: %s", e, exc_info=True)
        raise


def decompile_directory(
    input_dir: str | Path,
    output_dir: str | Path,
    progress=None,
    output_format: OutputFormat = "pb",
) -> None:
    """Decompile all extracted P-code files in a directory structure.

    Args:
        input_dir: Directory containing extracted P-code files (.fun, .str, .men)
    output_dir: Directory to write decompiled source files
    progress: Progress callback (optional)
    output_format: Output format ("pb", "txt", or "md")
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    logger.info("Decompiling extracted files from: %s -> %s", input_path, output_path)

    decompiled_count = 0
    failed_count = 0

    if not input_path.exists() or not input_path.is_dir():
        logger.exception("Input directory not found: %s", input_path)
        return

    # Create a decompiler instance with output format
    decompiler = ExtractedFileDecompiler(output_path, output_format=output_format)

    # Process only files that contain P-code
    # Note: .str files are structures and don't contain P-code - removing from list
    pcode_extensions = [".fun", ".men", ".mef", ".apf"]
    processed_files = set()

    # First, collect all files to process
    all_pcode_files: list[Path] = []
    for ext in pcode_extensions:
        all_pcode_files.extend(input_path.rglob(f"*{ext}"))

    # Also look for compiled user objects and windows
    # that might not have standard extensions
    for pattern in ["*.udo", "*.win"]:
        all_pcode_files.extend(input_path.rglob(pattern))

    total_files = len(all_pcode_files)

    # Create operation context if progress is provided
    if progress:
        with progress.operation_context(
            "Decompiling functions",
            total=total_files,
        ):
            for i, pcode_file in enumerate(all_pcode_files):
                if pcode_file in processed_files:
                    continue
                processed_files.add(pcode_file)

                # Double-check with object type detector
                if not ObjectTypeDetector.should_decompile(str(pcode_file.name)):
                    logger.debug(
                        "Skipping %s - not a decompilable file", pcode_file.name
                    )
                    continue

                progress.update_operation(i + 1, f"Decompiling {pcode_file.name}")
                logger.info("Processing: %s", pcode_file)
                try:
                    if decompiler.decompile_extracted_file(pcode_file):
                        decompiled_count += 1
                    else:
                        failed_count += 1
                except Exception as e:
                    logger.exception("Failed to decompile %s: %s", pcode_file, e)
                    failed_count += 1
    else:
        for pcode_file in all_pcode_files:
            if pcode_file in processed_files:
                continue
            processed_files.add(pcode_file)

            # Double-check with object type detector
            if not ObjectTypeDetector.should_decompile(str(pcode_file.name)):
                logger.debug("Skipping %s - not a decompilable file", pcode_file.name)
                continue

            logger.info("Processing: %s", pcode_file)
            try:
                if decompiler.decompile_extracted_file(pcode_file):
                    decompiled_count += 1
                else:
                    failed_count += 1
            except Exception as e:
                logger.exception("Failed to decompile %s: %s", pcode_file, e)
                failed_count += 1

    logger.info(
        "Decompilation complete. Success: %d, Failed: %d",
        decompiled_count,
        failed_count,
    )


class DecompileCoordinator(IDecompilerCoordinator):
    """Main coordinator for PowerBuilder decompilation operations.

    This class provides a unified interface for decompiling P-code files from
    PowerBuilder binary files. It supports two usage patterns:

    1. Simple: DecompileCoordinator(input_dir, output_dir)
    2. DI: DecompileCoordinator(object_type_detector=..., pcode_decoder=..., etc.)

    The simple mode maintains backward compatibility with the pipeline,
    while DI mode allows for better testability and flexibility.
    """

    def __init__(
        self,
        input_dir: str | Path | IObjectTypeDetector | None = None,
        output_dir: str | Path | IVersionDetector | None = None,
        enable_byte_recovery: bool | IPCodeDecoder | None = False,
        output_format: OutputFormat | IControlFlowAnalyzer | None = "pb",
        enable_filtering: bool | IExpressionReconstructor | None = True,
        # DI-specific parameters
        object_type_detector: IObjectTypeDetector | None = None,
        version_detector: IVersionDetector | None = None,
        pcode_decoder: IPCodeDecoder | None = None,
        control_flow_analyzer: IControlFlowAnalyzer | None = None,
        expression_reconstructor: IExpressionReconstructor | None = None,
        output_formatter: IOutputFormatter | None = None,
        output_validator: IOutputValidator | None = None,
    ) -> None:
        """Initialize the decompile coordinator.

        Supports two usage patterns:
        1. Simple: DecompileCoordinator(input_dir, output_dir, enable_byte_recovery, output_format, enable_filtering)
        2. DI: DecompileCoordinator(object_type_detector, version_detector, pcode_decoder, ...)

        Args:
            input_dir: Input directory (simple) or IObjectTypeDetector (DI)
            output_dir: Output directory (simple) or IVersionDetector (DI)
            enable_byte_recovery: Enable recovery (simple) or IPCodeDecoder (DI)
            output_format: Output format (simple) or IControlFlowAnalyzer (DI)
        enable_filtering: Enable filtering (simple) or IExpressionReconstructor (DI)
        object_type_detector: Object type detector service (DI only)
        version_detector: Version detector service (DI only)
        pcode_decoder: P-code decoder service (DI only)
        control_flow_analyzer: Control flow analyzer service (DI only)
        expression_reconstructor: Expression reconstructor service (DI only)
        output_formatter: Output formatter service (DI only)
        output_validator: Output validator service (DI only)
        """
        # Detect which constructor pattern is being used
        if object_type_detector is not None:
            # Dependency injection pattern
            self._init_with_services(
                object_type_detector=object_type_detector,
                version_detector=version_detector,
                pcode_decoder=pcode_decoder,
                control_flow_analyzer=control_flow_analyzer,
                expression_reconstructor=expression_reconstructor,
                output_formatter=output_formatter,
                output_validator=output_validator,
            )
        else:
            # Simple pattern for backward compatibility
            self._init_simple(
                input_dir,
                output_dir,
                enable_byte_recovery,
                output_format,
                enable_filtering,
            )

    def _init_simple(
        self,
        input_dir: str | Path | None,
        output_dir: str | Path | None,
        enable_byte_recovery: bool,
        output_format: OutputFormat,
        enable_filtering: bool,
    ) -> None:
        """Initialize with simple constructor pattern."""
        self.input_dir = Path(input_dir) if input_dir else None
        self.output_dir = Path(output_dir) if output_dir else None
        self.enable_byte_recovery = enable_byte_recovery
        self.output_format = output_format
        self.enable_filtering = enable_filtering

        # Services are None in simple mode
        self.object_type_detector = None
        self.version_detector = None
        self.pcode_decoder = None
        self.control_flow_analyzer = None
        self.expression_reconstructor = None
        self.output_formatter = None
        self.output_validator = None

        # Create decompiler instance for simple mode
        self.decompiler = None

    def _init_with_services(
        self,
        object_type_detector: IObjectTypeDetector,
        version_detector: IVersionDetector | None,
        pcode_decoder: IPCodeDecoder | None,
        control_flow_analyzer: IControlFlowAnalyzer | None,
        expression_reconstructor: IExpressionReconstructor | None,
        output_formatter: IOutputFormatter | None,
        output_validator: IOutputValidator | None,
    ) -> None:
        """Initialize with dependency injection pattern."""
        self.object_type_detector = object_type_detector
        self.version_detector = version_detector
        self.pcode_decoder = pcode_decoder
        self.control_flow_analyzer = control_flow_analyzer
        self.expression_reconstructor = expression_reconstructor
        self.output_formatter = output_formatter
        self.output_validator = output_validator

        # Default values for compatibility
        self.input_dir = None
        self.output_dir = None
        self.enable_byte_recovery = False
        self.output_format = "pb"
        self.enable_filtering = True
        self.decompiler = None

    def decompile(
        self,
        input_dir: Path | None = None,
        output_dir: Path | None = None,
        progress_callback=None,
        enable_cache: bool = True,
        enable_parallel: bool = True,
    ) -> dict[str, Any]:
        """Coordinate decompilation process.

        Args:
            input_dir: Optional override for input directory
            output_dir: Optional override for output directory
            progress_callback: Optional callback for progress updates
            enable_cache: Whether to enable caching
            enable_parallel: Whether to enable parallel processing

        Returns:
            Dictionary with decompilation results
        """
        # Use provided directories or fall back to instance ones
        in_dir = Path(input_dir) if input_dir else self.input_dir
        out_dir = Path(output_dir) if output_dir else self.output_dir

        if not in_dir:
            raise ValueError("No input directory specified")
        if not out_dir:
            raise ValueError("No output directory specified")

        # Ensure output directory exists
        out_dir.mkdir(parents=True, exist_ok=True)

        logger.info("Starting decompilation process")
        logger.info("Input directory: %s", in_dir)
        logger.info("Output directory: %s", out_dir)
        logger.info("Output format: %s", self.output_format)
        logger.info("Cache enabled: %s", enable_cache)
        logger.info("Parallel processing enabled: %s", enable_parallel)

        import time

        start_time = time.time()
        decompiled_count = 0
        failed_count = 0
        skipped_count = 0
        total_files = 0
        cache_hits = 0
        cache_misses = 0

        try:
            # Initialize cache manager if caching is enabled
            cache_manager = None
            if enable_cache:
                try:
                    from src.core.cache_config import get_cache_manager

                    cache_manager = get_cache_manager()
                    logger.info("Cache manager initialized")
                except Exception as e:
                    logger.warning("Failed to initialize cache manager: %s", e)
                    enable_cache = False

            # Check if parallel processing should be used
            if enable_parallel:
                try:
                    # Try enhanced parallel coordinator first
                    try:
                        from src.decompile.enhanced_parallel_coordinator import (
                            EnhancedParallelDecompileCoordinator,
                        )
                        from src.decompile.parallel_config import get_config

                        # Get optimal configuration
                        parallel_config = get_config()

                        # Use enhanced parallel coordinator with all optimizations
                        enhanced_coordinator = EnhancedParallelDecompileCoordinator(
                            input_dir=in_dir,
                            output_dir=out_dir,
                            max_workers=parallel_config.parallelism.max_workers,
                            enable_work_stealing=parallel_config.parallelism.enable_work_stealing,
                            enable_memory_monitoring=True,
                            enable_heartbeat_tracking=True,
                            memory_config=parallel_config.memory,
                        )

                        result = enhanced_coordinator.decompile(
                            input_dir=in_dir,
                            output_dir=out_dir,
                            progress_callback=progress_callback,
                            enable_resumption=True,
                        )

                        logger.info(
                            "Used enhanced parallel processing with adaptive optimizations"
                        )

                    except ImportError:
                        # Fall back to basic parallel coordinator
                        logger.info(
                            "Enhanced parallel coordinator not available, using basic version"
                        )

                        from src.decompile.parallel_coordinator import (
                            ParallelDecompileCoordinator,
                        )

                        # Use basic parallel coordinator
                        parallel_coordinator = ParallelDecompileCoordinator(
                            input_dir=in_dir,
                            output_dir=out_dir,
                            use_adaptive_parallelism=True,
                        )

                        result = parallel_coordinator.decompile(
                            input_dir=in_dir,
                            output_dir=out_dir,
                            progress_callback=progress_callback,
                        )

                    # Extract cache statistics if available
                    if cache_manager:
                        cache_stats = cache_manager.get_stats()
                        for stage_stats in cache_stats.values():
                            if isinstance(stage_stats, dict):
                                cache_hits += stage_stats.get("hits", 0)
                                cache_misses += stage_stats.get("misses", 0)

                    # Add cache statistics to result
                    result.update(
                        {
                            "cache_hits": cache_hits,
                            "cache_misses": cache_misses,
                            "cache_enabled": enable_cache,
                            "parallel_enabled": True,
                        }
                    )

                    return result

                except ImportError as e:
                    logger.warning("Parallel processing not available: %s", e)
                    logger.info("Falling back to sequential processing")
                    enable_parallel = False

            # If DI mode with services, use them
            if self.object_type_detector:
                # Create decompiler with injected services
                decompiler = ExtractedFileDecompiler(
                    object_type_detector=self.object_type_detector,
                    pcode_decoder=self.pcode_decoder,
                    control_flow_analyzer=self.control_flow_analyzer,
                    expression_reconstructor=self.expression_reconstructor,
                    output_formatter=self.output_formatter,
                    output_validator=self.output_validator,
                )
            else:
                # Create decompiler in simple mode
                decompiler = ExtractedFileDecompiler(
                    output_dir=out_dir,
                    enable_filtering=self.enable_filtering,
                    output_format=self.output_format,
                )

            # Collect all P-code files to process
            pcode_extensions = [".fun", ".men", ".mef", ".apf", ".udo", ".win"]
            all_pcode_files = []

            if in_dir.is_file():
                # Single file mode
                if any(in_dir.suffix.lower() == ext for ext in pcode_extensions):
                    all_pcode_files.append(in_dir)
            else:
                # Directory mode
                for ext in pcode_extensions:
                    all_pcode_files.extend(in_dir.rglob(f"*{ext}"))

            total_files = len(all_pcode_files)
            logger.info("Found %d P-code files to decompile", total_files)

            # Process each file
            for i, pcode_file in enumerate(all_pcode_files):
                # Check if we should decompile this file
                if not ObjectTypeDetector.should_decompile(str(pcode_file.name)):
                    logger.debug(
                        "Skipping %s - not a decompilable file", pcode_file.name
                    )
                    skipped_count += 1
                    continue

                # Update progress if callback provided
                if progress_callback:
                    progress_callback(
                        i + 1, total_files, f"Decompiling {pcode_file.name}"
                    )

                logger.info("Processing [%d/%d]: %s", i + 1, total_files, pcode_file)

                try:
                    # Check cache first if caching is enabled
                    cache_hit = False
                    if enable_cache and cache_manager:
                        try:
                            from src.core.cache import file_hash

                            file_hash(pcode_file)
                            cache = cache_manager.get_cache("decompile")

                            if cache:
                                # Check if output file exists and is newer than input
                                output_path = self._get_output_path(pcode_file, out_dir)
                                if output_path and output_path.exists():
                                    output_mtime = output_path.stat().st_mtime
                                    source_mtime = pcode_file.stat().st_mtime

                                    if output_mtime > source_mtime:
                                        cache_hit = True
                                        cache_hits += 1
                                        logger.debug(
                                            "Cache hit for %s", pcode_file.name
                                        )
                                    else:
                                        cache_misses += 1
                                else:
                                    cache_misses += 1
                        except Exception as e:
                            logger.warning(
                                "Cache check failed for %s: %s", pcode_file, e
                            )
                            cache_misses += 1

                    if not cache_hit:
                        if decompiler.decompile_extracted_file(pcode_file):
                            decompiled_count += 1
                            logger.info("Successfully decompiled: %s", pcode_file.name)
                        else:
                            failed_count += 1
                            logger.warning("Failed to decompile: %s", pcode_file.name)
                    else:
                        decompiled_count += 1  # Count cache hits as successful

                except Exception as e:
                    logger.exception("Error decompiling %s: %s", pcode_file, e)
                    failed_count += 1
                    cache_misses += 1

            # Calculate statistics
            duration = time.time() - start_time
            success_rate = (
                (decompiled_count / total_files * 100) if total_files > 0 else 0
            )

            results = {
                "status": "completed",
                "input_dir": str(in_dir),
                "output_dir": str(out_dir),
                "output_format": self.output_format,
                "total_files": total_files,
                "decompiled": decompiled_count,
                "failed": failed_count,
                "skipped": skipped_count,
                "success_rate": f"{success_rate:.1f}%",
                "duration_seconds": duration,
                "cache_enabled": enable_cache,
                "parallel_enabled": enable_parallel,
                "cache_hits": cache_hits,
                "cache_misses": cache_misses,
                "cache_hit_rate": f"{(cache_hits / (cache_hits + cache_misses) * 100):.1f}%"
                if (cache_hits + cache_misses) > 0
                else "0.0%",
            }

            logger.info("Decompilation complete:")
            logger.info("  Total files: %d", total_files)
            logger.info("  Decompiled: %d", decompiled_count)
            logger.info("  Failed: %d", failed_count)
            logger.info("  Skipped: %d", skipped_count)
            logger.info("  Success rate: %.1f%%", success_rate)

            return results

        except Exception as e:
            logger.exception("Decompilation process failed: %s", e)
            return {
                "status": "failed",
                "error": str(e),
                "input_dir": str(in_dir),
                "output_dir": str(out_dir),
                "decompiled": decompiled_count,
                "failed": failed_count,
            }

    def decompile_file(self, file_path: Path) -> str:
        """Decompile a single file.

        Args:
            file_path: Path to the file to decompile

        Returns:
            Decompiled source code
        """
        # Create or reuse decompiler instance
        if not self.decompiler:
            if self.object_type_detector:
                # DI mode
                self.decompiler = ExtractedFileDecompiler(
                    object_type_detector=self.object_type_detector,
                    pcode_decoder=self.pcode_decoder,
                    control_flow_analyzer=self.control_flow_analyzer,
                    expression_reconstructor=self.expression_reconstructor,
                    output_formatter=self.output_formatter,
                    output_validator=self.output_validator,
                )
            else:
                # Simple mode
                self.decompiler = ExtractedFileDecompiler(
                    output_dir=None,  # No output dir for single file
                    enable_filtering=self.enable_filtering,
                    output_format=self.output_format,
                )

        # Decompile the file
        # The decompiler writes to disk, so we need to read the output file
        import tempfile

        # Create a temporary output directory
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_output_dir = Path(temp_dir)

            # Create a temporary decompiler with the temp output directory
            # Use simple constructor mode to avoid DI conflicts
            temp_decompiler = ExtractedFileDecompiler(
                output_dir=temp_output_dir,
                enable_filtering=self.enable_filtering,
                output_format=self.output_format,
            )

            # Decompile the file
            success = temp_decompiler.decompile_extracted_file(file_path)

            if not success:
                raise RuntimeError(f"Failed to decompile {file_path}")

            # Find the output file
            # The decompiler creates files based on input extension mapping
            expected_output_path = self._get_expected_output_path(
                file_path, temp_output_dir
            )

            # Look for the expected output file first
            output_files = []
            if expected_output_path and expected_output_path.exists():
                output_files = [expected_output_path]
            else:
                # Fallback: search for any output files
                # Try common PowerBuilder extensions
                for ext in [".sru", ".srw", ".srm", ".srs", ".srd", ".sra", ".pb"]:
                    output_files = list(temp_output_dir.rglob(f"*{ext}"))
                    if output_files:
                        break

                # Last resort: get any non-empty file
                if not output_files:
                    all_files = list(temp_output_dir.rglob("*"))
                    output_files = [
                        f for f in all_files if f.is_file() and f.stat().st_size > 0
                    ]

            if not output_files:
                # Check if decompilation actually succeeded
                logger.error(
                    "No output files found in temp directory: %s", temp_output_dir
                )
                logger.error("Directory contents: %s", list(temp_output_dir.rglob("*")))
                raise RuntimeError(
                    f"No output file found after decompiling {file_path}. "
                    f"Expected: {expected_output_path}, temp dir: {temp_output_dir}"
                )

            # Read and return the content of the first output file
            output_file = output_files[0]
            return output_file.read_text(encoding="utf-8")

    def register_decompiler(self, _decompiler: Any) -> None:
        """Register a new decompiler (for interface compatibility)."""
        logger.warning("register_decompiler is not implemented in this coordinator")

    def get_decompilers(self) -> list[Any]:
        """Get all registered decompilers (for interface compatibility)."""
        return [self.decompiler] if self.decompiler else []

    def validate_inputs(self) -> bool:
        """Validate input requirements for decompilation.

        Returns:
            True if inputs are valid, False otherwise
        """
        if not self.input_dir:
            logger.error("No input directory specified")
            return False

        if not self.input_dir.exists():
            logger.error("Input directory does not exist: %s", self.input_dir)
            return False

        if not self.output_dir:
            logger.error("No output directory specified")
            return False

        return True

    def process(self, progress_callback=None) -> dict[str, Any]:
        """Process files for pipeline integration.

        This method provides compatibility with the pipeline interface.

        Args:
            progress_callback: Optional callback for progress updates

        Returns:
            Dictionary with processing results
        """
        # Validate inputs first
        if not self.validate_inputs():
            return {
                "status": "failed",
                "error": "Input validation failed",
                "input_dir": str(self.input_dir) if self.input_dir else None,
                "output_dir": str(self.output_dir) if self.output_dir else None,
            }

        return self.decompile(
            input_dir=self.input_dir,
            output_dir=self.output_dir,
            progress_callback=progress_callback,
        )

    def _get_output_path(self, pcode_file: Path, output_dir: Path) -> Path | None:
        """Get the expected output path for a P-code file.

        Args:
            pcode_file: Input P-code file path
            output_dir: Output directory

        Returns:
            Expected output file path or None if cannot be determined
        """
        try:
            # Map P-code extension to PowerBuilder source extension
            ext_mapping = {
                ".fun": ".sru",  # function/user object
                ".win": ".srw",  # window
                ".men": ".srm",  # menu
                ".str": ".srs",  # structure
                ".dwo": ".srd",  # datawindow
                ".app": ".sra",  # application
                ".mef": ".srm",  # menu function
                ".apf": ".sru",  # application function
                ".udo": ".sru",  # user-defined object
            }

            new_ext = ext_mapping.get(pcode_file.suffix.lower(), ".sru")
            output_filename = pcode_file.stem + new_ext

            # Try to preserve directory structure
            try:
                relative_path = pcode_file.relative_to(
                    pcode_file.parents[2]
                )  # Assume extracted/<project>/<file>
                return output_dir / relative_path.parent / output_filename
            except (ValueError, IndexError):
                # Fallback to simple filename
                return output_dir / output_filename

        except Exception as e:
            logger.warning("Could not determine output path for %s: %s", pcode_file, e)
            return None

    def _get_expected_output_path(
        self, input_file: Path, output_dir: Path
    ) -> Path | None:
        """Get the expected output file path for a given input file."""
        try:
            # Map input extension to expected output extension
            ext_mapping = {
                ".fun": ".sru",  # function/user object -> source user object
                ".win": ".srw",  # window -> source window
                ".men": ".srm",  # menu -> source menu
                ".str": ".srs",  # structure -> source structure
                ".dwo": ".srd",  # datawindow -> source datawindow
                ".app": ".sra",  # application -> source application
                ".mef": ".srm",  # menu function -> source menu
                ".apf": ".sru",  # application function -> source user object
                ".udo": ".sru",  # user-defined object -> source user object
            }

            input_ext = input_file.suffix.lower()
            output_ext = ext_mapping.get(input_ext, ".sru")  # default to .sru
            output_filename = input_file.stem + output_ext

            # Try to find where the file would be placed
            # The decompiler preserves directory structure
            possible_paths = [
                output_dir / output_filename,  # Direct in output dir
                output_dir / input_file.stem / output_filename,  # In subdirectory
            ]

            # Also search recursively for the filename
            for path in output_dir.rglob(output_filename):
                if path.is_file():
                    return path

            # Return the most likely path even if it doesn't exist yet
            return possible_paths[0]

        except Exception as e:
            logger.warning(
                "Could not determine expected output path for %s: %s", input_file, e
            )
            return None

    def extract_schemas(
        self,
        project_dir: str | Path | None = None,
        output_dir: str | Path | None = None,
        output_format: str = "markdown",
        progress_callback=None,
    ) -> dict[str, Any]:
        """Extract database schemas from decompiled PowerBuilder files.

        Args:
            project_dir: Directory containing decompiled PowerBuilder source files
            output_dir: Directory to write schema documentation
            output_format: Documentation format ("markdown", "html", "json")
            progress_callback: Optional callback for progress updates

        Returns:
            Dictionary with extraction results
        """
        # Use provided directories or fall back to instance ones
        proj_dir = Path(project_dir) if project_dir else self.output_dir
        out_dir = Path(output_dir) if output_dir else self.output_dir

        if not proj_dir:
            raise ValueError("No project directory specified")
        if not out_dir:
            raise ValueError("No output directory specified")

        # Ensure output directory exists
        out_dir.mkdir(parents=True, exist_ok=True)

        logger.info("Starting schema extraction")
        logger.info("Project directory: %s", proj_dir)
        logger.info("Output directory: %s", out_dir)
        logger.info("Output format: %s", output_format)

        try:
            # Call the existing extract_database_schema function
            extract_database_schema(
                project_dir=proj_dir,
                output_dir=out_dir,
                output_format=output_format,
                progress=progress_callback,
            )

            # Return results
            return {
                "status": "completed",
                "project_dir": str(proj_dir),
                "output_dir": str(out_dir),
                "output_format": output_format,
                "schema_file": str(
                    out_dir / f"database_schema_documentation.{output_format}"
                ),
                "raw_data_file": str(out_dir / "database_schema_raw.json"),
            }

        except Exception as e:
            logger.exception("Schema extraction failed: %s", e)
            return {
                "status": "failed",
                "error": str(e),
                "project_dir": str(proj_dir),
                "output_dir": str(out_dir),
            }

    def _convert_dict_blocks_to_objects(self, dict_blocks: list[dict]) -> list[Any]:
        """Convert dictionary blocks back to ControlBlock objects.

        This is a helper method for backward compatibility when dealing with
        interface requirements vs. internal implementation needs.

        Args:
            dict_blocks: List of block dictionaries

        Returns:
            List of ControlBlock objects
        """
        from src.decompile.types import ControlBlock, BlockType

        control_blocks = []

        for block_dict in dict_blocks:
            try:
                # Convert type string back to enum
                block_type = BlockType[block_dict.get("type", "BASIC")]

                # Create ControlBlock object
                control_block = ControlBlock(
                    type=block_type,
                    start_addr=block_dict.get("start_addr", 0),
                    end_addr=block_dict.get("end_addr", 0),
                    instructions=[],  # Instructions not preserved in dict format
                    statements=block_dict.get("statements", []),
                    metadata=block_dict.get("metadata", {}),
                )

                control_blocks.append(control_block)

            except (KeyError, ValueError) as e:
                logger.warning("Failed to convert dict block to ControlBlock: %s", e)
                continue

        return control_blocks


def main() -> None:
    """Command-line interface for the decompiler."""
    parser = argparse.ArgumentParser(
        description="PowerBuilder PBD Decompiler - Best of Both Worlds Edition",
    )
    parser.add_argument(
        "pbd_file",
        type=Path,
        help="Path to the PBD file to decompile",
    )
    parser.add_argument(
        "--output-dir",
        "-o",
        type=Path,
        help="Directory to write decompiled files (default: stdout)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging",
    )
    parser.add_argument(
        "--output-format",
        "-f",
        type=str,
        choices=SUPPORTED_OUTPUT_FORMATS,
        default="pb",
        help="Output format: pb (PowerBuilder), txt (plain text), or md (Markdown)",
    )

    args = parser.parse_args()

    # Configure logging
    log_level = logging.INFO
    if args.debug:
        log_level = logging.DEBUG
    elif args.verbose:
        log_level = logging.INFO

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    # Check input file
    if not args.pbd_file.exists():
        sys.exit(1)

    if args.pbd_file.suffix.lower() not in [".pbd", ".pbl"]:
        logger.exception(
            "Invalid file extension: %s. Expected .pbd or .pbl", args.pbd_file.suffix
        )
        sys.exit(1)

    # Run decompiler
    decompiler = PowerBuilderDecompiler(
        args.output_dir, output_format=args.output_format
    )
    success = decompiler.decompile_pbd(args.pbd_file)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
