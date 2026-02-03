"""Generate Feature - Code generation from semantic models.

This module generates modern application code from semantic models.
Supports multiple target languages and frameworks.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List

from src_new._core import (
    ApplicationModel,
    GeneratedFile,
    GeneratedProject,
    Method,
    ObjectType,
    Property,
    SemanticObject,
    TargetLanguage,
)
from src_new._patterns import (
    BaseCoordinator,
    FileHandler,
)
from .templates import render_template

logger = logging.getLogger(__name__)


# ============================================================================
# CODE GENERATORS
# ============================================================================


class BaseCodeGenerator:
    """Base class for code generators."""

    def __init__(self, target: TargetLanguage):
        """Initialize generator.

        Args:
            target: Target language
        """
        self.target = target

    def generate_project(self, model: ApplicationModel) -> GeneratedProject:
        """Generate complete project from application model.

        Args:
            model: Application model

        Returns:
            Generated project
        """
        project = GeneratedProject(
            name=model.name,
            target=self.target,
        )

        # Generate files for each object
        for obj in model.objects.values():
            files = self.generate_object(obj)
            project.files.extend(files)

        # Generate project configuration
        config_files = self.generate_config(model)
        project.files.extend(config_files)

        return project

    def generate_object(self, obj: SemanticObject) -> List[GeneratedFile]:
        """Generate files for a semantic object.

        Args:
            obj: Semantic object

        Returns:
            List of generated files
        """
        # Dispatch based on object type
        if obj.type == ObjectType.WINDOW:
            return self.generate_window(obj)
        elif obj.type == ObjectType.DATAWINDOW:
            return self.generate_datawindow(obj)
        elif obj.type == ObjectType.USER_OBJECT:
            return self.generate_user_object(obj)
        else:
            return self.generate_generic(obj)

    def generate_window(self, obj: SemanticObject) -> List[GeneratedFile]:
        """Generate window code.

        Args:
            obj: Window object

        Returns:
            Generated files
        """
        return []

    def generate_datawindow(self, obj: SemanticObject) -> List[GeneratedFile]:
        """Generate datawindow code.

        Args:
            obj: DataWindow object

        Returns:
            Generated files
        """
        return []

    def generate_user_object(self, obj: SemanticObject) -> List[GeneratedFile]:
        """Generate user object code.

        Args:
            obj: User object

        Returns:
            Generated files
        """
        return []

    def generate_generic(self, obj: SemanticObject) -> List[GeneratedFile]:
        """Generate generic object code.

        Args:
            obj: Generic object

        Returns:
            Generated files
        """
        return []

    def generate_config(self, model: ApplicationModel) -> List[GeneratedFile]:
        """Generate project configuration files.

        Args:
            model: Application model

        Returns:
            Configuration files
        """
        return []


# ============================================================================
# FLUTTER GENERATOR
# ============================================================================


class FlutterGenerator(BaseCodeGenerator):
    """Generator for Flutter/Dart code."""

    def generate_window(self, obj: SemanticObject) -> List[GeneratedFile]:
        """Generate Flutter screen from window.

        Args:
            obj: Window object

        Returns:
            Generated Dart files
        """
        files = []

        # Generate main screen file
        screen_code = render_template(
            "flutter/screen.dart",
            {
                "class_name": self._to_pascal_case(obj.name),
                "title": obj.name,
                "properties": obj.properties,
                "methods": obj.methods,
                "events": obj.events,
            },
        )

        files.append(
            GeneratedFile(
                path=f"lib/screens/{obj.name}.dart",
                content=screen_code,
                language=TargetLanguage.FLUTTER,
            )
        )

        # Generate state management if needed
        if obj.properties:
            state_code = render_template(
                "flutter/state.dart",
                {
                    "class_name": self._to_pascal_case(obj.name),
                    "properties": obj.properties,
                },
            )

            files.append(
                GeneratedFile(
                    path=f"lib/providers/{obj.name}_provider.dart",
                    content=state_code,
                    language=TargetLanguage.FLUTTER,
                )
            )

        return files

    def generate_datawindow(self, obj: SemanticObject) -> List[GeneratedFile]:
        """Generate Flutter data grid from datawindow.

        Args:
            obj: DataWindow object

        Returns:
            Generated Dart files
        """
        files = []

        # Generate data grid widget
        grid_code = render_template(
            "flutter/data_grid.dart",
            {
                "class_name": self._to_pascal_case(obj.name),
                "columns": self._extract_columns(obj),
                "properties": obj.properties,
            },
        )

        files.append(
            GeneratedFile(
                path=f"lib/widgets/{obj.name}_grid.dart",
                content=grid_code,
                language=TargetLanguage.FLUTTER,
            )
        )

        # Generate data model
        model_code = render_template(
            "flutter/model.dart",
            {
                "class_name": self._to_pascal_case(obj.name),
                "properties": obj.properties,
            },
        )

        files.append(
            GeneratedFile(
                path=f"lib/models/{obj.name}.dart",
                content=model_code,
                language=TargetLanguage.FLUTTER,
            )
        )

        return files

    def generate_config(self, model: ApplicationModel) -> List[GeneratedFile]:
        """Generate Flutter project configuration.

        Args:
            model: Application model

        Returns:
            Configuration files
        """
        files = []

        # Generate pubspec.yaml
        pubspec = render_template(
            "flutter/pubspec.yaml",
            {
                "name": model.name.lower(),
                "version": model.version,
                "dependencies": self._get_flutter_dependencies(),
            },
        )

        files.append(
            GeneratedFile(
                path="pubspec.yaml",
                content=pubspec,
                language=TargetLanguage.FLUTTER,
                file_type="config",
            )
        )

        # Generate main.dart
        main_code = render_template(
            "flutter/main.dart",
            {
                "app_name": model.name,
                "screens": [
                    obj
                    for obj in model.objects.values()
                    if obj.type == ObjectType.WINDOW
                ],
            },
        )

        files.append(
            GeneratedFile(
                path="lib/main.dart",
                content=main_code,
                language=TargetLanguage.FLUTTER,
            )
        )

        return files

    def _to_pascal_case(self, name: str) -> str:
        """Convert name to PascalCase.

        Args:
            name: Name to convert

        Returns:
            PascalCase name
        """
        parts = name.replace("_", " ").replace("-", " ").split()
        return "".join(word.capitalize() for word in parts)

    def _extract_columns(self, obj: SemanticObject) -> List[Dict[str, str]]:
        """Extract column definitions from datawindow.

        Args:
            obj: DataWindow object

        Returns:
            Column definitions
        """
        # Simple extraction from properties
        columns = []
        for prop in obj.properties:
            if "column" in prop.name.lower():
                columns.append(
                    {
                        "name": prop.name,
                        "type": prop.type,
                        "label": prop.name.replace("_", " ").title(),
                    }
                )
        return columns

    def _get_flutter_dependencies(self) -> Dict[str, str]:
        """Get Flutter package dependencies.

        Returns:
            Dependencies map
        """
        return {
            "flutter": "sdk: flutter",
            "provider": "^6.0.0",
            "http": "^0.13.0",
            "json_annotation": "^4.8.0",
        }


# ============================================================================
# PYTHON GENERATOR
# ============================================================================


class PythonGenerator(BaseCodeGenerator):
    """Generator for Python code."""

    def generate_window(self, obj: SemanticObject) -> List[GeneratedFile]:
        """Generate Python class from window.

        Args:
            obj: Window object

        Returns:
            Generated Python files
        """
        files = []

        # Generate class file
        class_code = render_template(
            "python/class.py",
            {
                "class_name": self._to_class_name(obj.name),
                "properties": obj.properties,
                "methods": obj.methods,
                "parent": obj.parent,
            },
        )

        files.append(
            GeneratedFile(
                path=f"src/windows/{obj.name}.py",
                content=class_code,
                language=TargetLanguage.PYTHON,
            )
        )

        return files

    def generate_datawindow(self, obj: SemanticObject) -> List[GeneratedFile]:
        """Generate Python data model from datawindow.

        Args:
            obj: DataWindow object

        Returns:
            Generated Python files
        """
        files = []

        # Generate SQLModel/Pydantic model
        model_code = render_template(
            "python/model.py",
            {
                "class_name": self._to_class_name(obj.name),
                "properties": obj.properties,
                "table_name": obj.name.lower(),
            },
        )

        files.append(
            GeneratedFile(
                path=f"src/models/{obj.name}.py",
                content=model_code,
                language=TargetLanguage.PYTHON,
            )
        )

        # Generate repository
        repo_code = render_template(
            "python/repository.py",
            {
                "model_name": self._to_class_name(obj.name),
                "model_import": f"models.{obj.name}",
            },
        )

        files.append(
            GeneratedFile(
                path=f"src/repositories/{obj.name}_repository.py",
                content=repo_code,
                language=TargetLanguage.PYTHON,
            )
        )

        return files

    def generate_config(self, model: ApplicationModel) -> List[GeneratedFile]:
        """Generate Python project configuration.

        Args:
            model: Application model

        Returns:
            Configuration files
        """
        files = []

        # Generate pyproject.toml
        pyproject = render_template(
            "python/pyproject.toml",
            {
                "name": model.name.lower(),
                "version": model.version,
                "dependencies": self._get_python_dependencies(),
            },
        )

        files.append(
            GeneratedFile(
                path="pyproject.toml",
                content=pyproject,
                language=TargetLanguage.PYTHON,
                file_type="config",
            )
        )

        # Generate main.py
        main_code = render_template(
            "python/main.py",
            {
                "app_name": model.name,
                "models": [obj for obj in model.objects.values()],
            },
        )

        files.append(
            GeneratedFile(
                path="src/main.py",
                content=main_code,
                language=TargetLanguage.PYTHON,
            )
        )

        return files

    def _to_class_name(self, name: str) -> str:
        """Convert name to Python class name.

        Args:
            name: Name to convert

        Returns:
            Class name
        """
        parts = name.replace("-", "_").split("_")
        return "".join(word.capitalize() for word in parts)

    def _get_python_dependencies(self) -> List[str]:
        """Get Python package dependencies.

        Returns:
            Dependencies list
        """
        return [
            "litestar>=2.0.0",
            "sqlmodel>=0.0.14",
            "pydantic>=2.0.0",
            "uvicorn>=0.24.0",
        ]


# ============================================================================
# GENERATE COORDINATOR
# ============================================================================


class GenerateCoordinator(BaseCoordinator):
    """Coordinator for code generation stage.

    Generates modern application code from semantic models.
    """

    def __init__(
        self, *args, target: TargetLanguage = TargetLanguage.FLUTTER, **kwargs
    ):
        """Initialize coordinator.

        Args:
            target: Target language for generation
        """
        super().__init__(*args, **kwargs)
        self.target = target
        self.generator = self._create_generator()

    def _create_generator(self) -> BaseCodeGenerator:
        """Create appropriate generator for target.

        Returns:
            Code generator
        """
        if self.target == TargetLanguage.FLUTTER:
            return FlutterGenerator(self.target)
        elif self.target == TargetLanguage.PYTHON:
            return PythonGenerator(self.target)
        elif self.target == TargetLanguage.TYPESCRIPT:
            from .typescript import TypeScriptGenerator

            return TypeScriptGenerator()
        elif self.target == TargetLanguage.REACT:
            from .react import ReactGenerator

            return ReactGenerator()
        elif self.target == TargetLanguage.TAURI:
            from .tauri import TauriGenerator

            return TauriGenerator(self.input_path, self.output_path)
        elif self.target == TargetLanguage.DIOXUS:
            from .rust_dioxus import DioxusGenerator as RustDioxusGenerator

            return RustDioxusGenerator(self.input_path, self.output_path)
        elif self.target == TargetLanguage.VUE:
            from .vue import VueGenerator

            return VueGenerator()
        elif self.target == TargetLanguage.SVELTE:
            from .svelte import SvelteGenerator

            return SvelteGenerator()
        else:
            # Default to Flutter
            return FlutterGenerator(TargetLanguage.FLUTTER)

    @property
    def stage_name(self) -> str:
        """Get stage name."""
        return "generate"

    def discover_files(self) -> List[Path]:
        """Discover model files to process.

        Returns:
            List of model files
        """
        # Look for application model
        app_model = self.input_path / "application_model.json"
        if app_model.exists():
            return [app_model]

        # Fall back to individual model files
        return list(self.input_path.rglob("*.model.json"))

    def process_file(self, input_file: Path, output_dir: Path) -> bool:
        """Process model file to generate code.

        Args:
            input_file: Model file
            output_dir: Output directory

        Returns:
            True if successful
        """
        try:
            self.logger.info(f"Generating from: {input_file}")

            # Read model
            file_handler = FileHandler()
            model_data = file_handler.read_json(input_file)

            # Check if it's an application model or individual model
            if "objects" in model_data:
                # Application model
                app_model = self._load_application_model(model_data)
                project = self.generator.generate_project(app_model)

            else:
                # Individual model
                semantic_obj = self._load_semantic_object(model_data)
                files = self.generator.generate_object(semantic_obj)

                project = GeneratedProject(
                    name=semantic_obj.name,
                    target=self.target,
                    files=files,
                )

            # Write generated files
            for gen_file in project.files:
                output_file = output_dir / gen_file.path
                output_file.parent.mkdir(parents=True, exist_ok=True)
                file_handler.write_text(output_file, gen_file.content)
                self.logger.info(f"Generated: {output_file}")

            # Write project metadata
            metadata_file = output_dir / "project.json"
            metadata = {
                "name": project.name,
                "target": project.target.value,
                "files": [f.path for f in project.files],
                "generated_at": str(Path.cwd()),
            }
            file_handler.write_json(metadata_file, metadata, indent=2)

            return True

        except Exception as e:
            self.logger.error(f"Failed to generate from {input_file}: {e}")
            return False

    def _load_application_model(self, data: Dict[str, Any]) -> ApplicationModel:
        """Load application model from JSON.

        Args:
            data: JSON data

        Returns:
            Application model
        """
        model = ApplicationModel(
            name=data["name"],
            version=data.get("version", "1.0.0"),
        )

        # Load objects
        for name, obj_data in data.get("objects", {}).items():
            obj = self._load_semantic_object(obj_data)
            model.objects[name] = obj

        return model

    def _load_semantic_object(self, data: Dict[str, Any]) -> SemanticObject:
        """Load semantic object from JSON.

        Args:
            data: JSON data

        Returns:
            Semantic object
        """
        obj = SemanticObject(
            name=data["name"],
            type=ObjectType(data["type"]),
            parent=data.get("parent"),
        )

        # Load properties
        for prop_data in data.get("properties", []):
            obj.properties.append(
                Property(
                    name=prop_data["name"],
                    type=prop_data["type"],
                    access=prop_data.get("access", "public"),
                    default_value=prop_data.get("default_value"),
                )
            )

        # Load methods
        for method_data in data.get("methods", []):
            obj.methods.append(
                Method(
                    name=method_data["name"],
                    return_type=method_data.get("return_type"),
                    access=method_data.get("access", "public"),
                )
            )

        return obj
