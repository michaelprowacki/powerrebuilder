"""Code generation module for converting PowerBuilder models to modern code.

This module forms the final stage in the PowerBuilder reverse engineering pipeline,
generating modern web application code from semantic models produced by the Model stage.

PIPELINE SEQUENCE:
1. Extract → .fun files
2. Decompile → .sru files
3. Parse → AST JSON
4. Model → Semantic models
5. Generate → Modern code (THIS STAGE)

INPUTS:
- From Model stage: Semantic models containing typed representations of the application

OUTPUTS:
- Backend: Python/Litestar APIs, SQLModel models, Pydantic schemas
- Frontend: Flutter/Dart UI, screens, widgets, state management

Key components:
- CodeGenerator: Base class providing template rendering functionality
- ModelGenerator: Generates SQLModel models from database schema
- ServiceGenerator: Converts business logic into service layer classes
- FlutterGenerator: Transforms UI definitions into Flutter/Dart widgets

The code generation relies on Jinja2 templates to transform semantic models
into production-ready code for modern frameworks.

Each generator handles a specific aspect of the application and is orchestrated
through the main entry points: generate_models(), generate_services(), and generate_flutter().

This coordinator supports two usage patterns:
1. Simple constructor for backward compatibility (used by pipeline)
2. Dependency injection for testability and flexibility

Implements BaseCoordinator interface with process() and validate_inputs() methods.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional
from collections.abc import Callable

from src.contracts.types import (
    GenerationSummaryDict,
    GeneratedFilesDict,
    GenerationErrorDict,
)

from src.parse.parser.sql import SQLParser

from .converters.flutter.layouts import LayoutConverter, LayoutStrategy
from .converters.flutter.models import TypeConverter
from .converters.flutter.widgets import UIConverter
from .converters.utils.ast import ASTConverter
from .flutter import FlutterGenerator
from .models import ModelGenerator
from .python_ui import PythonUIGenerator
from .service import ServiceGenerator

logger = logging.getLogger(__name__)


class GenerateCoordinator:
    """Coordinator class that wraps generation functions for pipeline integration.

    Implements BaseCoordinator interface with process() and validate_inputs() methods.
    """

    def __init__(
        self,
        input_dir: str | Path,
        output_dir: str | Path,
        framework: str = "flutter",
        null_safety: bool = True,
        generate_tests: bool = False,
    ) -> None:
        """Initialize the generate coordinator.

        Args:
            input_dir: Directory containing parsed AST files
            output_dir: Directory for generated code
            framework: Target framework (default: 'flutter')
            null_safety: Enable null safety (default: True)
            generate_tests: Generate test files (default: False)
        """
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.framework = framework
        self.null_safety = null_safety
        self.generate_tests = generate_tests

        # Create output directories
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize generators (disable validation temporarily for converter integration)
        self.model_generator = ModelGenerator(
            str(Path(__file__).parent / "templates"), str(self.output_dir / "backend")
        )
        self.service_generator = ServiceGenerator(
            str(Path(__file__).parent / "templates"),
            str(self.output_dir / "backend"),
            validate_templates=False,
        )
        self.flutter_generator = FlutterGenerator(
            str(Path(__file__).parent / "templates" / "flutter"),
            str(self.output_dir / "flutter"),
            validate_templates=False,
        )

        # Pass the layout converter to the Flutter generator
        self.flutter_generator.layout_converter = None  # Will set after initialization

        # Initialize Python UI generator
        self.python_ui_generator = PythonUIGenerator(
            str(Path(__file__).parent / "templates" / "python"),
            str(self.output_dir / "python"),
        )

        # Initialize converters
        self.type_converter = TypeConverter()
        self.ast_converter = ASTConverter()
        self.ui_converter = UIConverter(
            design_theme="liquid_glass"
        )  # Enable Liquid Glass aesthetic
        # Event converter expects type_converter and expression_converter
        # For now, initialize with minimal setup
        # self.event_converter = EventConverter()
        # Note: These converters expect different parameters, so we'll use them carefully
        # self.datawindow_converter = DataWindowConverter()
        # self.expression_converter = ExpressionConverter()

        # Initialize layout converter with absolute positioning by default
        # This preserves the exact PowerBuilder layout
        # Pass the event wiring system from flutter generator
        self.layout_converter = LayoutConverter(
            LayoutStrategy.ABSOLUTE, ui_converter=self.ui_converter
        )

        # Pass layout converter and UI converter to generators
        self.flutter_generator.layout_converter = self.layout_converter
        self.flutter_generator.ui_converter = self.ui_converter
        self.python_ui_generator.layout_converter = self.layout_converter

    def generate_from_model(self, model_file: str) -> Dict[str, Any]:
        """Generate code from a model file.

        Args:
            model_file: Path to model JSON file

        Returns:
            Dictionary with generation results
        """
        try:
            import json

            # Load model data
            model_path = Path(model_file)
            if not model_path.exists():
                # Try relative to input dir
                model_path = self.input_dir / model_file

            if not model_path.exists():
                logger.error("Model file not found: %s", model_file)
                return {"success": False, "error": "Model file not found"}

            with open(model_path) as f:
                model_data = json.load(f)

            generated_files = []

            # Extract original AST file reference if available
            model_data.get("ast_file", model_data.get("file"))

            # Process each model object in the file
            models = model_data.get("models", [])
            if not models:
                logger.warning("No models found in %s", model_file)
                return {"success": False, "error": "No models in file"}

            for model in models:
                model_type = model.get("type", "Unknown")
                model_name = model.get("name", "unnamed")
                model_instance = model.get("data", {})

                # Skip error models
                if model_instance == "error" or (
                    isinstance(model_instance, dict)
                    and model_instance.get("type") == "tree"
                    and model_instance.get("data") == "error"
                ):
                    logger.warning("Skipping error model in %s", model_file)
                    continue

                # Generate code based on model type
                if model_type in ["window", "PBWindow", "Window"]:
                    # Use model_name with fallback to properties
                    name = model_name or model_instance.get("name", "unnamed_window")
                    # Ensure model_instance has required properties
                    if not model_instance.get("name"):
                        model_instance["name"] = name
                    self.flutter_generator.generate_screen_from_model(model_instance)
                    generated_files.append(f"flutter/screens/{name}_screen.dart")

                elif model_type in ["datawindow", "PBDataWindow", "DataWindow"]:
                    name = model_name or model_instance.get(
                        "name", "unnamed_datawindow"
                    )
                    columns = model_instance.get("columns", [])
                    self.model_generator.generate_model(name, columns, [])
                    generated_files.append(f"backend/models/{name}.py")

                elif model_type in ["userobject", "PBUserObject", "UserObject"]:
                    name = model_name or model_instance.get(
                        "name", "unnamed_userobject"
                    )
                    if model_instance.get("visual", False):
                        # Generate Flutter widget
                        self.flutter_generator.generate_widget(
                            name=name,
                            properties=model_instance.get("properties", {}),
                            methods=model_instance.get("methods", []),
                        )
                        generated_files.append(f"flutter/widgets/{name}_widget.dart")
                    else:
                        # Generate service
                        methods = model_instance.get("methods", [])
                        self.service_generator.generate_service(name, methods)
                        generated_files.append(f"backend/services/{name}_service.py")

                elif model_type in ["function", "PBFunction", "Function"]:
                    name = model_name or model_instance.get("name", "unnamed_function")
                    # Generate utility function
                    self.service_generator.generate_utility_function(
                        name, model_instance
                    )
                    generated_files.append(f"backend/utils/{name}.py")

                elif model_type in ["menu", "PBMenu", "Menu"]:
                    name = model_name or model_instance.get("name", "unnamed_menu")
                    # Generate Flutter menu widget
                    self.flutter_generator.generate_menu(name, model_instance)
                    generated_files.append(f"flutter/widgets/{name}_menu.dart")

                elif model_type in ["structure", "PBStructure", "Structure"]:
                    name = model_name or model_instance.get("name", "unnamed_structure")
                    # Generate Python dataclass
                    fields = model_instance.get("fields", [])
                    self.model_generator.generate_structure(name, fields)
                    generated_files.append(f"backend/models/{name}.py")

                else:
                    logger.warning("Unknown model type: {model_type} in %s", model_file)

            return {
                "success": True,
                "generated_files": generated_files,
                "model_file": str(model_file),
                "models_processed": len(models),
            }

        except (ValueError, TypeError, OSError, ImportError) as e:
            logger.error("Error generating from model {model_file}: %s", e)
            return {"success": False, "error": str(e)}

    def generate_all(self) -> Dict[str, Any]:
        """Generate all code from parsed AST files.

        Returns:
            Dictionary with generation results
        """
        results = {
            "models": {"success": False, "files": []},
            "services": {"success": False, "files": []},
            "flutter": {"success": False, "files": []},
            "python_ui": {"success": False, "files": []},
        }

        try:
            # Generate models
            logger.info("Generating models...")
            model_results = generate_models(str(self.input_dir), str(self.output_dir))
            results["models"] = model_results

            # Generate services
            logger.info("Generating services...")
            service_results = generate_services(
                str(self.input_dir), str(self.output_dir)
            )
            results["services"] = service_results

            # Generate Flutter UI
            if self.framework == "flutter":
                logger.info("Generating Flutter UI...")
                flutter_results = generate_flutter(
                    str(self.input_dir), str(self.output_dir)
                )
                results["flutter"] = flutter_results

            # Generate Python UI
            elif self.framework == "python":
                logger.info("Generating Python UI...")
                python_results = generate_python_ui(
                    str(self.input_dir), str(self.output_dir)
                )
                results["python_ui"] = python_results

        except Exception as e:
            logger.error("Error in generate_all: %s", e)
            results["error"] = str(e)

        return results

    def generate(
        self, progress_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> Dict[str, Any]:
        """Main entry point for the pipeline - generates all code.

        Args:
            progress_callback: Optional callback for progress updates

        Returns:
            Dictionary with generation results
        """
        try:
            if progress_callback:
                progress_callback(0, 100, "Starting code generation")

            # Find all model files in input directory
            model_files = list(self.input_dir.rglob("*.model.json"))
            logger.info("Found %s model files", len(model_files))

            if progress_callback:
                progress_callback(
                    0, len(model_files), f"Processing {len(model_files)} model files"
                )

            # Create a summary for tracking all generated files
            generated_files: GeneratedFilesDict = {
                "models": [],
                "services": [],
                "flutter": [],
                "python": [],
            }

            summary: GenerationSummaryDict = {
                "total_models": len(model_files),
                "successful_models": 0,
                "failed_models": 0,
                "generated_files": generated_files,
                "errors": [],
            }

            # Process each model file
            for idx, model_file in enumerate(model_files):
                try:
                    if progress_callback:
                        progress_callback(
                            idx + 1, len(model_files), f"Processing {model_file.name}"
                        )

                    # Generate from the model file
                    result = self.generate_from_model(str(model_file))

                    if result.get("success"):
                        summary["successful_models"] += 1
                        # Categorize generated files
                        for file_path in result.get("generated_files", []):
                            if "models" in file_path:
                                summary["generated_files"]["models"].append(file_path)
                            elif "services" in file_path:
                                summary["generated_files"]["services"].append(file_path)
                            elif "flutter" in file_path:
                                summary["generated_files"]["flutter"].append(file_path)
                            elif "python" in file_path:
                                summary["generated_files"]["python"].append(file_path)
                    else:
                        summary["failed_models"] += 1
                        error_info: GenerationErrorDict = {
                            "file": str(model_file),
                            "error": result.get("error", "Unknown error"),
                        }
                        summary["errors"].append(error_info)

                except Exception as e:
                    logger.error("Failed to process {model_file}: %s", e)
                    summary["failed_models"] += 1
                    error_info: GenerationErrorDict = {
                        "file": str(model_file),
                        "error": str(e),
                    }
                    summary["errors"].append(error_info)

            # Write generation summary
            summary_path = self.output_dir / "generation_summary.json"
            with open(summary_path, "w") as f:
                json.dump(summary, f, indent=2)

            if progress_callback:
                progress_callback(
                    len(model_files), len(model_files), "Code generation complete"
                )

            logger.info("Code generation complete. Summary written to %s", summary_path)
            logger.info(
                "Successfully processed %s/%s models",
                summary["successful_models"],
                summary["total_models"],
            )

            return summary

        except Exception as e:
            logger.error("Error in generate: %s", e)
            return {"error": str(e), "success": False}

    def process(self) -> Dict[str, Any]:
        """Process input files and produce output (required by BaseCoordinator).

        Returns:
            Dictionary containing processing statistics
        """
        return self.generate()

    def validate_inputs(self) -> bool:
        """Validate input requirements for the stage (required by BaseCoordinator).

        Returns:
            True if inputs are valid, False otherwise
        """
        if not self.input_dir.exists():
            logger.error("Input directory does not exist: %s", self.input_dir)
            return False

        if not self.input_dir.is_dir():
            logger.error("Input path is not a directory: %s", self.input_dir)
            return False

        # Check if output directory can be created
        try:
            self.output_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.error("Cannot create output directory {self.output_dir}: %s", e)
            return False

        return True


def generate_models(input_dir: str, output_dir: str) -> Dict[str, Any]:
    """Generate SQLModel models from DataWindow AST files.

    Args:
        input_dir: Directory containing parsed AST files
        output_dir: Directory to write generated models

    Returns:
        Dictionary with generation results
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir) / "backend"

    # Reuse coordinator for model generation
    coordinator = ModelGenerationCoordinator(input_path, output_path)
    return coordinator.generate({})


