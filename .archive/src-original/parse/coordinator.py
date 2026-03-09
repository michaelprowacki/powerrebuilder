"""PowerBuilder SOURCE FILE parser using modular grammar and preprocessing.

This module implements a comprehensive parser for PowerBuilder SOURCE code files,
converting raw text into structured Abstract Syntax Trees (ASTs). It processes
PowerBuilder source files (.sru) that are produced by the Decompile stage.

IMPORTANT: This module runs AFTER the Decompile module in the sequential pipeline:
- Decompile: Converts .fun (P-code) files → .sru (source) files
- Parse: Processes .sru files → produces AST JSON

Key features:
- Extension-based parser selection for different PowerBuilder source file types
- Modular grammar design with shared rules across file types
- Preprocessing support for handling macros, includes, and conditional compilation
- Source location tracking for error reporting
- Visitor pattern support for AST traversal and transformation
- Specialized parsers for different PowerBuilder constructs (DataWindow, SQL, etc.)

The parsers are implemented using the Lark parsing library with LALR parsing
and custom visitor classes for transforming parse trees into the model layer's
AST nodes. Error handling is enhanced with context-aware error messages.

Input: Source files (.sru) from the Decompile stage
Output: AST JSON files for the Model stage

Based on reference implementation from Moose PowerBuilder Parser:
reference/moose-pb-parser/PowerBuilder-Parser-Core/PWBAbstractGrammar.class.st
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from collections.abc import Callable
from src.contracts.types import ParseStatsDict
from src.common.coordinators.base import BaseCoordinator

from src.model.ast.serialization import serialize_ast
from src.model.types.errors import ParseErrorCollector

from .grammar.loader import GrammarManager
from .library import LibraryManager
from .parser.base import PowerBuilderBaseParser
from .parser.powerbuilder import EnhancedPowerBuilderParser
from .preprocessor.preprocessor import PowerBuilderPreprocessor
from .recovery_strategy import EnhancedErrorRecovery
from .transformer.builder import PowerBuilderTransformer

logger = logging.getLogger(__name__)


class ParseCoordinator(BaseCoordinator):
    """Coordinator for PowerBuilder source file parsing.

    This coordinator handles the parsing of PowerBuilder source files (.sru, .srw, etc.)
    into Abstract Syntax Trees (ASTs) for further processing by the Model stage.
    """

    def __init__(
        self,
        input_dir: Path | str,
        output_dir: Path | str,
        enable_recovery: bool = True,
        validate_ast: bool = True,
    ) -> None:
        """Initialize the parse coordinator.

        Args:
            input_dir: Directory containing decompiled source files
            output_dir: Directory to write AST JSON files
            enable_recovery: Whether to enable error recovery during parsing
            validate_ast: Whether to validate generated ASTs
        """
        super().__init__(input_dir, output_dir, "parse")

        self.enable_recovery = enable_recovery
        self.validate_ast = validate_ast

        # Initialize components
        self.grammar_manager = GrammarManager()
        self.library_manager = LibraryManager()
        self.preprocessor = PowerBuilderPreprocessor()
        self.error_collector = ParseErrorCollector()

    def process(
        self, progress_callback: Callable[[int, int, str], None] | None = None
    ) -> dict[str, Any]:
        """Parse all source files in the input directory.

        Args:
            progress_callback: Optional callback for progress updates

        Returns:
            Dictionary with parsing results
        """
        # Collect source files
        source_extensions = [".sru", ".srw", ".srm", ".srs", ".srd", ".sra"]
        source_files = self.discover_files([f"*{ext}" for ext in source_extensions])

        logger.info("Found %d source files to parse", len(source_files))

        # Process files using base class helper
        self.process_files_with_callback(
            source_files, self._parse_file, progress_callback, "Parsing"
        )

        return self.get_statistics()

    def parse(
        self, progress_callback: Callable[[int, int, str], None] | None = None
    ) -> ParseStatsDict:
        """Parse all source files (backward compatibility method).

        Args:
            progress_callback: Optional callback for progress updates

        Returns:
            Dictionary with parsing results
        """
        return self.run_with_progress(progress_callback)

    def _parse_file(self, source_file: Path) -> None:
        """Parse a single source file.

        Args:
            source_file: Path to the source file
        """
        logger.debug("Parsing %s", source_file)

        # Read source content
        with source_file.open("r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        # Preprocess the content
        preprocessed_content = self.preprocessor.preprocess(content, str(source_file))

        # Determine parser based on file extension
        file_ext = source_file.suffix.lower()
        parser = self._get_parser_for_extension(file_ext)

        # Parse with error recovery
        if self.enable_recovery:
            error_recovery = EnhancedErrorRecovery(self.error_collector)
            ast = parser.parse_with_recovery(preprocessed_content, error_recovery)
        else:
            ast = parser.parse(preprocessed_content)

        # Transform to AST nodes
        transformer = PowerBuilderTransformer()
        transformed_ast = transformer.transform(ast)

        # Validate AST if enabled
        if self.validate_ast:
            validation_errors = self._validate_ast(transformed_ast)
            if validation_errors:
                for error in validation_errors:
                    self.record_warning(error, str(source_file))

        # Serialize AST to JSON
        ast_data = serialize_ast(transformed_ast)

        # Add metadata
        ast_json = {
            "file": str(source_file.name),
            "type": self._get_object_type(file_ext),
            "parsed_at": datetime.now().isoformat(),
            "ast": ast_data,
            "errors": self.error_collector.get_errors_for_file(str(source_file)),
        }

        # Write AST JSON file
        output_path = self.get_relative_output_path(source_file, ".ast.json")

        with output_path.open("w", encoding="utf-8") as f:
            json.dump(ast_json, f, indent=2)

        logger.debug("Wrote AST to %s", output_path)

    def _get_parser_for_extension(self, extension: str) -> PowerBuilderBaseParser:
        """Get appropriate parser for file extension.

        Args:
            extension: File extension (e.g., ".sru")

        Returns:
            Parser instance
        """
        # Use simple PowerBuilder grammar for testing
        # TODO: Fix the main powerbuilder.lark grammar file
        # Note: grammar loading is handled internally by EnhancedPowerBuilderParser

        # Create concrete parser implementation
        return EnhancedPowerBuilderParser(
            base_path=self.input_dir, enable_error_recovery=self.enable_recovery
        )

    def _get_object_type(self, extension: str) -> str:
        """Get object type from file extension.

        Args:
            extension: File extension

        Returns:
            Object type string
        """
        ext_to_type = {
            ".sru": "userobject",
            ".srw": "window",
            ".srm": "menu",
            ".srs": "structure",
            ".srd": "datawindow",
            ".sra": "application",
        }
        return ext_to_type.get(extension, "unknown")

    def _validate_ast(self, ast: Any) -> List[str]:
        """Validate AST structure.

        Args:
            ast: AST to validate

        Returns:
            List of validation errors
        """
        errors = []

        # Basic validation checks
        if not ast:
            errors.append("AST is empty")
            return errors

        # Check for required attributes
        if hasattr(ast, "__dict__"):
            if not hasattr(ast, "type") or not ast.type:
                errors.append("AST node missing 'type' attribute")

            # Check for source location info
            if not hasattr(ast, "line") or not hasattr(ast, "column"):
                errors.append("AST node missing source location info")

        return errors

    def validate_inputs(self) -> bool:
        """Validate input requirements for the stage.

        Returns:
            True if inputs are valid, False otherwise
        """
        return self.validate_common_inputs()


# Utility function for compatibility
def parse_file(
    file_path: Union[Path, str], output_dir: Optional[Union[Path, str]] = None
) -> Dict[str, Any]:
    """Parse a single PowerBuilder source file.

    Args:
        file_path: Path to the source file
        output_dir: Optional output directory for AST

    Returns:
        Dictionary containing the parsed AST
    """
    file_path = Path(file_path)

    # Use temporary directory if no output specified
    if not output_dir:
        import tempfile

        output_dir = Path(tempfile.mkdtemp())
    else:
        output_dir = Path(output_dir)

    # Create coordinator and parse single file
    coordinator = ParseCoordinator(file_path.parent, output_dir)
    coordinator._parse_file(file_path)

    # Read and return the generated AST
    output_path = coordinator._get_output_path(file_path)
    if output_path.exists():
        with output_path.open("r") as f:
            return json.load(f)

    raise RuntimeError(f"Failed to parse {file_path}")
