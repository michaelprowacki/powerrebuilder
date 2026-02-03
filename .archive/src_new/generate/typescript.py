"""TypeScript Generator - Generate TypeScript code from PowerBuilder objects.

This module generates TypeScript classes, interfaces, and types from
PowerBuilder semantic models.
"""

import logging
from typing import Any, List, Optional

from src_new._core import (
    ApplicationModel,
    GeneratedFile,
    Method,
    Parameter,
    SemanticObject,
    TargetLanguage,
)
from .generator import BaseCodeGenerator

logger = logging.getLogger(__name__)


class TypeScriptGenerator(BaseCodeGenerator):
    """Generator for TypeScript code."""

    def __init__(self):
        """Initialize TypeScript generator."""
        super().__init__(TargetLanguage.TYPESCRIPT)

        # Type mapping from PowerBuilder to TypeScript
        self.type_map = {
            "string": "string",
            "char": "string",
            "varchar": "string",
            "text": "string",
            "int": "number",
            "integer": "number",
            "long": "number",
            "decimal": "number",
            "float": "number",
            "double": "number",
            "boolean": "boolean",
            "bool": "boolean",
            "date": "Date",
            "datetime": "Date",
            "time": "Date",
            "blob": "Uint8Array",
            "any": "any",
            "object": "Record<string, any>",
            "array": "Array<any>",
        }

    def generate_window(self, obj: SemanticObject) -> List[GeneratedFile]:
        """Generate TypeScript class from window.

        Args:
            obj: Window object

        Returns:
            Generated TypeScript files
        """
        files = []

        # Generate window class
        class_content = self._generate_class(obj)
        files.append(
            GeneratedFile(
                path=f"src/windows/{obj.name}.ts",
                content=class_content,
                language=TargetLanguage.TYPESCRIPT,
            )
        )

        # Generate interface
        interface_content = self._generate_interface(obj)
        files.append(
            GeneratedFile(
                path=f"src/interfaces/I{obj.name}.ts",
                content=interface_content,
                language=TargetLanguage.TYPESCRIPT,
            )
        )

        return files

    def generate_datawindow(self, obj: SemanticObject) -> List[GeneratedFile]:
        """Generate TypeScript model from datawindow.

        Args:
            obj: DataWindow object

        Returns:
            Generated TypeScript files
        """
        files = []

        # Generate model interface
        model_content = self._generate_model_interface(obj)
        files.append(
            GeneratedFile(
                path=f"src/models/{obj.name}.model.ts",
                content=model_content,
                language=TargetLanguage.TYPESCRIPT,
            )
        )

        # Generate service class
        service_content = self._generate_service(obj)
        files.append(
            GeneratedFile(
                path=f"src/services/{obj.name}.service.ts",
                content=service_content,
                language=TargetLanguage.TYPESCRIPT,
            )
        )

        return files

    def generate_user_object(self, obj: SemanticObject) -> List[GeneratedFile]:
        """Generate TypeScript class from user object.

        Args:
            obj: User object

        Returns:
            Generated TypeScript files
        """
        files = []

        # Generate class
        class_content = self._generate_class(obj)
        files.append(
            GeneratedFile(
                path=f"src/objects/{obj.name}.ts",
                content=class_content,
                language=TargetLanguage.TYPESCRIPT,
            )
        )

        return files

    def generate_generic(self, obj: SemanticObject) -> List[GeneratedFile]:
        """Generate generic TypeScript code.

        Args:
            obj: Semantic object

        Returns:
            Generated files
        """
        return self.generate_user_object(obj)

    def generate_config(self, model: ApplicationModel) -> List[GeneratedFile]:
        """Generate TypeScript project configuration.

        Args:
            model: Application model

        Returns:
            Configuration files
        """
        files = []

        # Generate tsconfig.json
        tsconfig = {
            "compilerOptions": {
                "target": "ES2020",
                "module": "commonjs",
                "lib": ["ES2020", "DOM"],
                "outDir": "./dist",
                "rootDir": "./src",
                "strict": True,
                "esModuleInterop": True,
                "skipLibCheck": True,
                "forceConsistentCasingInFileNames": True,
                "declaration": True,
                "declarationMap": True,
                "sourceMap": True,
                "resolveJsonModule": True,
                "experimentalDecorators": True,
                "emitDecoratorMetadata": True,
            },
            "include": ["src/**/*"],
            "exclude": ["node_modules", "dist"],
        }

        import json

        files.append(
            GeneratedFile(
                path="tsconfig.json",
                content=json.dumps(tsconfig, indent=2),
                language=TargetLanguage.TYPESCRIPT,
                file_type="config",
            )
        )

        # Generate package.json
        package = {
            "name": model.name.lower().replace(" ", "-"),
            "version": model.version,
            "description": f"{model.name} TypeScript Application",
            "main": "dist/index.js",
            "scripts": {
                "build": "tsc",
                "start": "node dist/index.js",
                "dev": "ts-node src/index.ts",
                "test": "jest",
                "lint": "eslint src/**/*.ts",
                "format": "prettier --write src/**/*.ts",
            },
            "dependencies": {
                "axios": "^1.4.0",
                "class-transformer": "^0.5.1",
                "class-validator": "^0.14.0",
                "reflect-metadata": "^0.1.13",
            },
            "devDependencies": {
                "@types/node": "^20.0.0",
                "@typescript-eslint/eslint-plugin": "^5.0.0",
                "@typescript-eslint/parser": "^5.0.0",
                "eslint": "^8.0.0",
                "jest": "^29.0.0",
                "prettier": "^2.0.0",
                "ts-jest": "^29.0.0",
                "ts-node": "^10.0.0",
                "typescript": "^5.0.0",
            },
        }

        files.append(
            GeneratedFile(
                path="package.json",
                content=json.dumps(package, indent=2),
                language=TargetLanguage.TYPESCRIPT,
                file_type="config",
            )
        )

        # Generate main index.ts
        index_content = self._generate_index(model)
        files.append(
            GeneratedFile(
                path="src/index.ts",
                content=index_content,
                language=TargetLanguage.TYPESCRIPT,
            )
        )

        return files

    def _generate_class(self, obj: SemanticObject) -> str:
        """Generate TypeScript class.

        Args:
            obj: Semantic object

        Returns:
            TypeScript class code
        """
        lines = []

        # Imports
        lines.append("import 'reflect-metadata';")
        if obj.parent:
            lines.append(f"import {{ {obj.parent} }} from './{obj.parent}';")
        lines.append("")

        # Class decoration
        lines.append("/**")
        lines.append(f" * {obj.name} - Generated from PowerBuilder")
        lines.append(" */")

        # Class declaration
        parent = f" extends {obj.parent}" if obj.parent else ""
        lines.append(f"export class {self._to_class_name(obj.name)}{parent} {{")

        # Properties
        if obj.properties:
            lines.append("  // Properties")
            for prop in obj.properties:
                ts_type = self._map_type(prop.type)
                visibility = "private" if prop.access == "private" else "public"
                readonly = ""  # TODO: Add readonly to Property model if needed
                optional = "?" if not prop.is_required else ""
                lines.append(
                    f"  {visibility} {readonly}{prop.name}{optional}: {ts_type};"
                )
            lines.append("")

        # Constructor
        lines.append("  constructor() {")
        if obj.parent:
            lines.append("    super();")
        lines.append("    this.initialize();")
        lines.append("  }")
        lines.append("")

        # Initialize method
        lines.append("  private initialize(): void {")
        lines.append("    // Initialize properties")
        for prop in obj.properties:
            if prop.default_value:
                lines.append(
                    f"    this.{prop.name} = {self._format_value(prop.default_value, prop.type)};"
                )
        lines.append("  }")
        lines.append("")

        # Methods
        if obj.methods:
            lines.append("  // Methods")
            for method in obj.methods:
                lines.extend(self._generate_method(method))
                lines.append("")

        # Events
        if obj.events:
            lines.append("  // Event Handlers")
            for event in obj.events:
                lines.append(
                    f"  public on{self._to_pascal_case(event.name)}(): void {{"
                )
                lines.append(f"    // Handle {event.name} event")
                if event.body:
                    lines.append(f"    // Original handler: {event.body}")
                lines.append("  }")
                lines.append("")

        lines.append("}")

        return "\n".join(lines)

    def _generate_interface(self, obj: SemanticObject) -> str:
        """Generate TypeScript interface.

        Args:
            obj: Semantic object

        Returns:
            TypeScript interface code
        """
        lines = []

        lines.append("/**")
        lines.append(f" * Interface for {obj.name}")
        lines.append(" */")
        lines.append(f"export interface I{self._to_class_name(obj.name)} {{")

        # Properties
        for prop in obj.properties:
            if prop.access != "private":
                ts_type = self._map_type(prop.type)
                optional = "?" if not prop.is_required else ""
                lines.append(f"  {prop.name}{optional}: {ts_type};")

        # Methods
        for method in obj.methods:
            if method.access != "private":
                params = self._format_parameters(method.parameters)
                return_type = (
                    self._map_type(method.return_type) if method.return_type else "void"
                )
                lines.append(f"  {method.name}({params}): {return_type};")

        lines.append("}")

        return "\n".join(lines)

    def _generate_model_interface(self, obj: SemanticObject) -> str:
        """Generate model interface.

        Args:
            obj: DataWindow object

        Returns:
            Model interface code
        """
        lines = []

        lines.append(
            "import { IsString, IsNumber, IsBoolean, IsDate, IsOptional } from 'class-validator';"
        )
        lines.append("")

        lines.append("/**")
        lines.append(f" * {obj.name} Model")
        lines.append(" */")
        lines.append(f"export class {self._to_class_name(obj.name)}Model {{")

        for prop in obj.properties:
            ts_type = self._map_type(prop.type)

            # Add validation decorators
            if not prop.is_required:
                lines.append("  @IsOptional()")

            if ts_type == "string":
                lines.append("  @IsString()")
            elif ts_type == "number":
                lines.append("  @IsNumber()")
            elif ts_type == "boolean":
                lines.append("  @IsBoolean()")
            elif ts_type == "Date":
                lines.append("  @IsDate()")

            optional = "?" if not prop.is_required else ""
            lines.append(f"  {prop.name}{optional}: {ts_type};")
            lines.append("")

        lines.append("}")

        return "\n".join(lines)

    def _generate_service(self, obj: SemanticObject) -> str:
        """Generate service class.

        Args:
            obj: DataWindow object

        Returns:
            Service class code
        """
        lines = []
        model_name = self._to_class_name(obj.name)

        lines.append("import axios, { AxiosInstance } from 'axios';")
        lines.append(
            f"import {{ {model_name}Model }} from '../models/{obj.name}.model';"
        )
        lines.append("")

        lines.append("/**")
        lines.append(f" * Service for {obj.name}")
        lines.append(" */")
        lines.append(f"export class {model_name}Service {{")
        lines.append("  private api: AxiosInstance;")
        lines.append("")

        lines.append("  constructor(baseURL: string = '/api') {")
        lines.append("    this.api = axios.create({")
        lines.append("      baseURL,")
        lines.append("      headers: {")
        lines.append("        'Content-Type': 'application/json',")
        lines.append("      },")
        lines.append("    });")
        lines.append("  }")
        lines.append("")

        # CRUD methods
        lines.append(f"  async getAll(): Promise<{model_name}Model[]> {{")
        lines.append(
            f"    const response = await this.api.get<{model_name}Model[]>('/{obj.name.lower()}');"
        )
        lines.append("    return response.data;")
        lines.append("  }")
        lines.append("")

        lines.append(
            f"  async getById(id: string | number): Promise<{model_name}Model> {{"
        )
        lines.append(
            f"    const response = await this.api.get<{model_name}Model>(`/{obj.name.lower()}/${{id}}`);"
        )
        lines.append("    return response.data;")
        lines.append("  }")
        lines.append("")

        lines.append(
            f"  async create(data: {model_name}Model): Promise<{model_name}Model> {{"
        )
        lines.append(
            f"    const response = await this.api.post<{model_name}Model>('/{obj.name.lower()}', data);"
        )
        lines.append("    return response.data;")
        lines.append("  }")
        lines.append("")

        lines.append(
            f"  async update(id: string | number, data: Partial<{model_name}Model>): Promise<{model_name}Model> {{"
        )
        lines.append(
            f"    const response = await this.api.put<{model_name}Model>(`/{obj.name.lower()}/${{id}}`, data);"
        )
        lines.append("    return response.data;")
        lines.append("  }")
        lines.append("")

        lines.append("  async delete(id: string | number): Promise<void> {")
        lines.append(f"    await this.api.delete(`/{obj.name.lower()}/${{id}}`);")
        lines.append("  }")

        lines.append("}")

        return "\n".join(lines)

    def _generate_method(self, method: Method) -> List[str]:
        """Generate method code.

        Args:
            method: Method object

        Returns:
            Method code lines
        """
        lines = []

        # Method signature
        visibility = "private" if method.access == "private" else "public"
        params = self._format_parameters(method.parameters)
        return_type = (
            self._map_type(method.return_type) if method.return_type else "void"
        )
        async_prefix = ""  # TODO: Add is_async to Method model if needed

        lines.append(
            f"  {visibility} {async_prefix}{method.name}({params}): {return_type} {{"
        )

        # Method body
        if method.body:
            lines.append(f"    // {method.body}")

        # Default return
        if method.return_type:
            default_return = self._get_default_return(method.return_type)
            lines.append(f"    return {default_return};")

        lines.append("  }")

        return lines

    def _generate_index(self, model: ApplicationModel) -> str:
        """Generate index.ts file.

        Args:
            model: Application model

        Returns:
            Index file content
        """
        lines = []

        lines.append("import 'reflect-metadata';")
        lines.append("")

        # Export all classes
        for obj_name in model.objects.keys():
            class_name = self._to_class_name(obj_name)
            lines.append(f"export {{ {class_name} }} from './windows/{obj_name}';")

        lines.append("")
        lines.append("// Application entry point")
        lines.append("export class Application {")
        lines.append(f"  public readonly name = '{model.name}';")
        lines.append(f"  public readonly version = '{model.version}';")
        lines.append("")
        lines.append("  public start(): void {")
        lines.append("    console.log(`Starting ${this.name} v${this.version}`);")
        lines.append("    // Initialize application")
        lines.append("  }")
        lines.append("}")
        lines.append("")
        lines.append("// Create and start application")
        lines.append("if (require.main === module) {")
        lines.append("  const app = new Application();")
        lines.append("  app.start();")
        lines.append("}")

        return "\n".join(lines)

    def _map_type(self, pb_type: Optional[str]) -> str:
        """Map PowerBuilder type to TypeScript.

        Args:
            pb_type: PowerBuilder type

        Returns:
            TypeScript type
        """
        if not pb_type:
            return "any"

        type_lower = pb_type.lower()
        return self.type_map.get(type_lower, "any")

    def _format_value(self, value: Any, pb_type: str) -> str:
        """Format value for TypeScript.

        Args:
            value: Value to format
            pb_type: PowerBuilder type

        Returns:
            Formatted value
        """
        if value is None:
            return "null"

        ts_type = self._map_type(pb_type)

        if ts_type == "string":
            return f"'{value}'"
        elif ts_type == "Date":
            return f"new Date('{value}')"
        elif ts_type == "boolean":
            return "true" if value else "false"
        else:
            return str(value)

    def _format_parameters(self, parameters: Optional[List[Parameter]]) -> str:
        """Format method parameters.

        Args:
            parameters: Method parameters

        Returns:
            Formatted parameters
        """
        if not parameters:
            return ""

        params = []
        for param in parameters:
            ts_type = self._map_type(param.type)
            optional = "?" if param.is_optional else ""
            params.append(f"{param.name}{optional}: {ts_type}")

        return ", ".join(params)

    def _get_default_return(self, pb_type: str) -> str:
        """Get default return value.

        Args:
            pb_type: PowerBuilder type

        Returns:
            Default value
        """
        ts_type = self._map_type(pb_type)

        if ts_type == "string":
            return "''"
        elif ts_type == "number":
            return "0"
        elif ts_type == "boolean":
            return "false"
        elif ts_type == "Date":
            return "new Date()"
        elif ts_type.startswith("Array"):
            return "[]"
        else:
            return "null"

    def _to_class_name(self, name: str) -> str:
        """Convert to TypeScript class name.

        Args:
            name: Original name

        Returns:
            Class name
        """
        return self._to_pascal_case(name)

    def _to_pascal_case(self, name: str) -> str:
        """Convert to PascalCase.

        Args:
            name: Original name

        Returns:
            PascalCase name
        """
        parts = name.replace("_", " ").replace("-", " ").split()
        return "".join(word.capitalize() for word in parts)