def extract_datawindow_from_ast(ast_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Extract DataWindow information from an AST.

    Args:
        ast_data: The AST data

    Returns:
        Dictionary containing DataWindow information or None
    """
    try:
        if ast_data.get("type") != "datawindow":
            return None

        # Get the SQL select statement
        sql_select = ""
        if "body" in ast_data:
            for item in ast_data["body"]:
                if item.get("type") == "sql_select":
                    sql_select = item.get("value", "")
                    break

        # Parse SQL to extract table and column info
        sql_parser = SQLParser()
        sql_info = sql_parser.parse_sql(sql_select) if sql_select else {}

        # Extract columns from the AST
        columns = []
        if "columns" in ast_data:
            for col in ast_data["columns"]:
                columns.append(
                    {
                        "name": col.get("name", ""),
                        "type": col.get("datatype", "string"),
                        "nullable": col.get("nullable", True),
                        "primary_key": col.get("primary_key", False),
                    }
                )

        # If no columns in AST, try to get from SQL
        if not columns and sql_info.get("columns"):
            columns = sql_info["columns"]

        # Extract relationships if available
        relationships = []
        if "relationships" in ast_data:
            relationships = ast_data["relationships"]

        return {
            "name": ast_data.get("name", "unnamed"),
            "sql": sql_info,
            "columns": columns,
            "relationships": relationships,
            "primary_keys": [col["name"] for col in columns if col.get("primary_key")],
        }

    except Exception as e:
        logger.error("Failed to extract DataWindow from AST: %s", e)
        return None


def generate_services(input_dir: str, output_dir: str) -> Dict[str, Any]:
    """Generate service layer from User Object AST files.

    Args:
        input_dir: Directory containing parsed AST files
        output_dir: Directory to write generated services

    Returns:
        Dictionary with generation results
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir) / "backend"

    # Reuse coordinator for service generation
    coordinator = ServiceGenerationCoordinator(input_path, output_path)
    return coordinator.generate({})


def generate_flutter(input_dir: str, output_dir: str) -> Dict[str, Any]:
    """Generate Flutter UI from Window AST files.

    Args:
        input_dir: Directory containing parsed AST files
        output_dir: Directory to write generated Flutter code

    Returns:
        Dictionary with generation results
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir) / "flutter"

    # Reuse coordinator for Flutter generation
    coordinator = FlutterGenerationCoordinator(input_path, output_path)
    return coordinator.generate({})


def generate_python_ui(input_dir: str, output_dir: str) -> Dict[str, Any]:
    """Generate Python UI from Window AST files.

    Args:
        input_dir: Directory containing parsed AST files
        output_dir: Directory to write generated Python UI code

    Returns:
        Dictionary with generation results
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir) / "python"
    output_path.mkdir(parents=True, exist_ok=True)

    logger.info("Generating Python UI from {input_path} to %s", output_path)

    # Initialize the Python UI generator
    python_ui_gen = PythonUIGenerator(
        str(Path(__file__).parent / "templates" / "python"), str(output_path)
    )

    # Collect all window AST files
    window_files = list(input_path.rglob("*.srw.ast.json"))
    logger.info("Found %s window files", len(window_files))

    generated_files = []
    errors = []

    for window_file in window_files:
        try:
            # Read the AST
            with open(window_file) as f:
                ast_data = json.load(f)

            # Extract window name
            window_name = window_file.stem.replace(".srw.ast", "")

            # Generate Python UI code
            python_ui_gen.generate_window(window_name, ast_data)
            generated_files.append(f"python/{window_name}_window.py")

            logger.info("Generated Python UI for %s", window_name)

        except Exception as e:
            logger.error("Failed to generate Python UI for {window_file}: %s", e)
            errors.append({"file": str(window_file), "error": str(e)})

    # Generate main.py if we have windows
    if generated_files:
        try:
            # Extract window names for main.py
            window_names = [
                Path(f).stem.replace("_window", "") for f in generated_files
            ]
            python_ui_gen.generate_main(window_names)
            generated_files.append("python/main.py")
            logger.info("Generated main.py")
        except Exception as e:
            logger.error("Failed to generate main.py: %s", e)
            errors.append({"file": "main.py", "error": str(e)})

    return {
        "success": len(errors) == 0,
        "files": generated_files,
        "errors": errors,
        "windows_processed": len(window_files),
    }


# Re-export the coordinators for backward compatibility
from src.generate.coordinators.flutter import FlutterGenerationCoordinator
from src.generate.coordinators.model import ModelGenerationCoordinator
from src.generate.coordinators.service import ServiceGenerationCoordinator

__all__ = [
    "FlutterGenerationCoordinator",
    "GenerateCoordinator",
    "ModelGenerationCoordinator",
    "ServiceGenerationCoordinator",
    "extract_datawindow_from_ast",
    "generate_flutter",
    "generate_models",
    "generate_python_ui",
    "generate_services",
]
